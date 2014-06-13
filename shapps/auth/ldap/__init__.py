#! /usr/bin/env python
#coding=utf-8

from uliweb import settings
from uliweb.orm import get_model
from uliweb.i18n import ugettext as _

import logging as _logging
logging = _logging.getLogger('shapps.auth.ldap')

def update_user_groups(user,gnames):
    UserGroup = get_model('usergroup')
    groups = []
    for gname in gnames:
        if not isinstance(gname,unicode):
            decode_ok = False
            for c in [settings.GLOBAL.DEFAULT_ENCODING,"utf8"]:
                try:
                    gname = gname.decode(c)
                    decode_ok = True
                    break
                except UnicodeDecodeError as e:
                    pass
            if not decode_ok:
                gname = repr(gname)
        group = UserGroup.get(UserGroup.c.name==gname)
        if not group:
            group = UserGroup(name=gname)
            group.save()
        groups.append(group)
    user.groups.update(groups)

def authenticate(username, password):
    from ldap_login import ldapauth_handler
    
    if not settings.LDAP.user_case_sensitive:
        username = username.lower()
    
    ldap_auth_ok, ldap_dict = ldapauth_handler.login(**{'username':username,'password':password})
    if not ldap_auth_ok:
        return False,{'password' : _('LDAP error:user does not exist or password is not correct!')}
    
    User = get_model('user')
    user = User.get(User.c.username==username)
    if not user:
        if settings.LDAP.user_auto_create:
            user = User(username=username, password="")
            user.set_password("")
            user.save()
        else:
            return False,{'username': _('User "%s" does not existed!') % username}
    
    class cresult:
        pass
    cresult.changed = False
    
    #update user info
    def update_user_with_ldap_attr(setting_attrname,user_attrname):
        attrname = settings.LDAP.auth.get(setting_attrname,None)
        if attrname:
            attr = ldap_dict.get(attrname,None)
            if attr:
                if type(attr)==type([]):
                    attr = attr[0]
                setattr(user,user_attrname,attr)
                cresult.changed = True
    update_user_with_ldap_attr('aliasname_attribute','nickname')
    update_user_with_ldap_attr('email_attribute','email')
    
    #sync groups
    if settings.LDAP.sync_user_groups:
        attrname = settings.LDAP.auth.get("memberof_attribute",None)
        if attrname:
            memberof = ldap_dict.get(attrname,None)
            if memberof:
                gnames = []
                for i in memberof:
                    try:
                        gname = i.split(",")[0].split("=")[1]
                        gnames.append(gname)
                    except IndexError,e:
                        logging.error("error when handle memberOf( %s ): %s"%(i,e))
                update_user_groups(user,gnames)
    
    if cresult.changed:
        user.save()
    
    return True, user
