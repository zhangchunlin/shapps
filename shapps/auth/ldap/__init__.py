#! /usr/bin/env python
#coding=utf-8

def authenticate(username, password):
    from uliweb import settings
    from uliweb.orm import get_model
    from ldap_login import ldapauth_handler
    from uliweb.i18n import ugettext as _
    
    if not settings.LDAP.user_case_sensitive:
        username = username.lower()
    
    ldap_auth_ok = ldapauth_handler.login(**{'username':username,'password':password})
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
    return True, user
