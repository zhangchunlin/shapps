#coding=utf-8

from shapps.linci.job.manager import LinciJobScheme

class SimpleShell(LinciJobScheme):
    label = "Simple shell"
    job_steps = ["shell_command"]
