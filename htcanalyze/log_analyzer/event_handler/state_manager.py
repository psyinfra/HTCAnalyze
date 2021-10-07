"""State Manager Module."""

from enum import Enum


class State(Enum):
    NORMAL_TERMINATION = 0
    ABNORMAL_TERMINATION = 1
    WAITING = 2
    RUNNING = 3
    ERROR_WHILE_READING = 4
    ABORTED = 5
    JOB_HELD = 6
    SHADOW_EXCEPTION = 7
    UNKNOWN = 8
    INVALID_HOST_ADDRESS = 9
    INVALID_USER_ADDRESS = 10

    @property
    def __dict__(self):
        return {
            "name": self.name,
            "value": self.value
        }


class JobState(Enum):
    NORMAL_TERMINATION = State.NORMAL_TERMINATION.value
    ABNORMAL_TERMINATION = State.ABNORMAL_TERMINATION.value
    WAITING = State.WAITING.value
    RUNNING = State.RUNNING.value
    ERROR_WHILE_READING = State.ERROR_WHILE_READING.value
    ABORTED = State.ABORTED.value

    @property
    def __dict__(self):
        return {
            "name": self.name,
            "value": self.value
        }


class ErrorState(Enum):
    ABORTED = State.ABORTED.value
    JOB_HELD = State.JOB_HELD.value
    SHADOW_EXCEPTION = State.SHADOW_EXCEPTION.value
    ERROR_WHILE_READING = State.ERROR_WHILE_READING.value
    INVALID_HOST_ADDRESS = State.INVALID_HOST_ADDRESS.value
    INVALID_USER_ADDRESS = State.INVALID_USER_ADDRESS.value

    @property
    def __dict__(self):
        return {
            "name": self.name,
            "value": self.value
        }


class StateColors(Enum):
    NORMAL_TERMINATION = 'green'
    BAD_TERMINATION = 'red'
    RUNNING = 'blue'
    UNKNOWN_BEHAVIOUR = 'yellow'
    DEFAULT = 'default'


class StateManager:

    _state: JobState = None

    @property
    def state(self) -> JobState:
        return self._state

    @state.setter
    def state(self, state):
        self._state = state

    def get_state_color(self) -> str:
        if self._state == JobState.NORMAL_TERMINATION:
            return StateColors.NORMAL_TERMINATION.value
        elif (
                self._state == JobState.ABNORMAL_TERMINATION or
                self._state == JobState.ERROR_WHILE_READING or
                self._state == JobState.ABORTED
        ):
            return StateColors.BAD_TERMINATION.value
        elif (
                self._state == JobState.WAITING or
                self._state == JobState.RUNNING
        ):
            return StateColors.RUNNING.value
        elif self._state == JobState.UNKNOWN:
            return StateColors.UNKNOWN_BEHAVIOUR.value
        else:
            return StateColors.DEFAULT.value

    @property
    def __dict__(self):
        return {
            "state": self.state
        }

    def __repr__(self):
        color = self.get_state_color()
        return f"[{color}]{self.state.name}[/{color}]"
