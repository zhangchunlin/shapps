#coding=utf-8
from uliweb.core.SimpleFrame import expose, url_for
from uliweb.contrib.auth.views import login
import urllib


def login():
    from uliweb.contrib.auth import login
    from forms import LoginForm
    
    form = LoginForm()
    
    if request.method == 'GET':
        form.next.data = request.GET.get('next', request.referrer or '/')
        return {'form':form, 'msg':''}
    if request.method == 'POST':
        flag = form.validate(request.params)
        if flag:
            request.session.remember = form.rememberme.data
            login(form.username.data.lower())
            next = urllib.unquote(request.POST.get('next', '/'))
            return redirect(next)
        msg = form.errors.get('_', '') or _('Login failed!')
        return {'form':form, 'msg':str(msg)}
