#! /usr/bin/env python
#coding=utf-8

from uliweb.orm import get_model
from uliweb import settings

LinciWorker = get_model('linciworker')
LinciManager = get_model('lincimanager')

for worker in settings.LINCI.get('WORKERS', []):
    name = worker["name"]
    lworker = LinciWorker.get(LinciWorker.c.name==name)
    if not lworker:
        print "new worker name: %s"%(name)
        lworker = LinciWorker(name=name)
        lworker.save()

for manager in settings.LINCI.get('MANAGERS', []):
    name = manager["name"]
    workers = manager["workers"]
    lmanager = LinciManager.get(LinciManager.c.name==name)
    if not lmanager:
        lmanager = LinciManager(name=name)
        lmanager.save()
        print "new manager: %s"%(name)
        for worker in workers:
            lworker = LinciWorker.get(LinciWorker.c.name==worker)
            if lworker:
                lmanager.workers.add(lworker)
                print "manager %s workers add %s"%(name,worker)
