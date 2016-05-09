#coding=utf-8
from uliweb import expose, functions, settings
from weto.session import Session
from uliweb.utils.common import import_attr, application_path

def get_session(key=None):
    options = dict(settings.get('SESSION_STORAGE', {}))
    options['data_dir'] = application_path(options['data_dir'])
    if 'url' not in options:
        _url = (settings.get_var('ORM/CONNECTION', '') or
        settings.get_var('ORM/CONNECTIONS', {}).get('default', {}).get('CONNECTION', ''))
        if _url:
            options['url'] = _url

    #process Session options
    session_storage_type = settings.SESSION.type
    Session.force = settings.SESSION.force

    serial_cls_path = settings.SESSION.serial_cls
    if serial_cls_path:
        serial_cls = import_attr(serial_cls_path)
    else:
        serial_cls = None

    session = Session(key, storage_type=session_storage_type,
        options=options, expiry_time=settings.SESSION.timeout, serial_cls=serial_cls)
    return session

@expose('/apiuser')
class ApiUser(object):
    def api_get_auth(self):
        user = request.user
        if user:
            username = user.username
        else:
            username = None
        return json({"username":username})

    def api_login(self):
        username = request.values.get("username")
        password = request.values.get("password")
        rememberme = request.values.get("rememberme")
        if rememberme:
            rememberme = (rememberme.lower()=="true") or (rememberme=='1')
        if username and password:
            f,d = functions.authenticate(username=username, password=password,auth_type=settings.AUTH.APIUSER_AUTH_DEFAULT_TYPE)
            if f:
                from uliweb.utils.date import now

                user = d
                user.last_login = now()
                user.save()
                request.user = user

                session = functions.get_session()

                session[settings.AUTH_APIUSER.SESSION_KEY_USER] = user.id
                session[settings.AUTH_APIUSER.SESSION_KEY_IP] = request.environ['REMOTE_ADDR']
                if session.deleted:
                    session.delete()
                else:
                    if rememberme:
                        timeout = settings.SESSION.remember_me_timeout
                        session.set_expiry(timeout)
                    else:
                        timeout = settings.SESSION.timeout
                    flag = session.save()
                    return json({"success":True,
                        "msg":"log in successfully",
                        "token_name":settings.AUTH_APIUSER.TOKEN_NAME,
                        "token":session.key,
                        "timeout":timeout,
                        })

        return json({"success":False,"msg":"fail to log in"})

    def api_logout(self):
        user = request.user
        if user:
            key = request.values.get(settings.AUTH_APIUSER.TOKEN_NAME)
            session = functions.get_session(key)
            session.delete()
            request.user = None
            return json({"success":True,"msg":"user logout successfully"})
        else:
            return json({"success":False,"msg":"user not login, if you want to logout you should login first"})
