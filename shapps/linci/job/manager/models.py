#! /usr/bin/env python
#coding=utf-8

from uliweb import settings, functions, models
from uliweb.orm import *
from uliweb.utils.common import get_var
from gevent.queue import Queue
import logging
from sys import maxint

log = logging.getLogger('linci')

_gobj_cache = {}

class GobjModel(Model):
    def get_gobj(self):
        gobj_id = "_%s_%s"%(self.__class__.__name__,self.id)
        gobj = _gobj_cache.get(gobj_id)
        if not gobj:
            _gobj_cache[gobj_id] = self
            gobj = self
        return gobj

class LinciStepsInitError(Exception): pass

class LinciManager(GobjModel):
    name = Field(str, max_length=40, unique=True)
    scheme = Field(str, max_length=40)
    labels = Field(str, max_length=200)
    #last job, maybe running or finished
    latest_job = Reference('lincijob', max_length=20)
    #idle, waiting, working
    status = Field(str, default="idle")
    '''
    [
        {
            "type":"",
        }
    ]
    '''
    prop_work_steps = Field(JSON, default=[])
    #misc properties
    props = Field(JSON, default={})

    def init_work_steps(self,step_num):
        if len(self.prop_work_steps)!=step_num:
            self.prop_work_steps = [{}]*step_num
            self.save()
        else:
            raise LinciStepsInitError("the steps number already same, init already?")

    def update_work_step(self,index,step):
        self.prop_work_steps[index] = step
        self.save()

    def run(self):
        LinciWorkRequest = models.linciworkrequest
        running = bool(self.latest_job and self.latest_job.is_running())
        log.info("trigger to run job %s(%d), last job running: %s"%(repr(self.name),self.id,running))
        #如果当前没有job在运行,那么应该看看有没有需要处理的请求可以处理
        if not running:
            wr = self.requests.order_by(LinciWorkRequest.c.id.desc()).one()
            if wr and not wr.taken:
                #有需要处理的request,需要先去看看是否有worker可用
                worker = self.get_one_worker()
                log.info("find a worker, result: %s"%(worker))
                if worker:
                    worker = worker.get_gobj()
                    #worker拿走request去处理
                    worker.take_request(wr,self)
                    return worker

    def get_one_worker(self):
        LinciWorker = models.linciworker
        idle_worker = self.workers.filter(LinciWorker.c.status=="idle").one()
        if idle_worker:
            return idle_worker

        #如果找不到idle的,那么遍历working状态的worker,找一个还有工位而且job数最小的
        working_worker = None
        min_jobs_num = maxint
        for worker in self.workers.filter(LinciWorker.c.status=="working"):
            w = worker.get_gobj()
            num_ava = w.get_cojobs_num_available()
            if num_ava>0:
                if w.cojobs_num < min_jobs_num:
                    min_jobs_num = w.cojobs_num
                    working_worker = w
        return working_worker

class LinciJob(GobjModel):
    manager = Reference('lincimanager')
    worker = Reference('linciworker')
    jid = Field(int)
    #initial, waiting, working, finished
    status = Field(str, default="initial", max_length=20)
    #unknown, success, fail, exception
    result = Field(str, default="unknown", max_length=20)
    '''
    {
    }
    '''
    props = Field(JSON, default={})

    def run(self):
        #如果是处于初始状态,那么开始
        if self.status == "initial":
            w = self.worker.get_gobj()
            w.run_job(self)

    def is_running(self):
        return self.status=="working"

    @classmethod
    def get_next_jid(cls,manager):
        if manager.last_job:
            return manager.last_job.jid + 1
        return 1
