#! /usr/bin/env python
#coding=utf-8

from uliweb import settings
from uliweb.utils.common import import_attr

def get_linci_artifact_scheme_class(type_name):
    class_path = settings.LINCI_ARTIFACT_TYPE.get(type_name,{}).get('scheme_class',"shapps.linci.artifact.Default")
    return import_attr(class_path)

#default artifact type, refer to: settings.LINCI.artifact_type
class Default(object):
    name = "Default"
    #view_template = "Artifact/view.html"
