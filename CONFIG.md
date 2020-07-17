## Structure:

The default htcsetup.conf looks like this:
<details>
<summary>
htcompact.conf
</summary>

```
# this is a comment
# the following lines represent the default htcompact config setup
# the [] represent sections and the lines below the corresponding attributes
# there is no need to specify all of them, but it doesn't hurt
#
# Values will be accepted as True for :
# ["true", "yes", "y", "ja", "j", "enable", "enabled", "wahr", "0"]
# everything else will be interpreted as False

[documents]
files = check_the_htcompact.conf

[formats]
table_format = pretty
#       Available Types:
#       plain, simple, github, grid, fancy_grid, pipe,
#       orgtbl, rst, mediawiki, html, latex, latex_raw,
#       latex_booktabs, tsv, default: simple

[htc-files]
stdlog = .log
stderr = .err
stdout = .out

[show-more]
show_std_errors = no
show_std_output = no
show_std_warnings = no

# ignore HTCondor related information that is gained within the process
[ignore]
ignore_list = None
# valid values are: "allocated-resources, execution-details, all-resources"
# these might be added in future:
# used-resources, requested-resources, times, gpus, cpu, errors, warnings

[thresholds]
 # everything under 75% is considered "wasting sources"
low_usage = 0.75
# everything over 120% is considered "overusing sources"
bad_usage = 1.2

[modes]
filter_mode = False
summarizer_mode = False
analyser_mode = False

# if filter_mode set true, this section must be set,
# else the script does not know what to filter for
[filter]
filter_keywords = gpu
filter_extended = false
## if set, filter is extended with these keywords:
## [err, warn, exception, aborted, abortion, abnormal, fatal]

[features]
generate_log_file = False
to_csv = False
reverse_dns_lookup = disabled

```

These values are just the same as the defaults of the script,
so it would NOT change the output, if you do not have this config file

</details>


## Specification

This config file will be installed if you follow the installation on [README](https://github.com/psyinfra/htcompact/blob/master/README.md). \
But you can also just copy this into a file and run the script with that config file like:
```
htcompact config_file [files][arguments]
```

If you just run the script by:
```
htcompact config_file
```
This will search for the config_file with the priorities from 1 (high) to 5 (low)
if NOT --no-config Flag is set:

1. search config_file directly in the current working directory
2. search config file from current environment_directory/config (virtual environment)
3. search for config_file in ~/.config/htcompact
4. search for config_file in /etc
5. else go with default settings

Else if you just run the script by just:
```
htcompact
```
This will search for "htcompact.conf" as default in the same order

##### Note:
Arguments given by the terminal have a higher priority,\
so that the settings in the config file for that particular argument will be ignored (not overwritten),\
but all the other arguments stay defined by the config file.

## Idea

For example your config file sits in one of these directories:
1. current_working_directory
2. project_directory/config
3. ~/.config/htcompact
4. /etc

<details>
<summary>
htcompact_setup.conf
</summary>

```
[documents]
files = log_file1 log_directory1

[htc-files]
stdlog = .log
stderr = .err
stdout = .out

[features]
summarize = true
```
</details>

You could summarize *log_file1* and every log_file, that's found inside *log_directory1* just by:
```
htcompact htcompact_setup.conf
```

The idea is, that for a bunch of settings it's easier to go with config files, \
so you could have a specified file for just the summary mode and an other file just for the analyser mode and so on ...

If the name of the config file is changed to htcompact.conf the call reduced to:
```
htcompact
```

