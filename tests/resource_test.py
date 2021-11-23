"""Test the Resource class."""
from numpy import nan

# import Resource class
from htcanalyze.log_analyzer.condor_log.logresource import (
    CPULogResource,
    DiskLogResource,
    MemoryLogResource,
    GPULogResource,
    LogResource,
    LevelColors
)


def test_cpu_res():
    simple_res = CPULogResource(0.7, 1.0, 1)

    assert simple_res.description == "Cpus"
    assert simple_res.usage == 0.7
    assert simple_res.requested == 1.0
    assert simple_res.allocated == 1.0

    assert repr(simple_res) == (
        '{'
        '"usage": 0.7, '
        '"requested": 1.0, '
        '"allocated": 1, '
        '"description": "Cpus"'
        '}'
    )


def test_disk_res():
    simple_res = DiskLogResource(0.7, 1.0, 1)

    assert simple_res.description == "Disk (KB)"
    assert simple_res.usage == 0.7
    assert simple_res.requested == 1.0
    assert simple_res.allocated == 1.0

    assert repr(simple_res) == (
        '{'
        '"usage": 0.7, '
        '"requested": 1.0, '
        '"allocated": 1, '
        '"description": "Disk (KB)"'
        '}'
    )


def test_memory_res():
    simple_res = MemoryLogResource(0.7, 1.0, 1)

    assert simple_res.description == "Memory (MB)"
    assert simple_res.usage == 0.7
    assert simple_res.requested == 1.0
    assert simple_res.allocated == 1.0

    assert repr(simple_res) == (
        '{'
        '"usage": 0.7, '
        '"requested": 1.0, '
        '"allocated": 1, '
        '"description": "Memory (MB)"'
        '}'
    )


def test_gpu_res():
    simple_res = GPULogResource(0.7, 1.0, 1, "CUDA")

    assert simple_res.description == "Gpus (Average)"
    assert simple_res.usage == 0.7
    assert simple_res.requested == 1.0
    assert simple_res.allocated == 1.0
    assert simple_res.assigned == "CUDA"

    assert repr(simple_res) == (
        '{'
        '"usage": 0.7, '
        '"requested": 1.0, '
        '"allocated": 1, '
        '"description": "Gpus (Average)", '
        '"assigned": "CUDA"'
        '}'
    )


def test_strange_res():
    strange_res = CPULogResource(0.11, nan, nan)
    assert strange_res.description == "Cpus"
    assert strange_res.usage == 0.11
    assert str(strange_res.requested) == "nan"
    assert str(strange_res.allocated) == "nan"

    assert repr(strange_res) == (
        '{'
        '"usage": 0.11, '
        '"requested": NaN, '
        '"allocated": NaN, '
        '"description": "Cpus"'
        '}'
    )


def test_add():
    first_resource = CPULogResource(0.7, 1.0, 1)
    second_resource = CPULogResource(0.8, 1.4, 12)
    sum_resource = first_resource + second_resource

    assert (first_resource + 0) == first_resource
    assert (first_resource + None) == first_resource
    assert sum_resource.usage == 0.7 + 0.8
    assert sum_resource.requested == 1.0 + 1.4
    assert sum_resource.allocated == 1 + 12
    assert sum_resource.description == "Cpus"

    empty_resource = CPULogResource(nan, nan, nan)
    assert first_resource + empty_resource == first_resource


def test_div():
    first_resource = LogResource(0.7, 1.0, 1)

    div_resource = first_resource / 2
    assert div_resource.usage == 0.35
    assert div_resource.requested == 0.5
    assert div_resource.allocated == 0.5
    assert div_resource.description is None

    empty_resource = LogResource(nan, nan, nan)
    assert empty_resource / 2 == empty_resource


def test_is_empty():
    assert not LogResource(0.7, 1.0, 1).is_empty()
    assert not LogResource(0.7, 1.0, nan).is_empty()
    assert not LogResource(0.7, nan, nan).is_empty()
    assert not LogResource(nan, 1.0, 1).is_empty()
    assert not LogResource(nan, 1.0, nan).is_empty()
    assert not LogResource(nan, nan, 1).is_empty()
    assert LogResource(nan, nan, nan).is_empty()


def test_is_equal():
    assert LogResource(0.7, 1.0, 2) == LogResource(0.7, 1.0, 2)
    assert not LogResource(0.7, 1.0, 2) == LogResource(0.7, 1.1, 2)
    assert not LogResource(0.7, 1.0, 2) == 1


def test_warning_lvl():
    simple_res = LogResource(0.7, 1.0, 1)

    warning_level = simple_res.get_warning_lvl_by_threshold(0.5, 0.35)
    assert warning_level == LevelColors.NORMAL
    assert simple_res.get_color(warning_level) == "green"

    warning_level = simple_res.get_warning_lvl_by_threshold(0.25, 0.1)
    assert warning_level == LevelColors.ERROR
    assert simple_res.get_color(warning_level) == "red"

    warning_level = simple_res.get_warning_lvl_by_threshold(0.35, 0.1)
    assert warning_level == LevelColors.WARNING
    assert simple_res.get_color(warning_level) == "yellow"

    strange_resource = LogResource(nan, 1.0, 1)

    warning_level = strange_resource.get_warning_lvl_by_threshold(0.35, 0.1)
    assert warning_level == LevelColors.LIGHT_WARNING
    assert strange_resource.get_color(warning_level) == "yellow2"



