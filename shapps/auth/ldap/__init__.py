#! /usr/bin/env python
#coding=utf-8

from uliweb import settings
from uliweb.orm import get_model
from uliweb.i18n import ugettext as _
import logging
from ldap_login import ldapauth_handler


class UserNotFoundError(Exception): pass

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

def _sync_ldap_user(username,attr_dict,user_auto_create=None):
    changed = False
    User = get_model('user')
    user = User.get(User.c.username==username)
    if not user:
        if user_auto_create==None:
            user_auto_create = settings.LDAP.user_auto_create
        if user_auto_create:
            user = User(username=username,auth_type=settings.AUTH.AUTH_TYPE_LDAP)
            changed = True
        else:
            raise UserNotFoundError('User "%s" does not existed!'% username)

    #update user attributes
    for k,v in settings.LDAP.server_param.get('user_attributes',{}).items():
        if isinstance(v,dict):
            to_user = v.get('to_user')
            if to_user:
                #k is setting attribute name, to_user is User attribute name
                attr = attr_dict.get(k)
                if attr!=getattr(user,to_user):
                    setattr(user,to_user,attr)
                    changed = True

    #sync user.groups
    if settings.LDAP.sync_user_groups:
        memberof = attr_dict.get('memberof')
        if memberof:
            gnames = []
            for i in memberof:
                try:
                    gname = i.split(",")[0].split("=")[1]
                    gnames.append(gname)
                except IndexError,e:
                    log.error("error when handle memberOf( %s ): %s"%(i,e))
            _update_user_groups(user,gnames)

    if changed:
        user.save()

    return user

def authenticate(username, password):
    """
    ldap authenticate using username/password
    """
    if not settings.LDAP.user_case_sensitive:
        username = username.lower()

    ldap_auth_ok, attr_dict = ldapauth_handler.login(username=username,password=password)

    if not ldap_auth_ok:
        log.error("user '%s' fail to login for ldap"%(username))
        return False,{'password' : _('LDAP error:user does not exist or password is not correct!')}

    try:
        user = _sync_ldap_user(username,attr_dict)
    except UserNotFoundError as err:
        log.error("user '%s' not found"%(username))
        return False,{'username': _('User "%s" does not existed!') % username}

    log.info("user '%s' login successfully"%(username))
    return True, user

def get_user(user,auto_create=None):
    """
    user can be int(treated as id) or string(treated as username)
    auto_create = True or False or None
        when set to None,will use the value of settings.LDAP.user_auto_create
    """

    if isinstance(user,int):
        User = get_model('user')
        return User.get(user)
    elif isinstance(user,(str,unicode)):
        attr_dict = ldapauth_handler.get_user(username=user)

        if attr_dict:
            try:
                return _sync_ldap_user(user,attr_dict,auto_create)
            except UserNotFoundError as err:
                log.error("user '%s' not found"%(user))

def get_usergroup(usergroup,auto_create=None):
    """
    usergroup can be int(treated as id) or string(treated as groupname)
    auto_create = True or False or None
        when set to None,will use the value of settings.LDAP.group_auto_create
    """
    if isinstance(usergroup,int):
        UserGroup = get_model('usergroup')
        return UserGroup.get(usergroup)
    elif isinstance(usergroup,(str,unicode)):
        attr_dict = ldapauth_handler.get_group(groupname=usergroup)
        if attr_dict:
            groupname = attr_dict.get('name')
            if groupname:
                changed = False

                UserGroup = get_model('usergroup')
                usergroup_obj = UserGroup.get(UserGroup.c.name==groupname)
                if not usergroup_obj:
                    if auto_create==None:
                        auto_create = settings.LDAP.group_auto_create
                    if auto_create:
                        usergroup_obj = UserGroup(name=groupname)
                        changed = True
                        log.info("UserGroup '%s' auto create"%(groupname))

                #update usergroup attributes
                for k,v in settings.LDAP.server_param.get('group_attributes',{}).items():
                    if isinstance(v,dict):
                        to_group = v.get('to_group')
                        if to_group:
                            #k is setting attribute name, to_group is UserGroup attribute name
                            attr = attr_dict.get(k)
                            if attr!=getattr(usergroup_obj,to_group):
                                setattr(usergroup_obj,to_group,attr)
                                changed = True

                if changed:
                    usergroup_obj.save()
                return usergroup_obj

def ldap_get_user(username):
    return ldapauth_handler.get_user(username=username)

def ldap_get_usergroup(groupname):
    return ldapauth_handler.get_group(groupname=groupname)

def ldap_search_user(username):
    return ldapauth_handler.search_user(username=username)

def ldap_search_usergroup(groupname):
    return ldapauth_handler.search_group(groupname=groupname)
