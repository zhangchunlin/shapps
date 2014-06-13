#! /usr/bin/env python
#coding=utf-8

from uliweb.core.commands import Command
from uliweb.orm import get_model

class SuperuserListCommand(Command):
    name = 'sulist'
    help = 'Super user list'
    
    def handle(self, options, global_options, *args):
        self.get_application(global_options)
        
        User = get_model("user")
        for user in User.filter(User.c.is_superuser==True):
            print user.id, user.username, user.email

class SuperuserSetCommand(Command):
    name = 'suset'
    help = 'Super user set,usage "uliweb %s USERNAME"'%(name)
    
    def handle(self, options, global_options, *args):
        self.get_application(global_options)
        
        if len(args)>=1:
            username = args[0]
        else:
            print "usage: 'uliweb %s USERNAME'"%(self.name)
            return
        
        User = get_model("user")
        user = User.get(User.c.username == username)
        if user:
            print "%d %s is_superuser=%s"%(user.id,user.username,user.is_superuser),
            user.is_superuser = not (user.is_superuser)
            user.save()
            print "->",
            print "%d %s is_superuser=%s"%(user.id,user.username,user.is_superuser)
        else:
            print "user '%s' not found"%(username)
