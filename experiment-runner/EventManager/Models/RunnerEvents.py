from enum import Enum, auto

class RunnerEvents(Enum):
    BEFORE_EXPERIMENT = auto()
    BEFORE_RUN        = auto()
    START_RUN         = auto()
    START_MEASUREMENT = auto()
    INTERACT          = auto()
    CONTINUE          = auto()
    STOP_MEASUREMENT  = auto()
    STOP_RUN          = auto()
    POPULATE_RUN_DATA = auto()
    AFTER_EXPERIMENT  = auto()
