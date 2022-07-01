from enum import Enum, auto

class OperationType(Enum):
    """If set to AUTO, an experiment will continue with the next run (after waiting `RunnerConfig.time_between_runs_in_ms` milliseconds)
    automatically without waiting for any other stimuli."""
    AUTO = auto()

    """If set to SEMI, an experiment will continue with the next run (after waiting `RunnerConfig.time_between_runs_in_ms` milliseconds),
    only if the callback for the event `RunnerEvents.CONTINUE` has returned."""
    SEMI = auto()
