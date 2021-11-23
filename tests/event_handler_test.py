"""
Module to test EventHandler,

In particualar testing that Wrapping of HTCondor JobEvent works,
that the wrapped object can be turned into own JobEvent objects.

As HTCondor JobEvent can't be initialized,
testing just default events from: tests/test_logs/valid_logs/normal_log.log

This includes testing of:
JobSubmissionEvent (000)
JobExecutionEvent (001)
JobTerminationEvent(005)
ImageSizeEvent (006)
"""
import pytest
# from htcanalyze.log_analyzer.event_handler import event_handler
from numpy import nan
from datetime import datetime
from htcanalyze.globals import STRP_FORMAT
from htcanalyze.log_analyzer.condor_log.logresource import (
    LogResources,
    CPULogResource,
    DiskLogResource,
    GPULogResource,
    MemoryLogResource
)
from htcanalyze.log_analyzer.event_handler.states import (
    NormalTerminationState
)
from htcanalyze.log_analyzer.event_handler.event_handler import (
    HTCJobEventWrapper,
    EventHandler
)


@pytest.fixture(scope="module")
def events():
    file = "tests/test_logs/valid_logs/normal_log.log"
    event_handler = EventHandler()
    normal_events = list(event_handler.get_htc_events(file))
    return {
        "event_handler": event_handler,
        "submission_event": normal_events[0],
        "execution_event": normal_events[1],
        "image_size_event": normal_events[2],
        "termination_event": normal_events[4]
    }


def test_submission_event(events):
    event_handler = events.get("event_handler")
    submission_event = HTCJobEventWrapper(events.get("submission_event"))
    event_number = 0
    assert submission_event.get("EventTypeNumber") == event_number
    assert submission_event.get("EventTime") == "2021-07-11T20:39:51"
    assert submission_event.get("MyType") == "SubmitEvent"
    assert submission_event.get("Subproc") == 0
    assert submission_event.get("Cluster") == 107799
    assert submission_event.get("Proc") == 0
    assert submission_event.get("SubmitHost") == (
        "<10.0.8.10:9618?addrs=10.0.8.10-9618&noUDP&sock=2364585_35f2_3>"
    )
    assert submission_event.event_number == event_number
    assert submission_event.time_stamp == datetime.strptime(
        "2021-07-11T20:39:51",
        STRP_FORMAT
    )
    own_event = event_handler.get_submission_event(submission_event)
    assert own_event.event_number == event_number
    assert own_event.time_stamp == datetime.strptime(
        "2021-07-11T20:39:51",
        STRP_FORMAT
    )
    assert own_event.submitter_address == "10.0.8.10"


def test_execution_event(events):
    event_handler = events.get("event_handler")
    execution_event = HTCJobEventWrapper(events.get("execution_event"))
    event_number = 1
    assert execution_event.get("EventTypeNumber") == event_number
    assert execution_event.get("EventTime") == "2021-07-11T20:39:54"
    assert execution_event.get("MyType") == "ExecuteEvent"
    assert execution_event.get("Subproc") == 0
    assert execution_event.get("Cluster") == 107799
    assert execution_event.get("Proc") == 0
    assert execution_event.get("ExecuteHost") == (
        "<10.0.9.201:9618?addrs=10.0.9.201-9618&noUDP&sock=1637_6c9f_3>"
    )
    assert execution_event.event_number == event_number
    assert execution_event.time_stamp == datetime.strptime(
        "2021-07-11T20:39:54",
        STRP_FORMAT
    )
    own_event = event_handler.get_execution_event(execution_event)
    assert own_event.event_number == event_number
    assert own_event.time_stamp == datetime.strptime(
        "2021-07-11T20:39:54",
        STRP_FORMAT
    )
    assert own_event.host_address == "10.0.9.201"


