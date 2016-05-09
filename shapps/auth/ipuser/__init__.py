#! /usr/bin/env python
#coding=utf-8

from uliweb import request, settings
from uliweb.orm import get_model


def authenticate(*args, **kwargs):
    User = get_model('user')
    user = User.filter(User.c.auth_type==settings.AUTH.AUTH_TYPE_IPUSER,
        User.c.username==request.environ['REMOTE_ADDR']).one()
    if user:
        return True, user
    else:
        return False, {}
