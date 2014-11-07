#! /usr/bin/env python
#coding=utf-8

from uliweb.orm import *
from sqlalchemy.sql import and_

class RbacScheme(Model):
    name = Field(str, max_length=128, required=True)
    description = Field(str, max_length=255)
    #scheme scope global organization,to keep global roles and permissions of this scheme
    gorg = Reference('rbacorg', collection_name='gorgscheme', nullable=True)

#override contrib.rbac.models.Role_Perm_Rel
class Role_Perm_Rel(Model):
    role = Reference('role')
    permission = Reference('permission')
    scheme = Reference('rbacscheme', nullable=True)
    props = Field(PICKLE)

    @classmethod
    def OnInit(cls):
        Index('rolepermrel_idx', cls.c.role, cls.c.permission , cls.c.scheme , unique=True)

#override contrib.rbac.models.Permission
class Permission(Model):
    name = Field(str, max_length=80, required=True)
    description = Field(str, max_length=255)
    props = Field(PICKLE)

    def get_users(self,org=None):
        if org:
            OrgRole = get_model("orgrole")
            gorg = org.rbacscheme.gorg

            for role in self.perm_roles.filter(Role_Perm_Rel.c.scheme==org.rbacscheme.id):
                if gorg:
                    orgrole = OrgRole.get(and_(OrgRole.c.organization==gorg,OrgRole.c.role==role))
                    if orgrole:
                        for u in orgrole.users.all():
                            yield u
                orgrole = OrgRole.get(and_(OrgRole.c.organization==org,OrgRole.c.role==role))
                if orgrole:
                    for u in orgrole.users.all():
                        yield u
        else:
            for role in self.perm_roles.filter(Role_Perm_Rel.c.scheme==None):
                for u in role.users.all():
                    yield u

    def get_users_ids(self,org=None):
        if org:
            OrgRole = get_model("orgrole")
            gorg = org.rbacscheme.gorg

            for role in self.perm_roles.filter(Role_Perm_Rel.c.scheme==org.rbacscheme.id):
                if gorg:
                    orgrole = OrgRole.get(and_(OrgRole.c.organization==gorg,OrgRole.c.role==role))
                    if orgrole:
                        for u in orgrole.users.ids():
                            yield u
                orgrole = OrgRole.get(and_(OrgRole.c.organization==org,OrgRole.c.role==role))
                if orgrole:
                    for u in orgrole.users.ids():
                        yield u
        else:
            for role in self.perm_roles.filter(Role_Perm_Rel.c.scheme==None):
                for u in role.users.ids():
                    yield u

    def __unicode__(self):
        return self.name

class RbacOrg(Model):
    name = Field(str, max_length=128, required=True)
    #rbac scheme
    rbacscheme = Reference('rbacscheme',collection_name='orgs', nullable=True)

class OrgRole(Model):
    role = Reference('role', nullable=False)
    organization = Reference('rbacorg', nullable=True)
    users = ManyToMany('user', collection_name='user_orgroles')
    usergroups = ManyToMany('usergroup', collection_name='usergroup_orgroles')

    def usergroups_has_user(self,user):
        for usergroup in list(self.usergroups.all()):
            if usergroup.users.has(user):
                return usergroup
        return False
