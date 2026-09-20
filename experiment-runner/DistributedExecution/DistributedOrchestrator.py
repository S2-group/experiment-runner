from ProgressManager.RunTable.Models.RunProgress import RunProgress
from ConfigValidator.Config.Models.Metadata import Metadata
from ProgressManager.Output.CSVOutputManager import CSVOutputManager
from ConfigValidator.Config.Models.OperationType import OperationType
from EventManager.Models.RunnerEvents import RunnerEvents
from EventManager.EventSubscriptionController import EventSubscriptionController
from ProgressManager.Validation.AnomaliesChecker import ResultsValidator, AnomalyReport
from ProgressManager.Output.OutputProcedure import OutputProcedure as output
from ProgressManager.Output.JSONOutputManager import JSONOutputManager
from ConfigValidator.CustomErrors.BaseError import BaseError


from flask import Flask, request, jsonify
import threading
import time
from pathlib import Path
import pandas as pd
import os
from waitress import serve

###     =========================================================
###     |                                                       |
###     |                  TaskManager                          |
###     |       - Assign available runs to connected workers    |
###     |       - Update and persist run_table.csv state        |
###     |       - Trigger AFTER_EXPERIMENT lifecycle event      |
###     |       - Detect experiment completion                  |
###     |                                                       |
###     |       *Any state modification to runs should happen   |
###     |        through this class to avoid race conditions    |
###     |                                                       |
###     =========================================================
class TaskManager:

    EPHEMERAL_COLS = {'agent_id', '__current_run', '__total_runs', 'run_dir'}

    def __init__(self, config, run_table, experiment_path: Path):
        self.config = config
        self.run_table = run_table
        self.experiment_path = experiment_path
        self.assigned_runs = {}
        self.total_runs = len(run_table)
        self.lock = threading.Lock()
        self.csv_manager = CSVOutputManager(experiment_path)
        self.completed = False
        self.shutdown = False
        self.validation_results = {}

    def _strip_ephemeral(self, run):
        """Remove ephemeral worker fields from a run dict in place."""
        for col in self.EPHEMERAL_COLS:
            run.pop(col, None)

    def get_next_task(self, agent_id):
        with self.lock:
            if self.completed:
                return None

            for idx, run in enumerate(self.run_table):
                if run['__done'] == RunProgress.TODO:
                    run_id = run["__run_id"]

                    run_dir = self.experiment_path / str(run_id)
                    run_dir.mkdir(parents=True, exist_ok=True)

                    # Only persist what belongs in the CSV
                    run['__done'] = RunProgress.RUNNING
                    self.assigned_runs[run_id] = agent_id
                    self._strip_ephemeral(run)  # safety strip before writing
                    self.csv_manager.write_run_table(self.run_table)

                    # Build a separate task payload for the worker
                    task = run.copy()
                    task['__done'] = task['__done'].name
                    task['agent_id'] = agent_id
                    task['__current_run'] = idx + 1
                    task['__total_runs'] = self.total_runs
                    task['run_dir'] = str(run_dir)

                    print(f"[MASTER] Assigned {run_id} -> {agent_id}")
                    return task
        return None

    def complete_task(self, run_id, data):
        with self.lock:
            for run in self.run_table:
                if run["__run_id"] == run_id:
                    # Merge returned data
                    if data:
                        for k, v in data.items():
                            run[k] = v
                    run["__done"] = RunProgress.DONE
                    self._strip_ephemeral(run)  # safety strip before writing
                    self.assigned_runs.pop(run_id, None)
                    self.csv_manager.write_run_table(self.run_table)
                    print(f"[MASTER] Completed run {run_id}")
                    break

            # Check if all runs are done
            all_done = all(
                run['__done'] == RunProgress.DONE
                for run in self.run_table
            )
            if all_done and not self.completed:
                self.completed = True
                self.shutdown = True
                print("\n[MASTER] ALL RUNS COMPLETED\n")

                if self.config.operation_type is OperationType.SEMI:
                    EventSubscriptionController.raise_event(RunnerEvents.CONTINUE)

                print("[MASTER] Calling AFTER_EXPERIMENT hook")
                EventSubscriptionController.raise_event(
                    RunnerEvents.AFTER_EXPERIMENT
                )

    def fail_task(self, run_id):
        """Return a failed run to TODO so it can be retried."""
        with self.lock:
            for run in self.run_table:
                if run['__run_id'] == run_id:
                    run['__done'] = RunProgress.TODO
                    self._strip_ephemeral(run)
                    self.assigned_runs.pop(run_id, None)
                    self.csv_manager.write_run_table(self.run_table)
                    break

    def restore_crashed_runs(self):
        """If server restarts and finds RUNNING runs, restore them to TODO."""
        changed = False
        for run in self.run_table:
            if run['__done'] == RunProgress.RUNNING:
                run['__done'] = RunProgress.TODO
                self._strip_ephemeral(run)
                changed = True
        if changed:
            print("[MASTER] Restored RUNNING -> TODO after restart")
            self.csv_manager.write_run_table(self.run_table)

    def experiment_already_completed(self):
        return all(
            run['__done'] == RunProgress.DONE
            for run in self.run_table
        )


