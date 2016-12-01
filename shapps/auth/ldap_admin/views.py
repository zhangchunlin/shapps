# coding=utf-8
from uliweb import expose, functions, request, response, json
from uliweb.i18n import ugettext_lazy as _
import json as json_
import os
import logging
try:
    import ldap
except ImportError, err:
    logging.error("You need to have python-ldap installed (%s)." % str(err))
    raise

log = logging.getLogger(__name__)


def _get_portrait_image_thumbnail(id, size=50):
    return os.path.join('portraits', str(id) + '.%dx%d' % (size, size) + '.jpg')

@expose('/ldap_admin')
class LdapAdmin(object):
    def __begin__(self):
        functions.require_login()
        if not request.user.is_superuser:
            error(_('error: superuser role needed!'))

    def list(self):
        return{}

    def addbatch(self):
        response.template = 'LdapAdmin/add.html'
        return{}

    def api_get_database_userdata(self):
        if request.data:
            data = json_.loads(request.data)
        else:
            data = {}
        User = functions.get_model("user")
        l = User.filter(User.c.auth_type == settings.AUTH.AUTH_TYPE_LDAP)
        username = data.get("username", "").strip()
        sort = data.get("sort")
        order = data.get("order")
        limit = data.get("limit")
        offset = data.get("offset")
        if username:
            l.filter(User.c.username.like('%%%s%%' % username))
        if sort:
            sort_key = getattr(User.c, sort)
            if order:
                sort_key = getattr(sort_key, order)()
            l = l.order_by(sort_key)
        if limit:
            l = l.limit(limit)
        if offset:
            l = l.offset(offset)
        return json({"total":l.count(), "rows": [i.to_dict() for i in l]})

    def api_get_ladp_userdata(self):
        if request.data:
            data = json_.loads(request.data)
        else:
            data = {}
        rows = []
        User = functions.get_model("user")
        username = data.get("username", "").strip()
        if username:
            try:
                litems = functions.ldap_search_user(username)
                for dn, ldap_dict in litems:
                    if dn is not None:
                        cnt = User.filter(User.c.username == ldap_dict['name']).count()
                        if cnt:
                            ldap_dict["isIn"] = "1";
                        rows.append(ldap_dict);
                        # print "%s:%s" % (ldap_dict['name'], cnt)
            except ldap.INVALID_CREDENTIALS as err:
                return json({"desc":"invalid credentials, please contact administrator"})
            except Exception as err:
                return json(err.message)
        cntall = len(rows)
        # print rows
        return json({"total":cntall, "rows":rows})

    def api_sync_user(self):
        username = request.values.get("username", "").strip()
        errmsg = ""
        if username:
            user = functions.get_user(username)
        else:
            user = None
        if not user:
            errmsg = "User not found"
        return json({"errmsg":errmsg, "user":user})

    def view(self):
        user_id = request.values.get("id", 0).strip()
        User = functions.get_model("user")
        if user_id:
            user = User.get(int(user_id))
            ldapuser = functions.ldap_get_user(username=user.username)
            image = functions.get_filename(_get_portrait_image_thumbnail(user.id))
            if os.path.exists(image):
                image_url = functions.get_href(_get_portrait_image_thumbnail(user.id))
            else:
                image_url = user.get_image_url()
            can_modify = user.id == request.user.id
        else:
            error(_('error: para userid does not exist!'))

        return {"can_modify":can_modify, "image_url":image_url, "user":user.to_dict(), "ldapuser":ldapuser}

    def api_delete(self):
        user_id = request.values.get("id", 0).strip()
        User = functions.get_model("user")
        if user_id:
            user = User.get(int(user_id))
            user.update(deleted=True)
            ret = user.save()
            if ret:
                return json({"msg":u"user deleted!", "success":True})
            else:
                return json({"msg":u"Fail to delete user", "success":False})
        else:
            return json({"msg":u"para userid does not exist!", "success":False})

    def api_restore(self):
        user_id = request.values.get("id", 0).strip()
        User = functions.get_model("user")
        if user_id:
            user = User.get(int(user_id))
            user.update(deleted=False)
            ret = user.save()
            if ret:
                return json({"msg":u"user restore!", "success":True})
            else:
                return json({"msg":u"Fail to restore user", "success":False})
        else:
            return json({"msg":u"para userid does not exist!", "success":False})

    def api_addbatch(self):
        ldapusernames = request.values.get("ldapusers", 0).strip()
        usernames = ldapusernames.split(",")
        succlist = []
        faillist = []
        for name in usernames:
            user = functions.get_user(name)
            if user:
                succlist.append(user.to_dict())
            else:
                faillist.append(name)
        return json({"success":True, "succlist":succlist, "faillist":faillist})

