#! /usr/bin/env python
#coding=utf-8

class LinciWorkRequest(Model):
    user = Reference('user')
    manager = Reference('lincimanager', collection_name='requests')
    taken = Field(bool, default=False)
    worker = Reference('linciworker', default=None)
    props = Field(JSON, default={})

class LinciWorker(GobjModel):
    name = Field(str, max_length=40)
    user = Reference('user')
    lables = ManyToMany('linciworkerlabel', collection_name='workers')
    max_cojobs_num = Field(int,default=1)
    #idle, working, lost
    status = Field(str, default="idle", max_length=20, index=True)
    connected = Field(bool)
    '''
    {
    }
    '''
    props = Field(JSON, default={})

    #-- non-field --#
    pipe_connected = False
    cojobs_num = None
    msg_queue = None
    def get_msg(self,timeout = 10):
        if not self.msg_queue:
            self.msg_queue = Queue()
        return self.msg_queue.get(timeout = timeout)
    def put_msg(self,msg):
        if not self.msg_queue:
            self.msg_queue = Queue()
        self.msg_queue.put(msg)

    def take_request(self,request,manager):
        LinciJob = models.lincijob
        job = LinciJob(manager=manager.id,
            worker=self.id,
            jid=LinciJob.get_next_jid(manager),
        )
        job.save()
        job.get_gobj().run()

    def get_cojobs_num_available(self):
        if self.cojobs_num==None:
            self.update_cojobs_num()
        return self.max_cojobs_num - self.cojobs_num

    def update_cojobs_num(self):
        LinciJob = models.lincijob
        self.cojobs_num = LinciJob.filter(LinciJob.c.worker==self.id,LinciJob.status=="working").count()

    def run_job(self,job):
        pass

class LinciWorkerLabel(Model):
    label = Field(str, max_length=60)
