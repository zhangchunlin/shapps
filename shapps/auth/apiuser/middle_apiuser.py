from uliweb import Middleware, settings, functions
from uliweb.orm import get_model
from weto.session import Session
from uliweb.utils.common import import_attr, application_path

class ApiuserMiddle(Middleware):
    def process_request(self, request):
        user = getattr(request,'user',None)
        if not user:
            key = request.cookies.get(settings.AUTH_APIUSER.TOKEN_NAME)
            if not key:
                key = request.values.get(settings.AUTH_APIUSER.TOKEN_NAME)
            if key:
                session = functions.get_session(key)

                user_id = session.get(settings.AUTH_APIUSER.SESSION_KEY_USER)
                if user_id:
                    User = get_model('user')
                    user = User.get(user_id)
                    if user and settings.AUTH_APIUSER.LOGIN_AUTH_TYPE_RESTRICTED:
                        if user.auth_type!=settings.AUTH.AUTH_TYPE_APIUSER:
                            user = None
                    ip_addr = session.get(settings.AUTH_APIUSER.SESSION_KEY_IP)
                    if user and request.environ['REMOTE_ADDR']!=ip_addr:
                        user = None
                    request.user = user
