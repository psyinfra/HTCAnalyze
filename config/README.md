## Structure

The default htcsetup.conf looks like this:
<details>
<summary>
htcanalyze.conf
</summary>

```
#
# this is a comment
# the following lines represent the default htcanalyze config setup
# there is no need to specify all of them, but it doesn't hurt
#
# lists must be specified like: [var1, var2, var3]

#! Setup of the Config file

# if ext-log is not set, every file will be interpreted as a log file,
# except ext-err and ext-out files
ext-log = .log
ext-err = .err
ext-out = .out

# only for default and analyze mode
show = []
# valid values are: "htc-err, htc-out"
# This is checking for errors and warnings inside the stderr output of a job
# if a .err file is found, same with output, which will just return stdout in .out files

# everything with a deviation of more than 10% is tolerated
tolerated-usage = 0.1
# everything with a deviation of more than 25% is considered bad
bad-usage = 0.25

# more features
analyze = False
rdns-lookup = False
recursive = False

```

These values are just the same as the defaults of the script,
so it would NOT change the output, if you do not have this config file

</details>


## Specification

This config file will be installed if you follow the installation on [README](https://github.com/psyinfra/HTCanalyze/blob/master/README.md). \
But you can also just copy this into a file and run the script with that config file like:
```
htcanalyze -c config_file [files][arguments]
```

Else if you just run the script by just:
```
htcanalyze
```
If the --ignore-config Flag is NOT set, this will search following locations for the config_file with the priorities from 1 (low) to 5 (high):

1. default settings (no config file was found)
2. /etc/htcanalyze.conf
3. ~/.config/htcanalyze.conf
4. <sys_prefix>/HTCAnalyze/config/htcanalyze.conf
5. <sys_prefix>/HTCAnalyze/htcanalyze.conf


##### Note
Arguments given by the terminal have a higher priority,\
so that the settings in the config file for that particular argument will be ignored (not overwritten),\
but all the other arguments stay defined by the config file.

## Idea

Just move your config file to one of these locations,
the name has to be "htcanalyze.conf":
1.  project_dir/config
2.  ~/.config/htcanalyze
3.  /etc

The idea is, that for a bunch of settings it's easier to go with config files, \
so you could have a specified file for just the summary mode and another file just for the analyze mode and so on ...

