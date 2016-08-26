#coding=utf-8
from uliweb import expose, functions, settings
from weto.session import Session
from uliweb.utils.common import import_attr, application_path
from shapps.auth.lenovoid import authenticate, get_lenovoid_login_url, get_lenovoid_logout_url
import urllib

@expose('/lenovoid')
class Lenovoid(object):
    def api_get_auth(self):
        user = request.user
        if user:
            username = user.username
        else:
            username = None
        return json({"username":username})

    def api_login(self):
        lpsust = request.values.get(settings.AUTH_LENOVOID.LENOVOID_WUST_NAME)
        rememberme = request.values.get("rememberme")
        if rememberme:
            rememberme = (rememberme.lower()=="true") or (rememberme=='1')
        if lpsust:
            f,d = authenticate(lpsust=lpsust)
            if f:
                from uliweb.utils.date import now
                user = d
                user.last_login = now()
                user.save()
                request.user = user
                session = functions.get_session()
                session[settings.AUTH_LENOVOID.SESSION_KEY_USER] = user.id
                if session.deleted:
                    session.delete()
                else:
                    if rememberme:
                        timeout = settings.SESSION.remember_me_timeout
                        session.set_expiry(timeout)
                    else:
                        timeout = settings.SESSION.timeout
                    flag = session.save()
                    return json({
                        settings.AUTH_LENOVOID.TOKEN_NAME: session.key,
                        "timeout":timeout,
                        }
                    )
            else:
                return json({"error_message": d.get("error_message")}, status = d.get("error_code"))

        return json({"error_message":"Fail to log in."}, status = 400)

    def api_logout(self):
        user = request.user
        if user:
            key = request.values.get(settings.AUTH_LENOVOID.TOKEN_NAME)
            session = functions.get_session(key)
            session.delete()
            request.user = None
            return json({"success":True,"msg":"user logout successfully"})
        else:
            return json({"success":False,"msg":"user not login, if you want to logout you should login first"})

    def call_back(self):
        lpsust = request.values.get(settings.AUTH_LENOVOID.LENOVOID_WUST_NAME)
        lenovoid_action = request.values.get("lenovoid.action")
        if lenovoid_action == 'uilogout':
            Redirect("%s/login"%(settings.DOMAINS.default.get('url_prefix')))
        rememberme = request.values.get("rememberme")
        error_message = ""
        if rememberme:
            rememberme = (rememberme.lower()=="true") or (rememberme=='1')
        if lpsust:
            f,d = authenticate(lpsust=lpsust)
            if f:
                from uliweb.contrib.auth import login
                user = d
                request.session.remember = rememberme
                login(user.username)
                next = urllib.unquote(request.GET.get('next', '%s/'%(settings.DOMAINS.default.get('url_prefix'))))
                return redirect(next)
            else:
                error_message = d.get("error_message")
        error_message = error_message if error_message else "Login failed."
        Redirect("%s/login?msg=%s"%(settings.DOMAINS.default.get('url_prefix'), error_message))

@expose('/login')
def login():
    return {
        "lenovoid_login_url": get_lenovoid_login_url(),
        "msg": request.GET.get("msg"),
        "lenovoid_url": settings.AUTH_LENOVOID.BASE_URL
    }

@expose('/logout')
def logout():
    from uliweb.contrib.auth import logout as out
    out()
    Redirect(get_lenovoid_logout_url())
