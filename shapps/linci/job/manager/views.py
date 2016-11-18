#coding=utf-8
from uliweb import expose, functions, models
import json as json_
from gevent.queue import Empty
import logging


log = logging.getLogger('linci')

@expose('/linci')
class LinciJobManager(object):
    @expose('manager/new')
    def job_manager_new(self):
        return {}

    @expose('manager/edit/<path:name>')
    def job_manager_edit(self,name):
        return {}

    @expose('job')
    def job(self):
        return {}

    @expose('job/<path:name>')
    def job_view(self,name):
        return {}

    @expose('job/<path:name>/<int:num>')
    def job_view_history(self,name,num):
        return {}

    @expose('api/worker_pipe')
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
