#! /usr/bin/env python
#coding=utf-8

from uliweb.orm import *
from uliweb import settings
import logging
import os
import time
import json


log = logging.getLogger('linci.artifact')

class LinciArtifact(Model):
    #artifact id = "%s-%s"%(asite,aindex)
    #artifact site
    asite = Field(str)
    #artifact index
    aindex = Field(int)

    #artifact type
    type = Field(str, max_length=20, default='default')

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

    def get_artifact_dpath(self):
        artifact_root_dpath = settings.LINCI.artifact_root_dpath
        num_name = "%03d"%(int(self.aindex/1000))
        dname = "%s-%03d"%(self.asite,self.aindex)
        artifact_dpath = os.path.join(artifact_root_dpath,self.asite,num_name,dname)
        return artifact_dpath

    def _get_artifact_meta_fpath(self):
        return "%s.meta"%(self.get_artifact_dpath())

    def normalize_path(self, p):
        p = p.replace('\\', '/')
        if p.startswith("./"):
            p = p[2:]
        elif p.startswith("/"):
            p = p[1:]
        return p

    def _update_file_list(self, file_list):
        file_list_meta = self.get_meta("file_list",default=[])
        d = {}
        for f in file_list_meta:
            d[f["path"]] = f
        for store_fpath,fpath in file_list:
            if d.has_key(fpath):
                d[fpath] = {
                    "path": fpath,
                    "store_path": store_fpath,
                }
            else:
                finfo = {
                    "path": fpath,
                    "store_path": store_fpath,
                }
                file_list_meta.append(finfo)
                d[fpath] = finfo

        self.set_meta("file_list",file_list_meta)

    def get_meta(self,k=None,default={}):
        try:
            meta_fpath = self._get_artifact_meta_fpath()
            meta = json.load(open(meta_fpath))
        except IOError as e:
            meta = {}
        if k:
            return meta.get(k,default)
        else:
            return meta

    def set_meta(self,k,v):
        meta = self.get_meta()
        meta[k] = v
        if not meta.get("artifact_id"):
            if self.aindex and self.asite:
                meta["artifact_id"] = "%s-%s"%(self.asite,self.aindex)
        meta_fpath = self._get_artifact_meta_fpath()
        json.dump(meta,open(meta_fpath,"w"),indent=2,sort_keys=True)

    def add_files(self,files):
        LinciArtifactFile = get_model("linciartifactfile")
        count = 0
        file_list = []
        for k in files:
            f = files[k]
            store_fpath,fpath = self.add_file(f)
            file_list.append((store_fpath,fpath))
            count += 1
            afile = LinciArtifactFile.filter(LinciArtifactFile.c.artifact==self.id,
                LinciArtifactFile.c.path==fpath).one()
            if afile:
                afile.store_path = store_fpath
                afile.size = -1
                afile.md5 = ""
            else:
                afile = LinciArtifactFile(artifact=self.id,path=fpath,store_path=store_fpath)
            afile.save()
        self._update_file_list(file_list)
        return count

    def add_file(self,fobj):
        from uliweb.utils import files
        artifact_dpath = self.get_artifact_dpath()
        if not os.path.exists(artifact_dpath):
            os.makedirs(artifact_dpath)
            log.info("mkdir %s"%(artifact_dpath))
        fname = "%s"%(int(time.time()*1000000))
        fpath = os.path.join(artifact_dpath,fname)
        files.save_file(fpath,fobj)
        fpath_normalized = self.normalize_path(fobj.filename)
        log.info("store %s in %s"%(repr(fpath_normalized),fpath))
        return fname,fpath_normalized

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
    #real server store relative path
    store_path = Field(str)
    #size in bytes
    size = Field(int,default=-1)
    md5 = Field(str,default="")
    #upload date
    udate = Field(datetime.datetime, auto_now_add=True)
