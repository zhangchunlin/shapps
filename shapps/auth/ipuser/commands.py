#! /usr/bin/env python
#coding=utf-8

from uliweb.core.commands import Command
from uliweb.orm import get_model
from uliweb import settings
import logging
from optparse import make_option

log = logging.getLogger("ipuser")

class IpuserAdd(Command):
    name = 'ipuseradd'
    option_list = (
        make_option('-n', '--nickname', dest='nickname', help='nickname of ipuser'),
        make_option('--ip', dest='ip', help='ip of ipuser'),
    )
    help = 'add ipuser'

    def handle(self, options, global_options, *args):
        self.get_application(global_options)

        User = get_model("user")
        if not options.ip:
            log.error("need ip address")
            return
        if not options.nickname:
            log.error("need nickname for ipuser")
            return
        log.info("create ipuser, ip: '%s', nickname: '%s'"%(options.ip,options.nickname))
        user = User(username=options.ip,nickname=options.nickname,auth_type=settings.AUTH.AUTH_TYPE_IPUSER)
        ret = user.save()
        if not ret:
            log.error("create fail")
