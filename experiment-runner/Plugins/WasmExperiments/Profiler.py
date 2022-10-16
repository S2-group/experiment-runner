from subprocess import Popen
from typing import Dict
from os import kill
from signal import SIGINT
from shlex import split
from time import sleep
from pandas import DataFrame, read_csv

from Plugins.WasmExperiments.ProcessManager import ProcessManager
from ConfigValidator.Config.Models.RunnerContext import RunnerContext


class Profiler(ProcessManager):

    class Report:

        def populate() -> Dict:
            raise LookupError("\"populate\" is not implementented by this object!")


    def __init__(self, target_pid: int, context: RunnerContext) -> None:
        super(Profiler, self).__init__()

        self.target_pid: int = target_pid
        self.context: RunnerContext = context

    def start(self) -> None:
        self.reset()

    def stop(self) -> None:
        self.kill_process(SIGINT)

    def report(self) -> Report:
        raise LookupError("\"report\" is not implementented by this object!")


Report = Profiler.Report


class PerformanceProfiler(Profiler):

    
    class PerformanceReport(Report):

        def __init__(self, data_frame: DataFrame) -> None:
            super(PerformanceReport, self).__init__()
            self.data_frame: DataFrame = data_frame

        def populate(self) -> Dict:
            return {
                'cpu_usage': round(self.data_frame['cpu_usage'].mean(), 3),
                'memory_usage': round(self.data_frame['memory_usage'].mean(), 3),  # TODO: still not shown properly
                'execution_time': 'TODO',
            }

    
    def start(self) -> None:
        super(PerformanceProfiler, self).start()

        profiler_cmd = f"ps -p {self.target_pid} --noheader -o '%cpu %mem'"
        timer_cmd = f"while true; do {profiler_cmd}; sleep 1; done"
        self.create_shell_process(timer_cmd)

    def report(self) -> PerformanceReport:
        data_frame = DataFrame(columns=['cpu_usage', 'memory_usage'])

        for index, line in enumerate(self.stdout.readlines()):  # TODO: depends on order + is cryptic
            decoded_line = line.decode('ascii').strip()
            decoded_arr = decoded_line.split("  ")
            cpu_usage = float(decoded_arr[0])
            mem_usage = float(decoded_arr[1])
            data_frame.loc[index] = [cpu_usage, mem_usage]

        return PerformanceReport(data_frame)


PerformanceReport = PerformanceProfiler.PerformanceReport


class EnergyProfiler(Profiler):

    
    class EnergyReport(Report):
        
        def __init__(self, data_frame: DataFrame) -> None:
            super(EnergyReport, self).__init__()
            self.data_frame: DataFrame = data_frame

        def populate(self) -> Dict:
            return {
                'energy_usage': round(self.data_frame['CPU Power'].sum(), 3)
            }

    
    def start(self) -> None:
        super(EnergyProfiler, self).start()

        profiler_cmd = f"powerjoular -l -p {self.target_pid} -f {self.context.run_dir / 'powerjoular.csv'}"
        self.create_process(split(profiler_cmd))

    def report(self) -> EnergyReport:
        data_frame = read_csv(self.context.run_dir / f"powerjoular.csv-{self.target_pid}.csv")
        data_frame.to_csv(self.context.run_dir / 'raw_data.csv', index=False)
        return EnergyReport(data_frame)


EnergyReport = EnergyProfiler.EnergyReport


class WasmProfiler(Profiler):


    class WasmReport(Report):

        DATA_COLUMNS = ['energy_usage', 'execution_time', 'memory_usage', 'cpu_usage', 'storage']
        
        def __init__(self, performance_report: PerformanceReport, energy_report: EnergyReport) -> None:
            super(WasmReport, self).__init__()

            self.performance_report: PerformanceReport = performance_report
            self.energy_report: EnergyReport = energy_report

        @property
        def performance_data(self) -> DataFrame:
            return self.performance_report.data_frame

        @property
        def energy_data(self) -> DataFrame:
            return self.energy_report.data_frame

        def populate(self) -> Dict:
            return {
                'cpu_usage': round(self.performance_data['cpu_usage'].mean(), 3),
                'memory_usage': round(self.performance_data['memory_usage'].mean(), 3),  # TODO: verify on Raspberry
                'energy_usage': round(self.energy_data['CPU Power'].sum(), 3),
                'execution_time': 'TODO',
            }

    
    def __init__(self, target_pid: int, context: RunnerContext) -> None:
        super(WasmProfiler, self).__init__(target_pid, context)
    
        self.performance_profiler: PerformanceProfiler = PerformanceProfiler(target_pid, context)
        self.energy_profiler: EnergyProfiler = EnergyProfiler(target_pid, context)

    @property
    def performance_process(self) -> Popen:
        return self.performance_profiler.process

    @property
    def energy_process(self) -> Popen:
        return self.energy_profiler.process

    def start(self) -> None:
        super(WasmProfiler, self).start()

        self.performance_profiler.start()
        self.energy_profiler.start()
        sleep(1) # TODO: necessary?

    def stop(self) -> None:
        # making sure they get terminated as quickly as possible without waiting for termination of previous process

        if self.performance_process is not None:
            kill(self.performance_process.pid, SIGINT)

        if self.energy_process is not None:
            kill(self.energy_process.pid, SIGINT)

        self.performance_profiler.wait_for_process()
        self.energy_profiler.wait_for_process()

    def report(self) -> WasmReport:
        performance_report = self.performance_profiler.report()
        energy_report      = self.energy_profiler.report()

        return WasmReport(performance_report, energy_report)


WasmReport = WasmProfiler.WasmReport