#coding=utf-8
import os
import time
import mimetypes
import urllib
from datetime import datetime

from uliweb import expose, NotFound, functions, decorators, settings
from uliweb.utils.filedown import FileIterator
from uliweb.utils.common import import_attr
from werkzeug import Response, wrap_file
from werkzeug.http import parse_range_header

#just example,do nothing
def check_permission(func):
    from uliweb.utils.common import wraps
    @wraps(func)
    def _f(*args, **kwargs):
        #do something before
        return func(*args, **kwargs)
    return _f

@decorators.sharedir_check_permission
@expose('/sharedir/<dname>')
def sharedir(dname):
    return {"dname":dname}

@decorators.api_sharedir_listdir_check_permission
@expose('/api/sharedir/listdir/<path:dname>')
def api_sharedir_listdir(dname):
    d = {}
    rpath = urllib.unquote_plus(request.params.get("rpath",""))
    rootpath = os.path.abspath(settings.SHAREDIR.directories.get(dname))
    if not rootpath:
        raise NotFound
    apath = os.path.abspath(os.path.join(rootpath,rpath))
    if not apath.startswith(rootpath):
        raise NotFound
    maxnum = int(request.params.get("maxnum",settings.SHAREDIR.entries_maxnum_default))

    def myquote(path):
        if isinstance(path,unicode):
            path = path.encode("utf8")
        return urllib.quote_plus(path)

    def get_rpathlist():
        dname2 = dname
        rpath2 = ""
        rpathlist = [{"name":dname2,"rpath":rpath2}]
        for dname3 in rpath.split(os.sep):
            if dname3:
                d={}
                d["name"]=dname3
                rpath2 = os.path.join(rpath2,dname3)
                d["rpath"]=myquote(rpath2)
                rpathlist.append(d)
        return rpathlist

    def get_entries():
        rlist = []
        if apath.startswith(rootpath):
            try:
                for entry in os.listdir(apath):
                    d = {}
                    d["name"]=entry
                    ep = os.path.join(apath,entry)
                    st = os.stat(ep)
                    d["isdir"]=os.path.isdir(ep)
                    relpath = os.path.relpath(ep,rootpath)
                    if d["isdir"]:
                        esize = ""
                        d["rpath"]=myquote(relpath)
                    else:
                        esize = st.st_size
                        d["rpath"]=relpath
                    d["mtime"] = time.strftime("%Y-%m-%d %H:%M:%S",time.localtime(st.st_mtime))
                    d["size"]=esize
                    rlist.append(d)
            except OSError as e:
                pass
        def mycmp(x,y):
            c = - cmp(x["isdir"],y["isdir"])
            if c==0:
                c = - cmp(x["mtime"],y["mtime"])
            return c
        return sorted(rlist,mycmp)
    entries = get_entries()
    d['entries'] = entries[:maxnum]
    d['entries_full'] = len(d['entries'])==len(entries) or len(d['entries'])>=settings.SHAREDIR.entries_maxnum_full
    d['rpathlist'] = get_rpathlist()
    return json(d)

@decorators.sharedir_download_check_permission
@expose('/sharedir_download/<dname>/<path:rpath>')
def sharedir_download(dname,rpath):
    rootpath = os.path.abspath(settings.SHAREDIR.directories.get(dname))
    if not rootpath:
        raise NotFound
    apath = os.path.abspath(os.path.join(rootpath,rpath))
    if (not apath.startswith(rootpath)) or (not os.path.isfile(apath)):
        raise NotFound

    def _opener(filename):
        return (
            open(filename, 'rb'),
            datetime.utcfromtimestamp(os.path.getmtime(filename)),
            int(os.path.getsize(filename))
        )

    guessed_type = mimetypes.guess_type(apath)
    mime_type = guessed_type[0] or 'application/octet-stream'

    headers = []
    headers.append(('Content-Type', mime_type))

    if request.range:
        range = request.range
    else:
        range = parse_range_header(request.environ.get('HTTP_RANGE'))
    #when request range,only recognize "bytes" as range units
    if range and range.units=="bytes":
        rbegin,rend = range.ranges[0]
        try:
            fsize = os.path.getsize(apath)
        except OSError as e:
            return Response("Not found",status=404)
        if (rbegin+1)<fsize:
            if rend == None:
                rend = fsize-1
            headers.append(('Content-Length',str(rend-rbegin+1)))
            headers.append(('Content-Range','%s %d-%d/%d' %(range.units,rbegin, rend, fsize)))
            return Response(FileIterator(apath,rbegin,rend),
                status=206, headers=headers, direct_passthrough=True)

    f, mtime, file_size = _opener(apath)

    return Response(wrap_file(request.environ, f), status=200, headers=headers,
        direct_passthrough=True)
