#coding=utf-8

from shapps.linci.job.manager import LinciJobStep

class ShellCommand(LinciJobStep):
    inc_template_edit = "ShellCommand/inc_edit.html"
    worker_script = "shell_command.py"
