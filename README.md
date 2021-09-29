# HTCAnalyze

![Build Status](https://github.com/psyinfra/HTCAnalyze/actions/workflows/tests.yml/badge.svg)
[![codecov](https://codecov.io/gh/psyinfra/HTCAnalyze/branch/master/graph/badge.svg)](https://codecov.io/gh/psyinfra/HTCAnalyze)

Search through [HTCondor](https://research.cs.wisc.edu/htcondor/) user log files
to extract information, identify patterns, and build time-based graphs of
resource utilization.

## Installation

**NOTE:** HTCAnalyze depends on the `htcondor` Python module, which currently
only runs on Linux.

This software can be installed directly from GitHub.
```
pip install git+https://github.com/psyinfra/HTCAnalyze.git
```

As a general recommendation, we encourage installing HTCAnalyze in a virtual
environment. If you are not already familiar with
[Python virtual environments](https://packaging.python.org/guides/installing-using-pip-and-virtual-environments/),
we highly recommend that you read up on them.

## Configuration File

A configuration file (`htcanalyze.conf`) can be used to control the default
behavior. This is especially useful for system administrators who wish to tune
the warning and error thresholds to their site requirements.

It can also be passed directly as a flag.
```
htcanalyze -c htcanalyze.conf [files/directories]
```

See [CONFIG](https://github.com/psyinfra/HTCAnalyze/blob/master/config/README.md)
for more information.

## Modes

HTCAnalyze has four modes of operation:

- `analyze`: provides detailed output, including a RAM
  histogram, HTCondor errors, and more.

- `summarize`: summarize a collection of log files, including average resource
  usage and execution time per-host.

- `analyzed-summary`: combined output of both the summarize and analyze
  modes.

Example output:

- analyzed-summary mode:

    ![Example](https://github.com/psyinfra/HTCAnalyze/blob/master/examples/example_analyzed_summary_mode.png)

- summarize mode:

    ![Example](https://github.com/psyinfra/HTCAnalyze/blob/master/examples/example_summary_mode.png)

- analyze mode:

    ![Example](https://github.com/psyinfra/HTCAnalyze/blob/master/examples/example_analyze_mode.png)


## Examples

- Print help text, listing functionality:
  ```
  htcanalyze -h (show a detailed description to all functionalities)
  ```
- Analyze a single file:
  ```
  htcanalyze logs/job_5991_0.log
  ```
- Analyze all log files in a directory (summarized by their states).
  ```
  htcanalyze logs/
  ```
- Summarize all files for a job cluster (exclude log files, without listed resources):
  ```
  htcanalyze -s logs/job_5991_*
  ```

## Testing

Tests can be found in the `tests/` dir. To invoke the tests, run:

Dependencies for tests are listed in `requirements-test.txt` and can be
installed by running:
```
pip install -U -r requirements-test.txt
```

To run the tests:

    pytest tests 

or with coverage:

    pytest  --cov=htcanalyze  tests

