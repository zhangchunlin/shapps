from uliweb import Middleware, settings
from uliweb.orm import get_model

class IpuserMiddle(Middleware):
    def process_request(self, request):
        user = getattr(request,'user',None)
        if not user:
            User = get_model('user')
            request.user = User.filter(User.c.auth_type==settings.AUTH.AUTH_TYPE_IPUSER,
                User.c.username==request.environ['REMOTE_ADDR']).one()
