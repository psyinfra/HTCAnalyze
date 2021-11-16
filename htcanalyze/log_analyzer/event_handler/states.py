"""State Module."""
from abc import ABC
from htcanalyze import ReprObject


class State(ReprObject, ABC):
    """Abstract state class."""
    _name: str

    @property
    def name(self):
        """Name getter."""
        return self._name

    @name.setter
    def name(self, name):
        """Name setter."""
        self._name = name

    def __eq__(self, other):
        return isinstance(self, other.__class__)

    def __hash__(self):
        """Use class name as hash to use states as dictionary keys."""
        return hash(self.__class__.name)


class JobState(State, ABC):
    """Represents the current state of a job."""
    _color: str = None

    @property
    def color(self):
        """Color getter."""
        return self._color

    @color.setter
    def color(self, color):
        """Color setter."""
        self._color = color


class TerminationState(JobState, ABC):
    """Abstract class to represent a termination state."""


class NormalTerminationState(TerminationState):
    """Represents a normal termination state."""

    def __init__(self):
        self.color = "green"
        self.name = "NORMAL_TERMINATION"


class AbnormalTerminationState(TerminationState):
    """Represents an abnormal termination state."""

    def __init__(self):
        self.color = "red"
        self.name = "ABNORMAL_TERMINATION"


class ExecutionState(JobState, ABC):
    """Abstract class to represent an execution state."""

    def __init__(self):
        self.color = "blue"


class WaitingState(ExecutionState):
    """Represents a waiting state."""

    def __init__(self):
        super().__init__()
        self.name = "WAITING"


class RunningState(ExecutionState):
    """Represents a running state."""

    def __init__(self):
        super().__init__()
        self.name = "RUNNING"


class ErrorState(State, ABC):
    """Represents an error state."""

    def __init__(self):
        self.color = "red"


class ErrorWhileReadingState(JobState, ErrorState):
    """Represents an error while reading state."""
    def __init__(self):
        super().__init__()
        self.name = "ERROR_WHILE_READING"


class InvalidHostAddressState(ErrorState):
    """Represents an invalid host address state."""

    def __init__(self):
        super().__init__()
        self.name = "INVALID_HOST_ADDRESS"


class InvalidUserAddressState(ErrorState):
    """Represents an invalid user address state."""

    def __init__(self):
        super().__init__()
        self.name = "INVALID_USER_ADDRESS"


class AbortedState(TerminationState, ErrorState):
    """Represents an abortion state."""

    def __init__(self):
        super().__init__()
        self.name = "ABORTED"


class JobHeldState(ErrorState):
    """Represents a job held state."""

    def __init__(self):
        super().__init__()
        self.name = "JOB_HELD"


class ShadowExceptionState(ErrorState):
    """Represents a shadow exception state."""

    def __init__(self):
        super().__init__()
        self.name = "SHADOW_EXCEPTION"
