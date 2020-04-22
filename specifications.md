**Necessary features:**

```
-name of executing node
-duration of job
-max RAM used (vs requested)
-max disk used (vs requested)
-average CPU usage (vs requested)
-support GPU usage
-note errors (allow for silencing, as many programs log to STDERR for non-errors)
```

**Non-functional, but usefull features:**

```
-use color to highlight exceeding requested resources
-use color to highlight severely under-utilization of requested resources
-histogram of RAM usage over job lifetime
-ingest a cluster's worth of .log files; provide a summarized overview of all jobs

-provide a histogram for typical job duration, RAM, Disk, CPU

-number of jobs executed per node
-average job duration per node

-> GUI apllicative 
-> Programming language: python3

```

NOTE: it is of potential interest to see how much job-related information is stored in the schedd logs.