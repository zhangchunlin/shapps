#coding=utf-8
from uliweb.form import *
from uliweb.i18n import ugettext as _
from uliweb import request


class LoginForm(Form):
    form_buttons = Submit(value=_('Login'), _class="btn btn-primary")
#    form_title = _('Login')
    
    username = UnicodeField(label=_('Username'), required=True)
    password = PasswordField(label=_('Password'), required=True)
    rememberme = BooleanField(label=_('Remember Me'))
    next = HiddenField()
    
    def form_validate(self,all_data):
        from uliweb.orm import get_model
        from ldap_login import ldapauth_handler
        from uliweb import settings
        
        username = all_data['username']
        if settings.LDAP.user_case_sensitive:
            username = username.lower()
        
        auth_ok = ldapauth_handler.login(**{'username':username,'password':all_data['password']})
        if not auth_ok:
            return {'password' : _('User not exist or password not right!')}

        User = get_model('user')
        user = User.get(User.c.username==username)
        if not user:
            if settings.LDAP.user_auto_create:
                user = User(username=username, password="")
                user.set_password("")
                user.save()
            else:
                return {'username': _('User "%s" is not existed!') % all_data['username']}