def test_image_size_event(events):
    event_handler = events.get("event_handler")
    image_size_event = HTCJobEventWrapper(events.get("image_size_event"))
    event_number = 6
    assert image_size_event.get("EventTypeNumber") == event_number
    assert image_size_event.get("EventTime") == "2021-07-11T20:40:03"
    assert image_size_event.get("Subproc") == 0
    assert image_size_event.get("Cluster") == 107799
    assert image_size_event.get("Proc") == 0
    assert image_size_event.get("ResidentSetSize") == 448
    assert image_size_event.get("Size") == 448
    assert image_size_event.get("MemoryUsage") == 1
    assert image_size_event.get("MyType") == "JobImageSizeEvent"
    assert image_size_event.event_number == event_number
    assert image_size_event.time_stamp == datetime.strptime(
        "2021-07-11T20:40:03",
        STRP_FORMAT
    )
    own_event = event_handler.get_image_size_event(image_size_event)
    assert own_event.event_number == event_number
    assert own_event.time_stamp == datetime.strptime(
        "2021-07-11T20:40:03",
        STRP_FORMAT
    )
    assert own_event.size_update == 448
    assert own_event.resident_set_size == 448
    assert own_event.memory_usage == 1


def test_termination_event(events):
    event_handler = events.get("event_handler")
    termination_event = HTCJobEventWrapper(events.get("termination_event"))
    event_number = 5
    assert termination_event.get("EventTypeNumber") == event_number
    assert termination_event.get("EventTime") == "2021-07-11T20:45:50"
    assert termination_event.get("Subproc") == 0
    assert termination_event.get("Cluster") == 107799
    assert termination_event.get("Proc") == 0
    assert termination_event.get("MyType") == "JobTerminatedEvent"
    assert termination_event.get("TotalReceivedBytes") == 0
    assert termination_event.get("ReceivedBytes") == 0
    assert termination_event.get("MemoryUsage") == 922
    assert termination_event.get("Memory") == 20480
    assert termination_event.get("RunLocalUsage") == (
        "Usr 0 00:00:00, Sys 0 00:00:00"
    )
    assert termination_event.get("Cluster") == 107799
    assert termination_event.get("TotalSentBytes") == 0
    assert termination_event.get("Disk") == 22312484
    assert termination_event.get("Gpus") == 0
    assert termination_event.get("RequestCpus") == 1
    assert termination_event.get("Subproc") == 0
    assert termination_event.get("RequestDisk") == 20200960
    assert termination_event.get("DiskUsage") == 4
    assert termination_event.get("Cpus") == 1
    assert termination_event.get("TotalRemoteUsage") == (
        "Usr 0 00:03:14, Sys 0 00:00:41"
    )
    assert termination_event.get("SentBytes") == 0
    assert termination_event.get("CpusUsage") == 0.11
    assert termination_event.get("TerminatedNormally") is True
    assert termination_event.get("ReturnValue") == 1
    assert termination_event.get("RunRemoteUsage") == (
        "Usr 0 00:03:14, Sys 0 00:00:41"
    )
    assert termination_event.get("TotalLocalUsage") == (
        "Usr 0 00:00:00, Sys 0 00:00:00"
    )
    assert termination_event.event_number == event_number
    assert termination_event.time_stamp == datetime.strptime(
        "2021-07-11T20:45:50",
        STRP_FORMAT
    )

    own_event = event_handler.get_job_terminated_event(termination_event)
    assert own_event.event_number == event_number
    assert own_event.time_stamp == datetime.strptime(
        "2021-07-11T20:45:50",
        STRP_FORMAT
    )
    assert isinstance(own_event.termination_state, NormalTerminationState)
    assert isinstance(own_event.resources, LogResources)
    assert own_event.resources.cpu_resource == CPULogResource(
        usage=0.11,
        requested=1,
        allocated=1
    )
    assert own_event.resources.disc_resource == DiskLogResource(
        usage=4,
        requested=20200960,
        allocated=22312484
    )
    assert own_event.resources.memory_resource == MemoryLogResource(
        usage=922,
        requested=20480,
        allocated=20480
    )
    assert own_event.resources.gpu_resource == GPULogResource(
        usage=nan,
        requested=nan,
        allocated=0
    )
    assert own_event.return_value == 1
