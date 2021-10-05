from enum import Enum
from .job_events import JobState


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



