#! /usr/bin/env python
#coding=utf-8

from uliweb.core.commands import Command
from optparse import make_option
from uliweb.orm import get_model
import sys

ERR_BAD_PARAM = 1

class UserAddCommand(Command):
    name = 'useradd'
    option_list = (
            make_option('-u', '--username', dest='username'),
    )
    help = 'add user'

    def handle(self, options, global_options, *args):
        from getpass import getpass
        from uliweb.contrib.auth import create_user
        from uliweb import settings

        self.get_application(global_options)

        User = get_model("user")

        if not options.username:
            print >> sys.stderr, "error: username required"
            sys.exit(ERR_BAD_PARAM)
        if User.get(User.c.username==options.username):
            print >> sys.stderr, "error: same username user exists already"
            sys.exit(ERR_BAD_PARAM)

        password = ""
        while (not password):
            password = getpass("input the password:")

        f, d = create_user(username=options.username,
            password=password,
            auth_type=settings.AUTH.AUTH_TYPE_DEFAULT)

        if f:
            print "user '%s' created successfully"%(options.username)
        else:
            print >> sys.stderr, "fail to create user '%s', error: %s"%(options.username,d.get("_",""))
