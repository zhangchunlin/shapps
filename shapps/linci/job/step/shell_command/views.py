#coding=utf-8
from uliweb import expose, functions, request

@expose("/linci/job/api_update_shell")
def api_update_shell():
    jmanager = functions.linci_get_jmanager()
    if jmanager:
        jstep_index = int(request.values.get("jstep_index"))
        shell_script = request.values.get("shell_script")
        step = {
            "step" : "shell_command",
            "shell_script" : shell_script
        }
        jmanager.update_work_step(jstep_index,step)
        return json({"msg":"update job shell config successfully","success":True})
    else:
        return json({"msg":"fail to update, error: cannot find this job manager","success":False})
