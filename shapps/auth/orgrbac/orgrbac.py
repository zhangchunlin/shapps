#! /usr/bin/env python
#coding=utf-8

from uliweb.orm import get_model
from uliweb.utils.common import import_attr
from uliweb.contrib.rbac.rbac import call_func, __role_funcs__
from sqlalchemy.sql import and_


def has_org_role(user, org, *roles, **kwargs):
    """
    Judge is the user belongs to the role of one orgnization, and if does, then
    return the role object if not then return False. kwargs will be passed to
    role_func.
    """
    Role = get_model('role')
    OrgRole = get_model('orgrole')

    if isinstance(user, (unicode, str)):
        User = get_model('user')
        user = User.get(User.c.username==user)

    if isinstance(org, (unicode, str)):
        RbacOrg = get_model('rbacorg')
        org = RbacOrg.get(RbacOrg.c.name==org)

    gorg = org.rbacscheme.gorg

    for role in roles:
        if isinstance(role, (str, unicode)):
            role = Role.get(Role.c.name==role)
            if not role:
                continue
        name = role.name

        #role function do not judge organization now
        func = __role_funcs__.get(name, None)
        if func:
            if isinstance(func, (unicode, str)):
                func = import_attr(func)

            assert callable(func)

            para = kwargs.copy()
            para['user'] = user
            para['org'] = org
            flag = call_func(func, para)
            if flag:
                return role

        #try org
        orgrole = OrgRole.get(and_(OrgRole.c.role==role.id, OrgRole.c.organization==org.id))
        if orgrole:
            flag = orgrole.users.has(user)
            if flag:
                return orgrole

            flag = orgrole.usergroups_has_user(user)
            if flag:
                return orgrole
        #try gorg
        orgrole = OrgRole.get(and_(OrgRole.c.role==role.id, OrgRole.c.organization==gorg.id))
        if orgrole:
            flag = orgrole.users.has(user)
            if flag:
                return orgrole

            flag = orgrole.usergroups_has_user(user)
            if flag:
                return orgrole
    return False

def has_org_permission(user, org, *permissions, **role_kwargs):
    """
    Judge if an user has organization permission, and if it does return role
    object, and if it doesn't return False. role_kwargs will be passed to role
    functions. With role object, you can use role.relation to get Role_Perm_Rel
    object.
    """
    Role = get_model('role')
    Perm = get_model('permission')
    Role_Perm_Rel = get_model('role_perm_rel')

    if isinstance(user, (unicode, str)):
        User = get_model('user')
        user = User.get(User.c.username==user)

    if isinstance(org, (unicode, str)):
        RbacOrg = get_model('rbacorg')
        org = RbacOrg.get(RbacOrg.c.name==org)

    for name in permissions:
        perm = Perm.get(Perm.c.name==name)
        if not perm:
            continue

        flag = has_org_role(user, org, *list(perm.perm_roles.filter(Role_Perm_Rel.c.scheme==org.rbacscheme.id).with_relation().all()), **role_kwargs)
        if flag:
            return flag

    return False
