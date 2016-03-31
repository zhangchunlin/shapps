#! /usr/bin/env python
#coding=utf-8

from uliweb import settings
from uliweb.utils.common import import_attr

def linci_artifact_types():
    for id,sort_num,type_class in settings.LINCI.artifact_type:
        if type_class:
            type_class = import_attr(type_class)
        else:
            type_class = None
        yield id,sort_num,type_class

def get_linci_artifact_type(type_id):
    if type_id:
        type_id = int(type_id)
    for sid,sort_num,tclass in linci_artifact_types():
        if sid == type_id or type_id == None:
            return sid,sort_num,tclass
    return None, None, None

#default artifact type, refer to: settings.LINCI.artifact_type
class Default(object):
    name = "Default"
    #view_template = "Artifact/view.html"
