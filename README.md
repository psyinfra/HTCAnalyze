# HTCAnalyse

[![Build Status](https://travis-ci.org/psyinfra/HTCAnalyser.svg?branch=master)](https://travis-ci.org/psyinfra/HTCAnalyser)
[![codecov](https://codecov.io/gh/psyinfra/HTCAnalyser/branch/master/graph/badge.svg)](https://codecov.io/gh/psyinfra/HTCAnalyser)
[![Codacy Badge](https://app.codacy.com/project/badge/Grade/d8fff0409968467d855a0efbf2ab8f7d)](https://www.codacy.com/gh/psyinfra/HTCAnalyser?utm_source=github.com&amp;utm_medium=referral&amp;utm_content=psyinfra/HTCAnalyser&amp;utm_campaign=Badge_Grade)

Search through [HTCondor](https://research.cs.wisc.edu/htcondor/) user log files
to extract information, identify patterns, and build time-based graphs of
resource utilization.

## Installation

**NOTE:** HTCAnalyse depends on the `htcondor` Python module, which currently
only runs on Linux.

This software can be installed directly from GitHub.
```
pip install git+https://github.com/psyinfra/HTCAnalyser.git
```

As a general recommendation, we encourage installing HTCAnalyse in a virtual
environment. If you are not already familiar with
[Python virtual environments](https://packaging.python.org/guides/installing-using-pip-and-virtual-environments/),
we highly recommend that you read up on them.

## Configuration File

A configuration file (`htcanalyser.conf`) can be used to control the default
behavior. This is especially useful for system administrators who wish to tune
the warning and error thresholds to their site requirements.

It can also be passed directly as a flag.
```
htcanalyse -c htcanalyser.conf [files/directories]
```

See [CONFIG](https://github.com/psyinfra/HTCAnalyser/blob/master/config/README.md)
for more information.

## Modes

HTCAnalyse has four modes of operation:

- `default`: a terse output describing the essentials.

- `analyse`: provides more  detailed output than `default`, including a RAM
  histogram, HTCondor errors, and more.

- `summarize`: summarize a collection of log files, including average resource
  usage and execution time per-host.

- `analysed-summary`: combined output of both the summarizer and analyzer
  modes.

Example output:

- default mode:

    ```
    The job procedure of : ../logs/job_5991_0.log
    +-------------------+--------------------+
    | Executing on Host |      cpu: 3        |
    |       Port        |       96186        |
    |      Runtime      |      0:00:04       |
    | Termination State | Normal termination |
    |   Return Value    |         0          |
    +-------------------+--------------------+
    +------------+-------+-----------+-----------+
    | Rescources | Usage | Requested | Allocated |
    +------------+-------+-----------+-----------+
    |    Cpu     |   0   |     1     |     1     |
    |    Disk    | 5000  |   5000    |  3770642  |
    |   Memory   |   0   |   6000    |   6016    |
    +------------+-------+-----------+-----------+
    ```

- summarizer mode:

    ![Example](https://github.com/psyinfra/HTCAnalyser/blob/master/examples/example_summary_mode.png)

- analyser mode:

    ![Example](https://github.com/psyinfra/HTCAnalyser/blob/master/examples/example_analyser_mode.png)

- analysed-summary mode:

    ![Example](https://github.com/psyinfra/HTCAnalyser/blob/master/examples/example_analysed_summary_mode.png)

## Examples

- Print help text, listing functionality:
  ```
  htcanalyse -h (show a detailed description to all functionalities)
  ```
- Analyse a single file:
  ```
  htcanalyse logs/job_5991_0.log
  ```
- Analyse all log files in a directory.
  ```
  htcanalyse logs/
  ```
- Summarize all files for a job cluster:
  ```
  htcanalyse -s logs/job_5991_*
  ```
- Print a pretty table:
  ```
  htcanalyse logs/395_2.log --table-format=pretty
  ```

## Testing

Tests can be found in the `tests/` dir. To invoke the tests, run:

Dependencies for tests are listed in `requirements-test.txt` and can be
installed by running:
```
pip install -U -r requirements-test.txt
```

To run the tests:
```
pytest tests
```

More details can be found in [TESTS](https://github.com/psyinfra/HTCAnalyser/blob/master/tests/README.md).
