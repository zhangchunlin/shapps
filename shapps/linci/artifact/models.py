#! /usr/bin/env python
#coding=utf-8

from uliweb.orm import *
import logging


log = logging.getLogger('linci.artifact')

class LinciArtifact(Model):
    #artifact id = "%s-%s"%(asite,aindex)
    #artifact site
    asite = Field(str)
    #artifact index
    aindex = Field(int)

    #artifact type
    type = Field(int, default = 1)

    project_id = Field(int, index=True)
    project_name = Field(str)

    #after ready=True, this artifact can be viewed by normal users
    ready = Field(bool, default= False)
    fixed = Field(bool, default= False)
    removed = Field(bool, default= False)

    #create date
    cdate = Field(datetime.datetime, auto_now_add=True)

    @classmethod
    def OnInit(cls):
        Index('aid_index', cls.c.asite, cls.c.aindex, unique=True)

class LinciArtifactProperty(Model):
    artifact = Reference("linciartifact", nullable=False, collection_name='props')
    key = Field(str, index=True)
    str_value = Field(str)
    int_value = Field(int)
    datetime_value = Field(datetime.datetime)

class LinciArtifactFile(Model):
    artifact = Reference("linciartifact", nullable=False, collection_name='files')
    #relative path
    path = Field(str)
    #size in bytes
    size = Field(int)
    md5 = Field(str)
    #upload date
    udate = Field(datetime.datetime, auto_now_add=True)
