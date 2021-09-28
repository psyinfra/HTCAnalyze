"""Save HTCondor job execution details."""


class JobDetails:
    """
    Class to store and manage the different job details.

    Mostly the complexity lies in creating
    colored output depending on the states
    """

    state_colors = {
        'abnormal': 'red',
        'aborted': 'red',
        'error_while_reading': 'red',
        'normal': 'green',
        'waiting': 'blue',
        'executing': 'blue',
        'strange': 'red',
        'unknown': 'yellow'
    }

    def __init__(self):
        self.state_desc = None
        self.state = None
        self.submitted_by = None
        self.executing_on = None
        self.return_value = None

    def get_state_color(self):
        """Return the color for the given state."""
        return self.state_colors.get(self.state)

    def to_dict(self):
        """Resolve the given JobDetails to a dictionary."""
        titles = list()
        values = list()
        if self.state_desc and self.state:
            titles.append(self.state_desc)
            color = self.get_state_color()
            cpy_state = self.state
            if cpy_state == "error_while_reading":
                cpy_state = "Error while reading"
            cpy_state = cpy_state.capitalize()
            values.append(f"[{color}]{cpy_state}[/{color}]")
        if self.submitted_by:
            titles.append("Submitted by")
            values.append(self.submitted_by)
        if self.executing_on:
            titles.append("Executing on")
            values.append(self.executing_on)
        if self.return_value and self.state:
            title = "Terminated by signal" if \
                self.state == 'abnormal' else "Return value"
            titles.append(title)
            values.append(self.return_value)

        return {
            "Execution details": titles,
            "Values": values
        }


def format_job_state(state):
    """Format the state to a colored capitalized string."""
    dummy_jd = JobDetails()
    dummy_jd.state = state
    color = dummy_jd.get_state_color()
    if state == "error_while_reading":
        state = "Error while reading"
    return f"[{color}]{state.capitalize()}[/{color}]"
