from ExperimentOrchestrator.Experiment.Run.RunController import RunController
from EventManager.EventSubscriptionController import EventSubscriptionController 
from EventManager.Models.RunnerEvents import RunnerEvents
from ProgressManager.Validation.AnomaliesChecker import ResultsValidator

import threading
import time
import requests
import numpy as np
from enum import Enum

### =========================================================
### |                                                       |
### |                  WorkerRuntime                        |
### |                                                       |
### |   - Connect to the master orchestrator                |
### |   - Request experiment runs/tasks                     |
### |   - Execute runs locally + anomalies check            |
### |   - Send results back to the master                   |
### |   - Send periodic heartbeat updates                   |
### |   - Gracefully shutdown on master request             |
### |                                                       |           
### =========================================================
class WorkerRuntime:
    @staticmethod
    def make_json_safe(obj):
        if isinstance(obj, dict):
            return {k: WorkerRuntime.make_json_safe(v) for k, v in obj.items()}
        if isinstance(obj, list):
            return [WorkerRuntime.make_json_safe(v) for v in obj]
        if isinstance(obj, np.generic):
            return obj.item()
        if isinstance(obj, Enum):
            return obj.value
        return obj

    def __init__(self, master_url, heartbeat_interval=40, idle_timeout=120):
        self.master_url = master_url
        self.heartbeat_interval = heartbeat_interval
        self.idle_timeout = idle_timeout

        self._stop = False
        self.current_run = None
        self.agent_id = None
        self.last_task_time = None

    def run_loop(self, agent_id, config):
        self.agent_id = agent_id
        self.last_task_time = time.time()

        print(f"[WORKER] Starting with agent_id: {self.agent_id}")
        print(f"[WORKER] Master URL: {self.master_url}")

        print("[WORKER] Validating experiment setup")
        EventSubscriptionController.raise_event(
            RunnerEvents.VALIDATE_EXPERIMENT
        )

        threading.Thread(target=self._heartbeat_loop, daemon=True).start()

        print("[WORKER] Heartbeat thread started")
        print(f"[WORKER] Waiting for tasks (idle timeout {self.idle_timeout}s)")

        while not self._stop:
            task = self._get_task()
            if task == "SHUTDOWN":
                print("[WORKER] Master shutdown acknowledged")
                break

            if not task:
                if time.time() - self.last_task_time > self.idle_timeout:
                    print("[WORKER] Idle timeout reached - exiting")
                    break
                self.current_run = None
                time.sleep(3)
                continue

            self.last_task_time = time.time()
            self.current_run = task

            run_id = task["__run_id"]

            try:
                run_data, anomaly_report = self._execute(task, config)
                self._send_result(run_id, run_data, anomaly_report)
            except Exception as e:
                self._send_failure(run_id, str(e))
            finally:
                self.current_run = None
        print(f"[WORKER] Worker {self.agent_id} exiting")

    def _get_task(self):
        try:
            r = requests.get(self.master_url + "/task", params={"agent_id": self.agent_id}, timeout=5)
            response = r.json()
            if response.get("shutdown"):
                print("[WORKER] Received shutdown signal from master")
                self._stop = True
                return "SHUTDOWN"
            task = response.get("run")

            if task:
                print(f"[WORKER] Got task: {task.get('__run_id')}")

            return task

        except Exception as e:
            print(f"[WORKER] Error getting task: {e}")
            return None

    def _execute(self, run, config):
        print(f"[WORKER] Executing task {run.get('__run_id')}")

        current_run = run.get('__current_run', 0)
        total_runs = run.get('__total_runs', 1)

        controller = RunController(run, config, current_run, total_runs, distributed_mode=True)
        run_data = controller.do_run()
        run_id = run["__run_id"]

        # Check for anomalies in the run raw result
        treatment_levels = {
            k: v
            for k, v in run.items()
            if not k.startswith("__")
        }
        run_dir = config.experiment_path / run_id
        anomaly_report = ResultsValidator.validate_output_log(
            run_dir,
            run_id,
            treatment_levels
        )
        
        print(f"[WORKER] Task {run.get('__run_id')} completed")
        return run_data, anomaly_report

    def _send_result(self, run_id, data, anomaly_report = None):
        try:
            safe_data = WorkerRuntime.make_json_safe(data)

            payload = {"run_id": run_id, "data": safe_data, "status": "DONE", "anomalies": (
                    anomaly_report.anomalies
                    if anomaly_report and anomaly_report.has_anomalies()
                    else []
                )}

            response = requests.post(self.master_url + "/result", json=payload, timeout=10)
            response.raise_for_status()

            print(f"[WORKER] Result sent for task {run_id}")

        except requests.exceptions.RequestException as e:
            print(f"[WORKER] Network error sending result: {e}")
        except Exception as e:
            print(f"[WORKER] Unexpected error: {e}")

    def _send_failure(self, run_id, error):
        try:
            requests.post(
                self.master_url + "/result",
                json={"run_id": run_id, "status": "FAILED", "error": error},
                timeout=10
            )
            print(f"[WORKER] Failure sent for {run_id}")

        except Exception as e:
            print(f"[WORKER] Error sending failure: {e}")

    def _heartbeat_loop(self):
        while not self._stop:
            try:
                requests.post(
                    self.master_url + "/heartbeat",
                    json={
                        "agent_id": self.agent_id,
                        "status": "RUNNING" if self.current_run else "IDLE",
                        "run_id": self.current_run["__run_id"] if self.current_run else None,
                        "timestamp": time.time()
                    },
                    timeout=5
                )
            except Exception as e:
                print(f"[WORKER] Heartbeat error: {e}")
            time.sleep(self.heartbeat_interval)