#coding=utf-8
from uliweb import expose, functions, models, jobschemes, request
import json as json_
from gevent.queue import Empty
from sqlalchemy import exc
import logging


log = logging.getLogger('linci')

def linci_get_jmanager():
    jm = None
    jid = request.values.get("id")
    jname = request.values.get("name")
    if jid or jname:
        model = models.lincimanager
        if jid:
            jm = model.get(int(jid))
        if not jm:
            jm = model.get(model.c.name==jname)
        if jm:
            jm = jm.get_gobj()
    return jm

@expose('/linci/job')
class LinciJobManager(object):
    def __begin__(self):
        self.jmanager = linci_get_jmanager()

    def new(self):
        sname = request.values.get("jscheme",settings.LINCI.default_job_scheme)
        return {
            "jscheme_name":sname,
            "jscheme":getattr(jobschemes,sname,None),
            "jobschemes":jobschemes,
        }

    def api_new(self):
        jscheme_name = request.values.get("jscheme_name")
        job_name = request.values.get("job_name")

        model_class = models.lincimanager
        model = model_class(name=job_name,
            scheme = jscheme_name)
        model.init_work_steps(getattr(jobschemes,jscheme_name).steps_num())
        try:
            model.save()
        except exc.IntegrityError as e:
            log.error("new job manager, scheme: %s, name: %s, error: %s"%(jscheme_name, job_name, e))
            return json({"msg":"fail to create new job: there already is a job named '%s'"%(job_name),"success":False})

        return json({"msg":"create new job successfully","success":True})

    def edit(self):
        return {
            "jmanager":self.jmanager,
            "jscheme":getattr(jobschemes,self.jmanager.scheme,None),
            "jcontext":{"jmanager":self.jmanager}
        }

    def api_update_job_common(self):
        if self.jmanager:
            job_name = request.values.get("job_name")
            if job_name:
                self.jmanager.name = job_name
                self.jmanager.save()
                return json({"msg":"update job common config successfully","success":True})
            else:
                return json({"msg":"fail to update, error: job name empty","success":False})
        else:
            return json({"msg":"fail to update, error: cannot find this job manager","success":False})

    def api_trigger(self):
        if self.jmanager:
            worker = self.jmanager.run()
            if worker:
                return json({"msg":"job triggered successfully","success":True})
            else:
                return json({"msg":"error: worker not found, request pending now","success":False})
        else:
            return json({"msg":"fail to trigger, error: cannot find this job manager","success":False})

    @expose('edit/<path:name>')
    def edit_path(self,name):
        return {}

    @expose('')
    def index(self):
        return {}

    def api_list_bootstraptable_data(self):
        if request.data:
            data = json_.loads(request.data)
        else:
            data = {}

        model = models.lincimanager
        l = model.all()

        sort = data.get("sort")
        order = data.get("order")
        limit = data.get("limit")
        offset = data.get("offset")
        if sort:
            sort_key = getattr(model.c,sort)
            if order:
                sort_key = getattr(sort_key,order)()
            l = l.order_by(sort_key)
        if limit:
            l = l.limit(limit)
        if offset:
            l = l.offset(offset)
        return json({"total":l.count(), "rows": [i.to_dict() for i in l]})

    @expose('view/<path:name>')
    def view(self,name):
        return {}

    @expose('view/<path:name>/<int:num>')
    def view_history(self,name,num):
        return {}

    def api_worker_pipe(self):
        worker_name = request.values.get("worker_name")
        if not worker_name:
            yield json_.dumps({"pipe_connect_success":False,"errmsg":"parameter worker_name not found"})
            return

        LinciWorker = models.linciworker
        worker = LinciWorker.get(LinciWorker.c.name==worker_name)
        if worker:
            worker = worker.get_gobj()

        if not worker:
            yield json_.dumps({"pipe_connect_success":False,"errmsg":"worker '%s' not found"%(worker_name)})
            return
        if worker.pipe_connected:
            yield json_.dumps({"pipe_connect_success":False,"errmsg":"worker '%s' have connect already"%(worker_name)})
            return

        worker.pipe_connected = True
        try:
            yield json_.dumps({"pipe_connect_success":True}) + '\n'
            while 1:
                try:
                    msg = worker.get_msg(timeout=10)
                    if msg:
                        log.info("receive a msg from queue of worker '%s'"%(worker_name))
                        yield json_.dumps(msg) + '\n'
                except Empty:
                    yield '\n'
        finally:
            log.error("connection of worker '%s' lost"%(worker_name))

            worker.pipe_connected = False
