#coding=utf-8
from uliweb import expose, functions
from uliweb.i18n import ugettext_lazy as _
import json as json_

@expose('/ipuser_admin')
class IpUserAdmin(object):
    def __begin__(self):
        functions.require_login()
        if not request.user.is_superuser:
            error(_('error: superuser role needed!'))

    def list(self):
        return {}

    def api_bootstraptable_data(self):
        if request.data:
            data = json_.loads(request.data)
        else:
            data = {}

        User = functions.get_model("user")
        l = User.filter(User.c.auth_type==settings.AUTH.AUTH_TYPE_IPUSER)

        sort = data.get("sort")
        order = data.get("order")
        limit = data.get("limit")
        offset = data.get("offset")
        if sort:
            sort_key = getattr(User.c,sort)
            if order:
                sort_key = getattr(sort_key,order)()
            l = l.order_by(sort_key)
        if limit:
            l = l.limit(limit)
        if offset:
            l = l.offset(offset)
        return json({"total":l.count(), "rows": [i.to_dict() for i in l]})

    def edit(self):
        errmsg = ""
        User = functions.get_model("user")
        user_id = request.values.get("id")
        if user_id:
            user = User.get(int(user_id))
        else:
            user = None
        if not user:
            errmsg = "User not found"
        return {"errmsg":errmsg,"user":user}

    def add(self):
        errmsg = ""
        return {"errmsg":errmsg}

    def api_add(self):
        ip = request.values.get("ip").strip()
        nickname = request.values.get("nickname").strip()
        if not ip:
            return json({"msg":u"IP address should be filled","success":False})
        if not nickname:
            return json({"msg":u"Nickname should be filled","success":False})
        User = functions.get_model("user")
        if User.get(User.c.username==ip):
            return json({"msg":u"This IP user %s  exists already"%(ip),"success":False})
        user = User(username=ip,nickname=nickname,auth_type=settings.AUTH.AUTH_TYPE_IPUSER)
        ret = user.save()
        if ret:
            return json({"msg":u"Add user %s(%s) OK!"%(ip,nickname),"success":True})
        else:
            return json({"msg":u"Fail to save user!","success":False})

    def api_update(self):
        from sqlalchemy.exc import IntegrityError
        user_id = int(request.values.get("id"))
        ip = request.values.get("ip").strip()
        nickname = request.values.get("nickname").strip()
        if not ip:
            return json({"msg":u"IP address should be filled","success":False})
        if not nickname:
            return json({"msg":u"Nickname should be filled","success":False})
        User = functions.get_model("user")
        user = User.get(user_id)
        if not user:
            return json({"msg":u"This IP user %s not found"%(ip),"success":False})
        user.update(username=ip,nickname=nickname)
        try:
            ret = user.save()
        except IntegrityError as e:
            return json({"msg":u"There is already another IP user(%s)"%(ip),"success":False})
        if ret:
            return json({"msg":u"Update user %s(%s) OK!"%(ip,nickname),"success":True})
        else:
            return json({"msg":u"Fail to save user %s, maybe not modified"%(ip),"success":False})

    def api_remove(self):
        user_id = int(request.values.get("id"))
        User = functions.get_model("user")
        user = User.get(user_id)
        if not user:
            return json({"msg":u"This IP user %s not found"%(ip),"success":False})

        user.delete()
        return json({"msg":u"Remove user %s(%s) OK!"%(user.username,user.nickname),"success":True})
