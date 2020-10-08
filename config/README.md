## Structure

The default htcsetup.conf looks like this:
<details>
<summary>
htcanalyser.conf
</summary>

```
#
# this is a comment
# the following lines represent the default htcanalyser config setup
# there is no need to specify all of them, but it doesn't hurt
#
# lists must be specified like: [var1, var2, var3]

#! Setup of the Config file

files = [check-the-htcanalyser.conf]

# if std-log is not set, every file will be interpreted as a log file,
# except std-err and std-out files
# std-log = ''
std-err = .err
std-out = .out

# only for default and analyser mode
show-list = []
# valid values are: "std-err, std-out"
# This is checking for errors and warnings inside the stderr output of a job
# if a .err file is found, same with output, which will just return stdout in .out files

# ignore HTCondor related information that is gained within the process
ignore-list = []
# valid values are:
# "used-resources, requested-resources, allocated-resources,
# execution-details, all-resources, times, errors, host-nodes"


# everything with a deviation of more than 10% is tolerated
tolerated-usage = 0.1
# everything with a deviation of more than 25% is considered bad
bad-usage = 0.25

mode = default
# valid modes: [summarize, analyse, analysed-summary, default]


filter = []
filter-extended = false
## if set, filter is extended with these keywords:
## [err, warn, exception, aborted, abortion, abnormal, fatal]

# more features
verbose = false
# generate-log-file = htcanalyser.log
reverse-dns-lookup = False
recursive = False

```

These values are just the same as the defaults of the script,
so it would NOT change the output, if you do not have this config file

</details>


## Specification

This config file will be installed if you follow the installation on [README](https://github.com/psyinfra/htcompact/blob/master/README.md). \
But you can also just copy this into a file and run the script with that config file like:
```
htcanalyse -c config_file [files][arguments]
```

If you just run the script by:
```
htcanalyse -c config_file
```
This will run the script with the given config_file


Else if you just run the script by just:
```
htcanalyse
```
This will search for the config_file with the priorities from 1 (high) to 4 (low)
if NOT --no-config Flag is set:

1.  environment_dir/config/htcanalyser.conf (virtual environment)
2.  ~/.config/htcanalyser/htcanalyser.conf
3.  /etc/htcanalyser.conf
4.  else go with default settings


##### Note
Arguments given by the terminal have a higher priority,\
so that the settings in the config file for that particular argument will be ignored (not overwritten),\
but all the other arguments stay defined by the config file.

## Idea

Just move your config file to one of these locations,
the name has to be "htcanalyser.conf":
1.  project_dir/config
2.  ~/.config/htcanalyser
3.  /etc

<details>
<summary>
htcanalyser_setup.conf
</summary>

```
[documents] # section headers will be ignored
files = [log_file1 log_directory1]

[htc-files]
std-log = .log
std-err = .err
std-out = .out

[features]
mode = summarize
```
</details>

You could summarize *log_file1* and every log_file, that's found inside *log_directory1* just by:
```
htcanalyse -c htcanalyser_setup.conf
```

The idea is, that for a bunch of settings it's easier to go with config files, \
so you could have a specified file for just the summary mode and an other file just for the analyser mode and so on ...

If the name of the config file is changed to htcanalyser.conf 
and is moved to one of the locations specified above the call reduced to:
```
htcanalyse
```



