from subprocess import Popen, PIPE, IO
from typing import Dict, List
from os import kill
from signal import SIGINT
from shlex import split
from time import sleep
from pandas import DataFrame, read_csv

from ConfigValidator.Config.Models.RunnerContext import RunnerContext


class Profiler:

    class Report:

        def populate() -> Dict:
            raise LookupError("\"populate\" is not implementented by this object!")


    def __init__(self, process: Popen, context: RunnerContext) -> None:
        self.target: Popen = process
        self.context: RunnerContext = context
        self.process: Popen = None

    @property
    def stdin(self) -> IO:
        return self.process.stdin

    @property
    def stdout(self) -> IO:
        return self.process.stdout

    @property
    def stderr(self) -> IO:
        return self.process.stderr

    def create_process(self, command: List[str]) -> None:
        self.process = Popen(command, stdin=PIPE, stdout=PIPE, stderr=PIPE)

    def start(self) -> None:
        raise LookupError("\"start\" is not implementented by this object!")

    def stop(self) -> None:
        kill(self.process.pid, SIGINT)
        self.process.wait()

    def report(self) -> Report:
        raise LookupError("\"report\" is not implementented by this object!")


Report = Profiler.Report


class PerformanceProfiler(Profiler):

    
    class PerformanceReport(Report):

        def __init__(self, data_frame: DataFrame) -> None:
            super(PerformanceReport, self).__init__()
            self.data_frame: DataFrame = data_frame

        def populate(self) -> Dict:
            run_data = {
                'cpu_usage': round(self.data_frame['cpu_usage'].mean(), 3),
                'memory_usage': round(self.data_frame['memory_usage'].mean(), 3),  # TODO: still not shown properly
                'execution_time': 'TODO',
            }

    
    def start(self):
        profiler_cmd = f"ps -p {self.target.pid} --noheader -o '%cpu %mem'"
        timer_cmd = f"while true; do {profiler_cmd}; sleep 1; done"
        self.create_process(["sh", "-c", timer_cmd])

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
            run_data = {
                'energy_usage': round(self.data_frame['CPU Power'].sum(), 3)
            }

    
    def start(self):
        profiler_cmd = f"powerjoular -l -p {self.target.pid} -f {self.context.run_dir / 'powerjoular.csv'}"
        self.create_process(split(profiler_cmd))

    def report(self) -> EnergyReport:
        data_frame = read_csv(self.context.run_dir / f"powerjoular.csv-{self.target.pid}.csv")
        data_frame.to_csv(self.context.run_dir / 'raw_data.csv', index=False)
        return EnergyReport(data_frame)


EnergyReport = EnergyProfiler.EnergyReport


class ExperimentProfiler(Profiler):


    class ExperimentReport(Report):
        
        def __init__(self, performance_report: PerformanceReport, energy_report: EnergyReport) -> None:
            super(ExperimentReport, self).__init__()

            self.performance_report: PerformanceReport = performance_report
            self.energy_report: EnergyReport = energy_report

        @property
        def performance_data(self) -> DataFrame:
            return self.performance_report.data_frame

        @property
        def energy_data(self) -> DataFrame:
            return self.energy_report.data_frame

        def populate(self) -> Dict:
            run_data = {
                'cpu_usage': round(self.performance_data['cpu_usage'].mean(), 3),
                'memory_usage': round(self.performance_data['memory_usage'].mean(), 3),  # TODO: still not shown properly
                'energy_usage': round(self.energy_data['CPU Power'].sum(), 3),
                'execution_time': 'TODO',
            }

    
    def __init__(self, process: Popen, context: RunnerContext) -> None:
        super(ExperimentProfiler, self).__init__(process)
    
        self.performance_profiler: PerformanceProfiler = PerformanceProfiler(process, context)
        self.energy_profiler: EnergyProfiler = EnergyProfiler(process, context)

    @property
    def performance_process(self) -> Popen:
        return self.performance_profiler.process

    @property
    def energy_process(self) -> Popen:
        return self.energy_profiler.process

    def start(self):
        self.performance_profiler.start()
        self.energy_profiler.start()
        sleep(1)

    def stop(self):
        # making sure they get terminated as quickly as possible without delay
        kill(self.performance_process.pid, SIGINT)
        kill(self.energy_process.pid, SIGINT)
        self.performance_process.wait()
        self.energy_process.wait()

    def report(self) -> ExperimentReport:
        performance_report = self.performance_profiler.report()
        energy_report      = self.energy_profiler.report()

        return ExperimentReport(performance_report, energy_report)


ExperimentReport = ExperimentProfiler.ExperimentReport