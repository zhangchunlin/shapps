#! /usr/bin/env python
#coding=utf-8

from orgrbac import *

def prepare_default_env(sender, env):
    from uliweb import functions

    env['has_org_permission'] = functions.has_org_permission
    env['has_org_role'] = functions.has_org_role
