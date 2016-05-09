#coding=utf-8
from uliweb import expose, functions, request, Response
from uliweb.orm import get_model
from uliweb.utils.filedown import filedown
import logging
import json as json_
import os


log = logging.getLogger('linci.artifact')

def linci_artifact_has_permission(perm):
    return bool(functions.has_permission(request.user,perm))

@expose('/linci/artifact')
class Artifact(object):
    def _get_new_index(self):
        LinciArtifact = get_model("linciartifact")
        site = settings.LINCI.artifact_site

        last_arti = LinciArtifact.filter(LinciArtifact.c.asite==site).order_by(LinciArtifact.c.aindex.desc()).one()
        if last_arti:
            nindex = last_arti.aindex +1
        else:
            nindex = 1
        while 1:
            if LinciArtifact.filter(LinciArtifact.c.asite==site,LinciArtifact.c.aindex==nindex).count()==0:
                return nindex
            nindex += 1

    def _get_artifact_item(self):
        id_ = request.values.get("id")
        aid = request.values.get("aid")
        LinciArtifact = get_model("linciartifact")
        if id_:
            item = LinciArtifact.get(int(id_))
        elif aid:
            asite,aindex = aid.split("-")
            item = LinciArtifact.get(LinciArtifact.c.asite==asite,LinciArtifact.c.aindex==int(aindex))
        else:
            item = None
        return item

    #--- api ---
    def api_new(self):
        if not functions.linci_artifact_has_permission("linci_artifact_new"):
            return json({"success":False,"msg":"error: no permission"})
        asite = request.values.get("asite",settings.LINCI.artifact_site)
        aindex = request.values.get("aindex")
        atype = request.values.get("atype","default")
        if not asite:
            return json({"success":False,"msg":"error: parameter 'asite' needed"})
        asite = asite.upper()
        local_site = (asite == settings.LINCI.artifact_site)
        if local_site:
            if aindex:
                return json({"success":False,"msg":"error: local artifact creation don't accept aindex parameter"})
            else:
                aindex = self._get_new_index()
        else:
            if not aindex:
                return json({"success":False,"msg":"error: non-local artifact creation need aindex parameter"})
            try:
                aindex = int(aindex)
            except ValueError as e:
                return json({"success":False,"msg":"error: aindex not integer"})
        if not settings.LINCI_ARTIFACT_TYPE.get(atype):
            return json({"success":False,"msg":"error: bad artifact type %s"%(atype)})

        LinciArtifact = get_model("linciartifact")
        linciartifact = LinciArtifact(asite = asite,aindex = aindex,type = atype)
        ret = linciartifact.save()
        if ret:
            aid = '%s-%s'%(linciartifact.asite,linciartifact.aindex)
            return json({"success":True,"aid":aid,"msg":"new artifact '%s' OK"%(aid)})
        else:
            json({"success":False,"msg":"error: unknown error when create new artifact"})

    def api_list_bootstraptable_data(self):
        if not functions.linci_artifact_has_permission("linci_artifact_read"):
            return json({"total":0, "rows": []})

        if request.data:
            data = json_.loads(request.data)
        else:
            data = {}

        LinciArtifact = get_model("linciartifact")
        l = LinciArtifact.all()

        sort = data.get("sort")
        order = data.get("order")
        limit = data.get("limit")
        offset = data.get("offset")
        if sort:
            sort_key = getattr(LinciArtifact.c,sort)
            if order:
                sort_key = getattr(sort_key,order)()
            l = l.order_by(sort_key)
        if limit:
            l = l.limit(limit)
        if offset:
            l = l.offset(offset)
        return json({"total":l.count(), "rows": [i.to_dict() for i in l]})

    def api_upload(self):
        item = self._get_artifact_item()
        if not item:
            return json({"success":False,"msg":"error: artifact not found"})

        item.add_files(request.files)
        flist_str = ",".join([item.normalize_path(request.files[k].filename) for k in request.files])

        return json({"success":True,"msg":"artifact file uploaded OK: %s"%(flist_str)})

    def api_get(self):
        if not functions.linci_artifact_has_permission("linci_artifact_read"):
            return json({"success":False,"msg":"error: have no permission"})
        item = self._get_artifact_item()
        if not item:
            return json({"success":False,"msg":"error: artifact not found"})

        d = item.to_dict()
        perm_update = functions.linci_artifact_has_permission("linci_artifact_update")
        d["aid"] = "%s-%s"%(d["asite"],d["aindex"])
        tclass = functions.get_linci_artifact_scheme_class(item.type)
        d["type_label"] = tclass.name
        d["action_fix"] = (not item.fixed) and item.ready and perm_update
        d["action_set_ready"] = (not item.ready) and perm_update

        return json({"success":True,"item":d})

    def api_fix(self):
        if not functions.linci_artifact_has_permission("linci_artifact_update"):
            return json({"success":False,"msg":"error: have no permission"})

        item = self._get_artifact_item()
        item.fixed = True
        item.save()

        return json({"success":True,"msg":"artifact fix OK"})

    def api_set_ready(self):
        if not functions.linci_artifact_has_permission("linci_artifact_update"):
            return json({"success":False,"msg":"error: have no permission"})

        item = self._get_artifact_item()
        item.ready = True
        item.save()

        return json({"success":True,"msg":"artifact set ready OK"})

    def api_artifactfile_list_bootstraptable_data(self):
        if not functions.linci_artifact_has_permission("linci_artifact_read"):
            return json({"total":0, "rows": []})

        if request.data:
            data = json_.loads(request.data)
        else:
            data = {}

        LinciArtifactFile = get_model("linciartifactfile")
        l = LinciArtifactFile.all()

        sort = data.get("sort")
        order = data.get("order")
        limit = data.get("limit")
        offset = data.get("offset")
        item_id = data.get("item_id")

        if not item_id:
            return json({"total":0, "rows": []})
        l = l.filter(LinciArtifactFile.c.artifact==item_id)
        if sort:
            sort_key = getattr(LinciArtifactFile.c,sort)
            if order:
                sort_key = getattr(sort_key,order)()
            l = l.order_by(sort_key)
        if limit:
            l = l.limit(limit)
        if offset:
            l = l.offset(offset)
        return json({"total":l.count(), "rows": [i.to_dict() for i in l]})

    def api_artifactfile_download(self):
        if not functions.linci_artifact_has_permission("linci_artifact_read"):
            return json({"success":False,"msg":"have no permission"}, status=403)

        not_found_response = json({"success":False,"msg":"not found"}, status=404)

        id_ = request.values.get("id")
        if not id_:
            return not_found_response

        LinciArtifactFile = get_model("linciartifactfile")
        afile = LinciArtifactFile.get(int(id_))
        if not afile:
            return not_found_response

        real_filename = os.path.join(afile.artifact.get_artifact_dpath(),afile.store_path)
        filename = os.path.basename(afile.path)

        if not os.path.isfile(real_filename):
            return not_found_response

        return filedown(request.environ,filename,cache=False,real_filename=real_filename,action="download")

    #--- web admin ---
    def list(self):
        if not functions.linci_artifact_has_permission("linci_artifact_read"):
            errmsg = "no permission"
        else:
            errmsg = ""
        return {"errmsg":errmsg}

    def view(self):
        item = self._get_artifact_item()
        if item:
            errmsg = ""
            tclass = functions.get_linci_artifact_scheme_class(item.type)
            if tclass:
                view_template = getattr(tclass,"view_template",None)
                if view_template:
                    response.template = view_template
        else:
            errmsg = "artifact not found"
        return {"errmsg":errmsg,"item":item}
