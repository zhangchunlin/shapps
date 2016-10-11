#! /usr/bin/env python
#coding=utf-8

from uliweb import settings, functions
from uliweb.orm import *
from uliweb.utils.common import get_var
from gevent.queue import Queue
import logging

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

class LinciManager(GobjModel):
    name = Field(str, max_length=40)
    scheme = Field(str, max_length=40)
    workers = ManyToMany('linciworker', collection_name='managers')
    #last job, maybe running or finished
    latest_job = Reference('lincijob')
    status = Field(int, choices=get_var('LINCI/MANAGER_STATUS'),default=1)
    '''
    [
        {
            "type":"",
        }
    ]
    '''
    prop_work_steps = Field(JSON, default=[])
    '''
    [
        {
        }
    ]
    '''
    prop_work_params = Field(JSON, default={})
    #misc properties
    props = Field(JSON, default={})

    def run(self):
        #如果最后一个job还未完成
        #如果当前正在工作那就
        #如果当前出于waiting状态,那么
            #尝试找到一个能够工作的worker
            #如果能找到,那么
                #新建一个job,并将request/param等信息在job里保存好
                #跑job
                #更新worker的当前running job数
        pass

class LinciWorkRequest(Model):
    user = Reference('user')
    manager = Reference('lincimanager')
    done = Field(bool)
    props = Field(JSON, default={})

class LinciWorker(GobjModel):
    name = Field(str, max_length=40)
    user = Reference('user')
    status = Field(int, choices=get_var('LINCI/WORKER_STATUS'),default=1)
    connected = Field(bool)
    '''
    {
    }
    '''
    props = Field(JSON, default={})

    #--non-field--#
    pipe_connected = False
    running_job_num = None
    msg_queue = None
    def get_msg(self,timeout = 10):
        if not self.msg_queue:
            self.msg_queue = Queue()
        return self.msg_queue.get(timeout = timeout)
    def put_msg(self,msg):
        if not self.msg_queue:
            self.msg_queue = Queue()
        self.msg_queue.put(msg)

class LinciJob(GobjModel):
    manager = Reference('lincimanager')
    worker = Reference('linciworker')
    jid = Field(int)
    status = Field(int, choices=get_var('LINCI/JOB_STATUS'))
    result = Field(int, choices=get_var('LINCI/JOB_RESULT'))
    '''
    {
    }
    '''
    props = Field(JSON, default={})

    def run(self):
        #给worker发出work指令
        pass
