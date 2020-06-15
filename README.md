# Script to summarise HTCondor log files

### Requirements:
- python3
- pip
- git

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
pip install git+https://jugit.fz-juelich.de/inm7/infrastructure/loony_tools/htcondor-summariser-script.git
```
- The script sits here:
```
/bin/htcompact
```
also a basic setup.conf file will be installed, which is able to manage all command line arguments \
check: [link to config]() for more information
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

htcompact path_to_logs/job_5991_* -s  (summarise all files starting with: job_5991_)

htcompact path_to_logs/395_2.log --table-format=pretty 
```

 lets consider we also have a config file (see: [link to config]()) \
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
see: [link to config]() 

possible output example:

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



#### Contribution:
please do




#### Used frameworks and packages:
- tabulate
- pandas (especially pandas.DataFrame)
- regular expresssions (Package re)
- sys
- os
- getopt
- datetime
- logging
- plotille