###     =========================================================
###     |                                                       |
###     |                  APIServer                            |
###     |       - Handles the communication between workers     |
###     |           and the orchestrator                        |
###     |                                                       |
###     =========================================================
class APIServer:

    def __init__(self, task_manager, worker_monitor):
        self.app = Flask(__name__)
        self.task_manager = task_manager
        self.monitor = worker_monitor

        @self.app.route('/task', methods=['GET'])
        def get_task():
            agent_id = request.args.get('agent_id')
            self.monitor.heartbeat(agent_id)

            if self.task_manager.shutdown:
                return jsonify({
                    "shutdown": True,
                    "run": None
                })

            task = self.task_manager.get_next_task(agent_id)

            return jsonify({
                "shutdown": False,
                "run": task if task else None
            })

        @self.app.route('/result', methods=['POST'])
        def submit_result():
            try:
                payload = request.get_json()
                run_id = payload.get('run_id')
                run_data = payload.get('data', {})
                status = payload.get('status')
                anomalies = payload.get("anomalies", [])

                if status == "FAILED":
                    print(f"[MASTER] Run failed: {run_id}")
                    print(payload.get('error'))
                    self.task_manager.fail_task(run_id)
                else:
                    self.task_manager.complete_task(run_id, run_data)
                    if anomalies:
                        report = AnomalyReport()
                        report.anomalies.extend(anomalies)
                        log_file_path = (self.task_manager.experiment_path/ self.task_manager.config.energy_validation_log_file)
                        ResultsValidator.update_report(report, log_file_path)

                return jsonify({"status": "ok"})

            except Exception as e:
                import traceback
                traceback.print_exc()
                return jsonify({"error": str(e)}), 500

        @self.app.route('/heartbeat', methods=['POST'])
        def heartbeat():
            data = request.get_json()
            agent_id = data.get('agent_id')
            self.monitor.heartbeat(agent_id)
            return jsonify({"status": "ok"})

        @self.app.route('/status', methods=['GET'])
        def status():
            total_runs = len(self.task_manager.run_table)
            todo_count = sum(
                1 for r in self.task_manager.run_table
                if r['__done'] == RunProgress.TODO
            )
            running_count = sum(
                1 for r in self.task_manager.run_table
                if r['__done'] == RunProgress.RUNNING
            )
            done_count = sum(
                1 for r in self.task_manager.run_table
                if r['__done'] == RunProgress.DONE
            )
            return jsonify({
                "status": "ok",
                "total_runs": total_runs,
                "runs": {
                    "todo": todo_count,
                    "running": running_count,
                    "done": done_count
                },
                "active_agents": len(self.monitor.heartbeats)
            })

        @self.app.route('/shutdown', methods=['POST'])
        def shutdown():
            shutdown_server()
            return jsonify({"status": "shutting down"})


###     =========================================================
###     |                                                       |
###     |                  WorkerMonitor                        |
###     |       - Keeps track of connected workers              |
###     |       - If a worker fails to send a heartbeat         |
###     |         within the timeout period, it is considered   |
###     |         dead and its run is returned to TODO          |
###     |                                                       |
###     =========================================================
class WorkerMonitor:

    def __init__(self, task_manager):
        self.heartbeats = {}
        self.task_manager = task_manager
        self.timeout = 60

    def heartbeat(self, agent_id):
        self.heartbeats[agent_id] = time.time()

    def monitor(self):
        while not self.task_manager.completed:
            time.sleep(10)
            now = time.time()
            dead = [
                agent for agent, t in self.heartbeats.items()
                if now - t > self.timeout
            ]
            for agent in dead:
                print(f"[MASTER] Worker {agent} dead")

                for run in self.task_manager.run_table:
                    run_id = run["__run_id"]
                    # Use assigned_runs to check ownership, NOT run dict fields
                    if (
                        self.task_manager.assigned_runs.get(run_id) == agent
                        and run["__done"] != RunProgress.DONE
                    ):
                        print(f"[MASTER] Returning run {run_id} -> TODO")
                        run["__done"] = RunProgress.TODO
                        self.task_manager.assigned_runs.pop(run_id, None)

                self.task_manager.csv_manager.write_run_table(
                    self.task_manager.run_table
                )
                del self.heartbeats[agent]


