from uliweb.core.SimpleFrame import Finder
from uliweb import application
import logging

jobschemes = Finder('LINCI_JOB_SCHEMES')
jobsteps = Finder('LINCI_JOB_STEPS')

log = logging.getLogger('linci.job')

class LinciJobScheme(object):
    job_steps = []

    @classmethod
    def html_edit(cls,jcontext={}):
        return "\n".join([application.template(getattr(jobsteps,step).inc_template_edit,vars=dict(jcontext,jstep_index=jstep_index,step=jcontext["jmanager"].prop_work_steps[jstep_index])) for jstep_index,step in enumerate(cls.job_steps)])

    @classmethod
    def steps_num(cls):
        return len(cls.job_steps)

class LinciJobStep(object):
    pass
