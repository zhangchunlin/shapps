#! /usr/bin/env python
#coding=utf-8

from uliweb import settings
from uliweb.orm import get_model
from uliweb.i18n import ugettext as _
import logging


log = logging.getLogger('shapps.auth.ldap')

def _update_user_groups(user,gnames):
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

class UserNotFoundError(Exception): pass

def _sync_ldap_user(username,ldap_dict,user_auto_create=None):
    User = get_model('user')
    user = User.get(User.c.username==username)
    if not user:
        if user_auto_create==None:
            user_auto_create = settings.LDAP.user_auto_create
        if user_auto_create:
            user = User(username=username)
            user.save()
        else:
            raise UserNotFoundError('User "%s" does not existed!'% username)

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
                        log.error("error when handle memberOf( %s ): %s"%(i,e))
                _update_user_groups(user,gnames)

    if cresult.changed:
        user.save()

    return user

def ldap_get_user(username,auto_create=None):
    """
    auto_create = True or False or None
    when set to None,will use the value of settings.LDAP.user_auto_create
    """
    from ldap_login import ldapauth_handler

    user = None
    ldap_dict = ldapauth_handler.get_user(**{'username':username})

    if ldap_dict:
        try:
            user = _sync_ldap_user(username,ldap_dict,auto_create)
        except UserNotFoundError as err:
            log.error("user '%s' not found"%(username))

    return user

def authenticate(username, password):
    """
    ldap authenticate using username/password
    """
    from ldap_login import ldapauth_handler

    if not settings.LDAP.user_case_sensitive:
        username = username.lower()

    ldap_auth_ok, ldap_dict = ldapauth_handler.login(**{'username':username,'password':password})

    if not ldap_auth_ok:
        log.error("user '%s' fail to login for ldap"%(username))
        return False,{'password' : _('LDAP error:user does not exist or password is not correct!')}

    try:
        user = _sync_ldap_user(username,ldap_dict)
    except UserNotFoundError as err:
        log.error("user '%s' not found"%(username))
        return False,{'username': _('User "%s" does not existed!') % username}

    log.info("user '%s' login successfully"%(username))
    return True, user
