#! /usr/bin/env python
#coding=utf-8

from uliweb import settings
from uliweb.orm import get_model
from sqlalchemy.sql import and_
from uliweb.utils.common import safe_str


def dbinit():
    RbacOrg = get_model('rbacorg')
    RbacScheme = get_model('rbacscheme')
    Role = get_model('role')
    Perm = get_model('permission')
    User = get_model('user')
    UserGroup = get_model('usergroup')
    OrgRole = get_model('orgrole')
    Rel = get_model('role_perm_rel')

    for k,v in settings.get('RBACSCHEME', {}).items():
        scheme_name,gorg_name,rp_list = v
        if not gorg_name:
            gorg_name = "%s_gorg"%(scheme_name)
        gorg = RbacOrg.get(RbacOrg.c.name==gorg_name)
        if not gorg:
            print "Add gorg(%s) of RbacScheme(%s)"%(gorg_name, scheme_name)
            gorg = RbacOrg(name=gorg_name)
            flag = gorg.save(); assert(flag)
        rbacscheme = RbacScheme.get(RbacScheme.c.name==scheme_name)
        if not rbacscheme:
            print "Add RbacScheme(%s)"%(scheme_name)
            rbacscheme = RbacScheme(name=scheme_name,gorg=gorg)
            flag = rbacscheme.save(); assert(flag)
        for role_name,perm_name in rp_list:
            role = Role.get(Role.c.name==role_name)
            if not role:
                print "Add Role(%s)"%(role_name)
                role = Role(name=safe_str(role_name))
                flag = role.save(); assert(flag)
            perm = Perm.get(Perm.c.name==perm_name)
            if not perm:
                print "Add Permission(%s)"%(perm_name)
                perm = Perm(name=safe_str(perm_name))
                flag = perm.save(); assert(flag)
            rel = Rel.get(and_(Rel.c.role==role.id,
                Rel.c.permission==perm.id,
                Rel.c.scheme==rbacscheme.id))
            if not rel:
                print "Add Role_Perm_Rel(%s,%s,%s)"%(role_name,perm_name,scheme_name)
                rel = Rel(role=role,permission=perm,scheme=rbacscheme)
                flag = rel.save(); assert(flag)

    for k,v in settings.get('RBACORG', {}).items():
        rbacorg_name,rbacscheme_name = v
        rbacscheme = RbacScheme.get(RbacScheme.c.name==scheme_name)
        if not rbacscheme:
            raise Exception, 'RbacScheme [%s] not found.' % rbacscheme
        rbacorg = RbacOrg.get(RbacOrg.c.name==rbacorg_name)
        if not rbacorg:
            print "Add RbacOrg(%s,%s)"%(rbacorg_name, rbacscheme_name)
            rbacorg = RbacOrg(name=rbacorg_name,rbacscheme=rbacscheme)
            flag = rbacorg.save(); assert(flag)
        elif (not rbacorg.rbacscheme) or (rbacorg.rbacscheme.id!=rbacscheme.id):
            print "Update RbacOrg[%s]'s scheme to %s"%(rbacorg_name,rbacscheme_name)
            rbacorg.update(rbacscheme=rbacscheme)
            rbacorg.save()

    for k,v in settings.get('ORGROLE').items():
        role_name, rbacorg_name, usernames, usergroupnames = v
        role = Role.get(Role.c.name==role_name)
        if not role:
            raise Exception, 'Role [%s] not found.' % role_name
        rbacorg = RbacOrg.get(RbacOrg.c.name==rbacorg_name)
        if not rbacorg:
            raise Exception, 'RbacOrg [%s] not found.' % rbacorg_name
        orgrole = OrgRole.get(and_(OrgRole.c.role==role.id,
            OrgRole.c.organization==rbacorg.id))
        if not orgrole:
            print "Add OrgRole(%s,%s)"%(role_name, rbacorg_name)
            orgrole = OrgRole(role=role,organization=rbacorg)
            flag = orgrole.save(); assert(flag)
        for username in usernames:
            user = User.get(User.c.username==username)
            if user:
                if not orgrole.users.has(user):
                    print "Add User(%s) to OrgRole(%s,%s)"%(username, role_name, rbacorg_name)
                    orgrole.users.add(user)
        for usergroupname in usergroupnames:
            usergroup = UserGroup.get(UserGroup.c.name==usergroupname)
            if usergroup:
                if not orgrole.usergroups.has(usergroup):
                    print "Add UserGroup(%s) to OrgRole(%s,%s)"%(usergroupname, role_name, rbacorg_name)
                    orgrole.usergroups.add(usergroup)

dbinit()
