#! /usr/bin/env python
#coding=utf-8

from uliweb import settings
from uliweb.utils.common import import_attr

def get_linci_artifact_type(type_id):
    v = settings.LINCI.artifact_type[type_id]
    if v:
        sort_num,type_class = v
        if type_class:
            type_class = import_attr(type_class)
        else:
            type_class = None
        return type_id,sort_num,type_class
    else:
        return None, None, None

#default artifact type, refer to: settings.LINCI.artifact_type
class Default(object):
    name = "Default"
    #view_template = "Artifact/view.html"
