from uliweb import Middleware, settings, functions
from uliweb.orm import get_model
from weto.session import Session
from uliweb.utils.common import import_attr, application_path

class LenovoIdMiddle(Middleware):
    def process_request(self, request):
        user = getattr(request, 'user', None)
        if not user:
            key = request.cookies.get(settings.AUTH_LENOVOID.TOKEN_NAME, request.values.get(settings.AUTH_LENOVOID.TOKEN_NAME))
            if key:
                session = functions.get_session(key)
                user_id = session.get(settings.AUTH_LENOVOID.SESSION_KEY_USER)
                if user_id:
                    User = get_model('user')
                    user = User.get(user_id)
                    request.user = user

