"""Test the Resource class."""

import pytest

from numpy import nan
from typing import List

# import Resource class
import condor_log.resource as htcan_res
Resource = htcan_res.Resource


@pytest.fixture
def job_res() -> List[List[Resource]]:
    """Fixture sample of 4 job logs resources."""
    # calc on 4 jobs
    descriptions = ["CPU", "Disk (KB)", "Memory (MB)"]
    # each line represents one joblog file,
    #   with values for the given descriptions
    usages = [0.11, 30, 920,
              0.13, 34, 960,
              0.78, 205, 650,
              0.11, 30, 1123]
    requested = [1, 232020, 24000,
                 1, 234020, 26430,
                 1, 180520, 19340,
                 1, 212829, 23217]
    allocated = [1, 234020, 24000,
                 1, 240020, 26430,
                 1, 190720, 19340,
                 1, 222800, 23220]
    job_res_list = list()
    for i in range(4):
        resources = list()
        for j in range(3):
            index = i*3+j

            resources.append(Resource(descriptions[index % 3],
                                      usages[index],
                                      requested[index],
                                      allocated[index]))
        job_res_list.append(resources)

    return job_res_list


def test_simple_res():
    simple_res = Resource("CPU", 0.7, 1.0, 1)

    assert simple_res.description == "CPU"
    assert simple_res.usage == 0.7
    assert simple_res.requested == 1.0
    assert simple_res.allocated == 1.0
    assert simple_res.warning_level is None

    assert simple_res.get_color() == "default"

    simple_res.chg_lvl_by_threholds(0.25, 0.1)
    assert simple_res.warning_level == "error"
    assert simple_res.get_color() == "red"

    simple_res.chg_lvl_by_threholds(0.35, 0.1)
    assert simple_res.warning_level == "warning"
    assert simple_res.get_color() == "yellow"

    assert str(simple_res) == \
           "Resource: CPU\n" \
           "Usage: [yellow]0.7[/yellow], " \
           "Requested: 1.0, " \
           "Allocated: 1"
    assert repr(simple_res) == "(CPU, 0.7, 1.0, 1, warning)"


def test_strange_res():
    strange_res = Resource("CPU", 0.11, nan, nan)
    assert strange_res.description == "CPU"
    assert strange_res.usage == 0.11
    assert str(strange_res.requested) == "nan"
    assert str(strange_res.allocated) == "nan"
    assert strange_res.warning_level is None
    assert strange_res.get_color() == "default"

    strange_res.chg_lvl_by_threholds(0.25, 0.1)
    assert strange_res.warning_level == "error"
    assert strange_res.get_color() == "red"

    assert str(strange_res) == \
           "Resource: CPU\n" \
           "Usage: [red]0.11[/red], " \
           "Requested: nan, " \
           "Allocated: nan"
    assert repr(strange_res) == "(CPU, 0.11, nan, nan, error)"


def test_create_avg_on_resources(job_res):
    resources = htcan_res.create_avg_on_resources(job_res)
    expected_vals = [("Average CPU", 0.283, 1.0, 1.0),
                     ("Average Disk (KB)", 74.75, 214847.25, 221890.0),
                     ("Average Memory (MB)", 913.25, 23246.75, 23247.5)]
    for i, res in enumerate(resources):
        vals = expected_vals[i]
        assert res.description == vals[0]
        assert res.usage == vals[1]
        assert res.requested == vals[2]
        assert res.allocated == vals[3]
        assert res.warning_level is None

        res.chg_lvl_by_threholds(0.4, 0.2)
        assert res.warning_level == "error"


def test_resources_to_dict(job_res):
    first_res = job_res[0]
    res_dict = htcan_res.resources_to_dict(first_res)
    assert res_dict == {
        'Resources': ['CPU', 'Disk (KB)', 'Memory (MB)'],
        'Usage': ['[default]0.11[/default]',
                  '[default]30[/default]',
                  '[default]920[/default]'],
        'Requested': [1, 232020, 24000],
        'Allocated': [1, 234020, 24000]
    }


def test_dict_to_resources():
    res_dict = {
        'Resources': ['CPU', 'Disk (KB)', 'Memory (MB)'],
        'Usage': [0.11, 30, 920],
        'Requested': [1, 232020, 24000],
        'Allocated': [1, 234020, 24000]
    }

    resources = htcan_res.dict_to_resources(res_dict)
    for i, res in enumerate(resources):
        assert res.description == res_dict.get("Resources")[i]
        assert res.usage == res_dict.get("Usage")[i]
        assert res.requested == res_dict.get("Requested")[i]
        assert res.allocated == res_dict.get("Allocated")[i]
        assert res.warning_level is None