###     =========================================================
###     |                                                       |
###     |                  DistributedOrchestrator              |
###     |       - Initialize experiment infrastructure          |
###     |       - Load or create run_table.csv                  |
###     |       - Restore interrupted experiments               |
###     |       - Start monitoring threads                      |
###     |       - Start the API server                          |
###     |                                                       |
###     =========================================================
class DistributedOrchestrator:

    EPHEMERAL_COLS = {'agent_id', '__current_run', '__total_runs', 'run_dir'}

    def __init__(self, config, metadata, host="0.0.0.0", port=5000):
        self.config = config
        self.metadata = metadata
        self.host = host
        self.port = port

        self.experiment_path = config.experiment_path  # set by RunnerConfig.__init__
        self.run_table_path = self.experiment_path / "run_table.csv"
        self.csv_data_manager = CSVOutputManager(self.experiment_path)
        self.json_data_manager = JSONOutputManager(self.experiment_path)

        EventSubscriptionController.raise_event(
            RunnerEvents.VALIDATE_EXPERIMENT
        )

        run_tbl = self.config.create_run_table_model()

        # Only append self-measure column if self_measure is active
        if hasattr(self.config, 'self_measure') and self.config.self_measure:
            if "self-measure" in run_tbl._RunTableModel__data_columns:
                raise BaseError("Cannot use self-measure as data column name if self_measure is active")
            run_tbl._RunTableModel__data_columns.append("self-measure")

        self.run_table = run_tbl.generate_experiment_run_table()

        # Create experiment output folder; if it exists, attempt to resume
        self.restarted = False
        try:
            self.experiment_path.mkdir(parents=True, exist_ok=False)
        except FileExistsError:
            output.console_log_WARNING(f"Reusing already existing experiment path: {self.experiment_path}")
            existing_run_table = self.csv_data_manager.read_run_table()

            # Strip ephemeral columns and restore RUNNING -> TODO before any checks
            for run in existing_run_table:
                for col in self.EPHEMERAL_COLS:
                    run.pop(col, None)
                if run['__done'] == RunProgress.RUNNING:
                    run['__done'] = RunProgress.TODO

            self.csv_data_manager.write_run_table(existing_run_table)
            print("[MASTER] Restored RUNNING -> TODO after restart")

            # Sanity check: abort if everything is already done
            todo_run_found = any(
                run['__done'] != RunProgress.DONE
                for run in existing_run_table
            )
            if not todo_run_found:
                raise BaseError("The experiment was restarted, but all runs have already been completed.")

            # Column names must match
            if not set(existing_run_table[0].keys()) == set(self.run_table[0].keys()):
                raise BaseError(
                    "The generated run table from the config file, and the found run table in the CSV in "
                    "the experiment output path, do not define the same columns!"
                )

            # md5sum check
            existing_metadata = self.json_data_manager.read_metadata()
            if existing_metadata.md5sum != self.metadata.md5sum:
                cont = output.query_yes_no(
                    "md5sum mismatch! This can occur if the configuration code "
                    "has changed since the last run. Continue anyway?",
                    default=None
                )
                if not cont:
                    raise BaseError("Aborting due to md5sum mismatch.")
                output.console_log_WARNING(
                    f"Updating md5sum from {existing_metadata.md5sum.hex()} to {self.metadata.md5sum.hex()}"
                )
                self.json_data_manager.write_metadata(self.metadata)

            self.restarted = True
            assert len(existing_run_table) == len(self.run_table)

            # Re-order generated run table to match existing order
            tmp_run_table = []
            for existing_var in existing_run_table:
                for generated_var in self.run_table:
                    if existing_var['__run_id'] == generated_var['__run_id']:
                        tmp_run_table.append(generated_var)
                        break
            self.run_table = tmp_run_table

            for existing_var, generated_var in zip(existing_run_table, self.run_table):
                assert existing_var['__run_id'] == generated_var['__run_id']

            # Fill in data columns and __done from existing CSV
            for existing_var, generated_var in zip(existing_run_table, self.run_table):
                assert existing_var['__run_id'] == generated_var['__run_id']

                for k in map(lambda factor: factor.factor_name,
                             self.config.run_table_model.get_factors()):
                    assert str(generated_var[k]) == str(existing_var[k])

                for k in set(self.config.run_table_model.get_data_columns()).union({'__done'}):
                    generated_var[k] = existing_var[k]

            # Write the clean merged table back to disk
            self.csv_data_manager.write_run_table(self.run_table)
            output.console_log_WARNING(">> WARNING << -- Experiment is restarted!")

        if not self.restarted:
            self.csv_data_manager.write_run_table(self.run_table)
            self.json_data_manager.write_metadata(self.metadata)

        output.console_log_WARNING("Experiment run table created...")

        self.task_manager = TaskManager(self.config, self.run_table, self.experiment_path)
        # restore_crashed_runs is now handled above in __init__ before TaskManager is created,
        # but call it again here so TaskManager's assigned_runs is also clean on restart
        self.task_manager.restore_crashed_runs()
        self.monitor = WorkerMonitor(self.task_manager)
        self.api = APIServer(self.task_manager, self.monitor)

    def start(self):
        EventSubscriptionController.raise_event(
            RunnerEvents.BEFORE_EXPERIMENT
        )

        threading.Thread(
            target=self.monitor.monitor,
            daemon=True
        ).start()

        print(f"[MASTER] Starting server on {self.host}:{self.port}")

        server_thread = threading.Thread(
            target=lambda: serve(
                self.api.app,
                host=self.host,
                port=self.port
            ),
            daemon=True
        )
        server_thread.start()

        while not self.task_manager.shutdown:
            time.sleep(1)

        print("[MASTER] Waiting for workers to shutdown...")
        time.sleep(10)
        print("[MASTER] Shutting down")
        os._exit(0)


def shutdown_server():
    func = request.environ.get('werkzeug.server.shutdown')
    if func is None:
        os._exit(0)
    func()