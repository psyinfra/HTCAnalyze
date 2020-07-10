# Script to summarize HTCondor log files

#### Requirements:
These are the packages you will need for manual installation
- python version >= 3.7
- [setuptools-git-version](https://pypi.org/project/setuptools-git-version/)
- [tabulate](https://pypi.org/project/tabulate/)
- [plotille](https://pypi.org/project/plotille/)
- [rich](https://pypi.org/project/rich/)
- pandas (especially pandas.DataFrame)

### Installation:
    
- first of all I would recommend a [virtual environment](https://packaging.python.org/guides/installing-using-pip-and-virtual-environments/), so that all the packages will only sit inside this scope:
```
python3 -m venv env 
```
Now you should see a directory called *env* inside your current directory,
- now you need to activate the virtual environment
```
source env/bin/activate
```
- to install all necesarry packages run:
```
pip install git+https://github.com/psyinfra/htcompact.git
```
- The script sits here:
```
/bin/htcompact
```
also a basic setup.conf file will be installed, which is able to manage all command line arguments \
check: [CONFIG.md](https://github.com/psyinfra/htcompact/blob/master/CONFIG.md) for more information
<br>
 
### get started:
- *htcompact --help* for detailed description
- general use :
**htcompact \[files] \[directories] \[config_file] \[args]**

lets consider we have a directory /logs with this structure:

    logs >
        395_2.log
        
        job_5991_0.err
        job_5991_0.log
        job_5991_0.out
        
        job_5992_23.err
        job_5992_23.log
        job_5992_23.out
        
        ...

#### possible configurations:
```
htcompact -h (show a detailed description to all functionalities)

htcompact path_to_logs/job_5991_0.log

htcompact path_to_logs/job_5991_0 path_to_logs/job_5992_23.log

htcompact path_to_logs (run through all files inside the logs directory)

htcompact path_to_logs/job_5991_* -s  (summarize all files starting with: job_5991_)

htcompact path_to_logs/395_2.log --table-format=pretty 
```

 lets consider we also have a config file (see: [CONFIG.md](https://github.com/psyinfra/htcompact/blob/master/CONFIG.md)) \
 a default setup.conf should already exist inside the project folder
 
 possible configurations could be reduced to something like: 
```
htcompact ( will search for setup.conf)
or
htcompact setup.conf 
or
htcompact [files/directories] setup.conf (ignores files/directories set inside the config file)
```

where all arguments, files and directories can be set inside that config file \
see: [CONFIG.md](https://github.com/psyinfra/htcompact/blob/master/CONFIG.md) 

Examples:

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

    ![Example](https://github.com/psyinfra/htcompact/blob/master/examples/example_summary_mode.png)

- analyser mode:

    ![Example](https://github.com/psyinfra/htcompact/blob/master/examples/example_analyser_mode.png)
    
- analysed summary mode:

    ![Example](https://github.com/psyinfra/htcompact/blob/master/examples/example_analysed_summary_mode.png)

#### Contribution:
please do

