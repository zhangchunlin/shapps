from uliweb import Middleware

class XForwardedForMiddle(Middleware):
    
    def process_request(self, request):
        if 'HTTP_X_FORWARDED_FOR' in request.environ:
            #http://en.wikipedia.org/wiki/X-Forwarded-For
            client_addr = request.environ['HTTP_X_FORWARDED_FOR'].split(",")[0].strip()
            if client_addr:
                request.environ['REMOTE_ADDR'] = client_addr
