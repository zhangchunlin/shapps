# coding=utf-8
from uliweb import expose
from uliweb.orm import get_model, do_, NotFound
from uliweb import request
import logging
from sqlalchemy.sql.expression import select, distinct
from sqlalchemy.orm.util import join
from sqlalchemy.sql.elements import and_
import json as _json
from collections import OrderedDict

mylog = logging.getLogger('orgrbac')

def __begin__():
    from uliweb import functions
    return functions.require_login()

@expose('/admin/orgschema')
class OrgSchema(object):
    def __init__(self):
        self.model = get_model('rbacscheme')

    def __begin__(self):
        if not request.user.is_superuser:
            error('你不是超级用户不能进行这项操作！')

    @expose('')
    def index(self):
        return dict()

    def api_list(self):
        page = int(request.GET.get('iDisplayStart', 0))
        psize = int(request.GET.get('iDisplayLength', 10))
        totalRecords = self.model.count()
        query = select([self.model.c.id, self.model.c.name, self.model.c.gorg, self.model.c.description]).select_from(self.model.table).order_by(self.model.c.id.desc()).offset((page)).limit(psize)
        schemaList = do_(query)
        ret = {}
        ret['aaData'] = [{'id':s['id'], 'name':s['name'], 'description':s['description'], 'gorg':s['gorg']} for s in schemaList]
        ret['iTotalRecords'] = totalRecords
        ret['iTotalDisplayRecords'] = totalRecords
        return json(ret)

    def api_update(self):
        id = request.POST.get('pk')
        value = str(request.POST.get('value')).strip()
        column = int(request.POST.get('column'))
        if column == 2:
            #----update the name about this schema
            #----TODO  check the new name if is exists
            self.model.filter(self.model.c.id == id).update(name=value)
        elif column == 3:
            #----update the description about this schema
            self.model.filter(self.model.c.id == id).update(description=value)
        elif column == 4:
            self.model.filter(self.model.c.id == id).update(gorg=value)
            orgmodel = get_model('rbacorg')
            gorg = orgmodel.get(value)
            value = gorg.name

        return json({"status":"OK", "value":value})

    @expose('api_add')
    def api_add(self):
        name = request.POST.get('name').strip()
        desc = request.POST.get('desc')
        gorg = request.POST.get('gorg')
        #----check name exists
        ret = {}
        ret['status'] = 'OK'
        exists = self.model.filter(self.model.c.name == name).count() > 0
        if exists:
            ret['status'] = 'ERR'
            ret['msg'] = 'name exists'
            return json(ret)
        else:
            orgmodel = get_model('rbacorg')
            model = orgmodel(name=name + '_gorg')
            #----TODO response directly
            flag1 = model.save()
            schemaObj = self.model(name=name, description=desc, gorg=model.id)
            flag2 = schemaObj.save()
            if not flag1 or not flag2:
                ret['status'] = 'ERR'
                ret['msg'] = 'add schema error'
            return json(ret)

    @expose('delete')
    def api_delete(self):
        id = int(request.POST.get('id'))
        model = self.model.get(id)
        orgmodel = get_model('rbacorg')
        Rel = get_model('role_perm_rel')
        model.delete()
        Rel.filter(Rel.c.scheme == id).remove()
        try:
            if model.gorg is not None:
                orgmodel.filter(orgmodel.c.id == model.gorg.id).remove()
        except NotFound as e:
            mylog.error('schema related global organization not found')

        return json({'status':'OK'})

    @expose('detail/<schema_id>')
    def detail(self, schema_id):
        OrgModel = get_model('rbacorg')
        RoleModel = get_model('role')
        PermModel = get_model('Permission')
        RPRModel = get_model('Role_Perm_Rel')

        query = select([self.model.c.id, self.model.c.name, self.model.c.gorg, self.model.c.description, OrgModel.c.name.label('org_name')]).select_from(join(self.model.table, OrgModel.table, self.model.c.gorg == OrgModel.c.id)).where(self.model.c.id == schema_id)
        schemaList = do_(query)
        return {'schemaid':schema_id, 'schema_obj':schemaList.fetchone()}

    @expose('api_load_schema_org/<schema_id>')
    def api_load_schema_org(self, schema_id):
        page = int(request.GET.get('iDisplayStart') or 0)
        psize = int(request.GET.get('iDisplayLength') or 10)
        ret = {}
        OrgModel = get_model('rbacorg')
        totalRecords = OrgModel.filter(OrgModel.c.rbacscheme == schema_id).count()
        orgList = OrgModel.filter(OrgModel.c.rbacscheme == schema_id).offset((page)).limit(psize).all()
        ret['aaData'] = [{'name':s.name, 'rbacscheme':s.rbacscheme} for s in orgList]
        ret['iTotalRecords'] = totalRecords
        ret['iTotalDisplayRecords'] = totalRecords
        return json(ret)

    @expose('api_loadrole')
    def api_loadrole(self):
        ret = {}
        selected = str(request.GET.get('selected'))
        selectedRoleList = _json.loads(selected)
        RoleModel = get_model('role')
        roleList = list(RoleModel.all())
        for role in roleList:
            if role.id in selectedRoleList:
                ret["%s_selected" % role.id] = role.name
            else:
                ret[str(role.id)] = role.name
        return json(ret)

    @expose('schema_permission/<schema_id>')
    def schema_permission(self, schema_id):
        schemaObj = self.model.get(schema_id)
        RoleModel = get_model('role')
        PermModel = get_model('Permission')
        RPRModel = get_model('Role_Perm_Rel')
        roleList = list(RoleModel.all())
        roleDict = {}
        for s in roleList:
            roleDict[s.id] = s.name
        permList = list(PermModel.all())
        permDict = {}
        for s in permList:
            permDict[s.id] = s.name

        return {'schemaid':schema_id, 'schemaname':schemaObj.name, 'roleDict':roleDict, 'permDict':permDict}

    @expose('api_schema_perm_load/<schema_id>')
    def api_schema_perm_load(self, schema_id):
        page = int(request.GET.get('iDisplayStart') or 0)
        psize = int(request.GET.get('iDisplayLength') or 10)
        RoleModel = get_model('role')
        PermModel = get_model('Permission')
        RPRModel = get_model('Role_Perm_Rel')

        perm_rpr = select([PermModel.c.id.label('perm_id'), PermModel.c.name.label('perm_name'), RPRModel.c.scheme, RPRModel.c.role ]).select_from(join(PermModel.table, RPRModel.table, PermModel.c.id == RPRModel.c.permission)).alias()
        query = select([perm_rpr.c.perm_id, perm_rpr.c.perm_name, perm_rpr.c.scheme, RoleModel.c.id.label('role_id'), RoleModel.c.name.label('role_name') ]).select_from(join(perm_rpr, RoleModel.table, RoleModel.c.id == perm_rpr.c.role)).where(perm_rpr.c.scheme == schema_id)  # .offset((page)).limit(psize)
        result = do_(query)
        ret = {}
        #----prepare dataset and do the pagnization in memery
        dataset = {}
        permDict = {}
        for s in result:
            if s['perm_name'] in dataset.keys():
                t = dataset.get(s['perm_name'])
                t.append({s['role_id']:s['role_name']})
            else:
                dataset[s['perm_name']] = [{s['role_id']:s['role_name']}]
                permDict[s['perm_name']] = s['perm_id']

        def fetch_role_id(rols):
            ret = []
            for s in rols:
                for k in s:
                    ret.append(k)
            return ret
        #----pagination in memery
        totalRecords = len(dataset)
        dataset = OrderedDict(sorted(dataset.items(), key=lambda t: t[0]))
        from itertools import islice
        dataset = OrderedDict(islice(dataset.items(), page, psize))
        ret['aaData'] = [{'perm':s, 'roles':dataset[s], 'role_id_list':fetch_role_id(dataset[s]), 'perm_id':permDict[s]} for s in dataset]
        ret['iTotalRecords'] = totalRecords
        ret['iTotalDisplayRecords'] = totalRecords
        return json(ret)

    @expose('api_schema_perm_update')
    def api_schema_perm_update(self):
        value = request.POST.get('value')
        schema = request.POST.get('scheme')
        permid = request.POST.get('permid')
        selectedRoleList = _json.loads(value)
        #----delete the origin role_perm_rel
        RPRModel = get_model('Role_Perm_Rel')
        do_(RPRModel.table.delete().where(and_(RPRModel.c.scheme == schema, RPRModel.c.permission == permid)))
        #----batch add the role_perm_rel
        for s in selectedRoleList:
            roleid = s.split('_')[0]
            RPRModel(role=roleid, permission=permid, scheme=schema).save()

        return json({"status":"OK", "value":value})

    @expose('api_schema_permission_add')
    def api_schema_permission_add(self):
        schemaid = int(request.POST.get('schemaid'))
        permid = int(request.POST.get('permid'))
        roleid = int(request.POST.get('roleid'))
        #----check if exists
        RelModel = get_model('role_perm_rel')
        count = RelModel.filter(and_(RelModel.c.scheme == schemaid, RelModel.c.role == roleid, RelModel.c.permission == permid)).count()
        ret = {}
        ret['status'] = 'OK'
        if count:
            ret['status'] = 'ERR'
            ret['msg'] = '权限已经存在'
        else:
            flag = RelModel(scheme=schemaid, permission=permid, role=roleid).save()
            if not flag:
                ret['status'] = 'ERR'
                ret['msg'] = '添加权限失败,inner error'
        return json(ret)


    @expose('api_schema_permission_delete')
    def api_schema_permission_delete(self):
        schemaid = int(request.POST.get('schemaid'))
        permid = int(request.POST.get('permid'))
        RelModel = get_model('role_perm_rel')
        flag = RelModel.filter(and_(RelModel.c.scheme == schemaid, RelModel.c.permission == permid)).remove()
        ret = {}
        ret['status'] = 'OK'
        if not flag:
            ret['status'] = 'ERR'
            ret['msg'] = '删除权限失败,inner error'

        return json(ret)



@expose('/admin/organization')
class Organization(object):
    def __init__(self):
        self.model = get_model('rbacorg')

    def __begin__(self):
        passList = ['shapps.auth.orgrbac_admin.views.Organization.org_roles', 'shapps.auth.orgrbac_admin.views.Organization.org_roles_load',
                    'shapps.auth.orgrbac_admin.views.Organization.api_loaduser', 'shapps.auth.orgrbac_admin.views.Organization.api_loadusergroup',
                    'shapps.auth.orgrbac_admin.views.Organization.api_loadschema', 'shapps.auth.orgrbac_admin.views.Organization.org_role_add',
                    'shapps.auth.orgrbac_admin.views.Organization.org_role_update', 'shapps.auth.orgrbac_admin.views.Organization.org_role_delete']
        orgRolePermList = ['shapps.auth.orgrbac_admin.views.Organization.org_roles', 'shapps.auth.orgrbac_admin.views.Organization.org_roles_load',
                         'shapps.auth.orgrbac_admin.views.Organization.org_role_add', 'shapps.auth.orgrbac_admin.views.Organization.org_role_update',
                         'shapps.auth.orgrbac_admin.views.Organization.org_role_delete']
        if not request.user.is_superuser:
            if request.rule.endpoint in passList:
                #----check the org role permission
                if request.GET.get('org_id') is not None and not functions.has_org_permission(request.user, request.GET.get('org_id'), 'organization_manage'):
                    error('你没有该组织的handle_organization_role权限，无法进行这项操作！')
            else:
                error('你不是超级用户不能进行这项操作！')

    @expose('')
    def index(self):
        #----prepare the schema list
        SchemaModel = get_model('rbacscheme')
        schemaList = list(SchemaModel.all())
        ret = {}
        for s in schemaList:
            ret[s.id] = s.name
        return dict({'schemaDict':ret})

    @expose('api_list')
    def api_list(self):
        page = int(request.GET.get('iDisplayStart') or 0)
        psize = int(request.GET.get('iDisplayLength') or 10)
        search = request.GET.get('sSearch').strip()
        SchemaModel = get_model('rbacscheme')
        schemaObj = None
        if search:
            schemaObj = SchemaModel.filter(SchemaModel.c.name == search).one()
        if schemaObj:
            totalRecords = self.model.filter(self.model.c.rbacscheme == schemaObj.id).count()
            query = select([self.model.c.id, self.model.c.name, self.model.c.rbacscheme, SchemaModel.c.name.label('schema_name')]).select_from(join(self.model.table, SchemaModel.table, self.model.c.rbacscheme == SchemaModel.c.id)).where(SchemaModel.c.id == schemaObj.id).offset((page)).limit(psize)
        else:
            totalRecords = self.model.filter(self.model.c.rbacscheme != None).count()
            query = select([self.model.c.id, self.model.c.name, self.model.c.rbacscheme, SchemaModel.c.name.label('schema_name')]).select_from(join(self.model.table, SchemaModel.table, self.model.c.rbacscheme == SchemaModel.c.id)).offset((page)).limit(psize)
        orgList = do_(query)
        ret = {}
        ret['aaData'] = [{'id':s['id'], 'name':s['name'], 'schema':s['schema_name'], 'schema_id':s['rbacscheme']} for s in orgList]
        ret['iTotalRecords'] = totalRecords
        ret['iTotalDisplayRecords'] = totalRecords
        return json(ret)

    @expose('api_update')
    def api_update(self):
        id = request.POST.get('pk')
        value = str(request.POST.get('value')).strip()
        column = int(request.POST.get('column'))
        if column == 2:
            self.model.filter(self.model.c.id == id).update(name=value)
        elif column == 3:
            OrgRoleModel = get_model('orgrole')
            OrgRoleList = OrgRoleModel.filter(OrgRoleModel.c.organization == id).all()
            for orgrole in OrgRoleList:
                orgrole.delete()
            self.model.filter(self.model.c.id == id).update(rbacscheme=value)
            schemamodel = get_model('rbacscheme')
            schema = schemamodel.get(value)
            value = schema.name

        return json({"status":"OK", "value":value})

    @expose('api_loadschema')
    def api_loadschema(self):
        SchemaModel = get_model('rbacscheme')
        schemaList = list(SchemaModel.all())
        ret = {}
        for s in schemaList:
            ret[s.id] = s.name
        return json(ret)

    @expose('api_organization_delete')
    def api_organization_delete(self):
        orgid = int(request.POST.get('orgid'))

        OrgroleModel = get_model('orgrole')
        orgroleList = list(OrgroleModel.filter(OrgroleModel.c.organization == orgid).all())
        for orgrole in orgroleList:
            orgrole.delete()
        flag = self.model.filter(self.model.c.id == orgid).remove()
        ret = {}
        ret['status'] = 'OK'
        if not flag:
            ret['status'] = 'ERR'
            ret['msg'] = '删除组织失败,inner error'
        return json(ret)

    @expose('api_organization_add')
    def api_organization_add(self):
        name = request.POST.get('name').strip()
        schemaid = request.POST.get('schemaid')
        ret = {}
        ret['status'] = 'OK'
        count = self.model.filter(self.model.c.name == name).count()
        if not count:
            if schemaid:
                self.model(name=name, rbacscheme=int(schemaid)).save()
            else:
                self.model(name=name).save()
        else:
            ret['status'] = 'ERR'
            ret['msg'] = '名称已经存在'
        return json(ret)

    @expose('org_roles/<org_id>')
    def org_roles(self, org_id):
        SchemaModel = get_model('rbacscheme')
        #----check if the organization is a global organization
        Org = self.model.get(org_id)
        RoleModel = get_model('role')
        RPRModel = get_model('Role_Perm_Rel')
        if Org.rbacscheme:
            query = select([self.model.c.id, self.model.c.name, self.model.c.rbacscheme, SchemaModel.c.id.label('schema_id'), SchemaModel.c.name.label('schema_name')]).select_from(join(self.model.table, SchemaModel.table, self.model.c.rbacscheme == SchemaModel.c.id)).where(self.model.c.id == org_id)
            OrgObj = do_(query).fetchone()
            query = select([distinct(RoleModel.c.id), RoleModel.c.name]).select_from(join(RoleModel.table, RPRModel.table, RoleModel.c.id == RPRModel.c.role)).where(RPRModel.c.scheme == OrgObj.rbacscheme)
        else:
            #----global organization
            query = select([self.model.c.id, self.model.c.name, self.model.c.rbacscheme, SchemaModel.c.id.label('schema_id'), SchemaModel.c.name.label('schema_name')]).select_from(join(self.model.table, SchemaModel.table, self.model.c.id == SchemaModel.c.gorg)).where(self.model.c.id == org_id)
            OrgObj = do_(query).fetchone()
            query = select([distinct(RoleModel.c.id), RoleModel.c.name]).select_from(join(RoleModel.table, RPRModel.table, RoleModel.c.id == RPRModel.c.role)).where(RPRModel.c.scheme == OrgObj.schema_id)
        #----need to filter the rols which belone to this schema
        roleList = do_(query)
        roleDict = {}
        for s in roleList:
            roleDict[s.id] = s.name
        return {'orgid':org_id, 'orgname':OrgObj.name, 'schemaname':OrgObj.schema_name, 'schema':OrgObj.rbacscheme , 'schema_id':OrgObj.schema_id, 'roleDict':roleDict}

    @expose('api_org_roles_load/<org_id>')
    def api_org_roles_load(self, org_id):
        page = int(request.GET.get('iDisplayStart') or 0)
        psize = int(request.GET.get('iDisplayLength') or 10)
        RoleModel = get_model('role')
        UserModel = get_model('user')
        OrgRoleModel = get_model('orgrole')
        UserGroupModel = get_model('usergroup')

        totalRecords = OrgRoleModel.filter(OrgRoleModel.c.organization == org_id).count()
        query = select([RoleModel.c.id.label('role_id'), RoleModel.c.name.label('role_name'), OrgRoleModel.c.organization, OrgRoleModel.c.id.label('orgrole_id')]).select_from(join(RoleModel.table, OrgRoleModel.table, RoleModel.c.id == OrgRoleModel.c.role)).where(OrgRoleModel.c.organization == org_id).offset(page).limit(psize)
        result = do_(query)
        ret = {}
        def fetch_users(orgrole_id):
            ret = []
            userList = UserModel.filter(OrgRoleModel.users.join_filter(OrgRoleModel.c.id == orgrole_id))
            for s in userList:
                ret.append({s.id:s.username})
            return ret

        def fetch_usergroups(orgrole_id):
            ret = []
            userList = UserGroupModel.filter(OrgRoleModel.usergroups.join_filter(OrgRoleModel.c.id == orgrole_id))
            for s in userList:
                ret.append({s.id:s.name})
            return ret

        ret['aaData'] = [{'role_id':s['role_id'], 'role_name':s['role_name'], 'users':fetch_users(s.orgrole_id), 'usergroups':fetch_usergroups(s.orgrole_id), 'orgrole_id':s['orgrole_id']} for s in result]
        ret['iTotalRecords'] = totalRecords
        ret['iTotalDisplayRecords'] = totalRecords
        return json(ret)

    @expose('api_loaduser')
    def api_loaduser(self):
        ret = {}
        selected = str(request.GET.get('selected'))
        selectedUserList = _json.loads(selected)
        UserModel = get_model('user')
        userList = list(UserModel.all())
        for u in userList:
            if u.id in selectedUserList:
                ret["%s_selected" % u.id] = u.username
            else:
                ret[str(u.id)] = u.username
        return json(ret)

    @expose('api_loadusergroup')
    def api_loadusergroup(self):
        ret = {}
        selected = str(request.GET.get('selected'))
        selectedList = _json.loads(selected)
        UserGroupModel = get_model('usergroup')
        usergroupList = list(UserGroupModel.all())
        for u in usergroupList:
            if u.id in selectedList:
                ret["%s_selected" % u.id] = u.name
            else:
                ret[str(u.id)] = u.name
        return json(ret)

    @expose('api_org_role_add')
    def api_org_role_add(self):
        orgid = int(request.POST.get('orgid'))
        roleid = int(request.POST.get('roleid'))
        #----check if exists
        OrgroleModel = get_model('orgrole')
        count = OrgroleModel.filter(and_(OrgroleModel.c.role == roleid, OrgroleModel.c.organization == orgid)).count()
        ret = {}
        ret['status'] = 'OK'
        if count:
            ret['status'] = 'ERR'
            ret['msg'] = '组织角色已经存在'
        else:
            flag = OrgroleModel(role=roleid, organization=orgid).save()
            if not flag:
                ret['status'] = 'ERR'
                ret['msg'] = '添加组织角色失败,inner error'
        return json(ret)

    @expose('api_org_role_update')
    def api_org_role_update(self):
        value = request.POST.get('value')
        orgid = request.POST.get('orgid')
        orgroleid = request.POST.get('orgroleid')
        selectedList = [ s.split('_')[0] for s in _json.loads(value)]
        column = int(request.POST.get('column') or 2)
        #----delete the  many to many orgrole_user_users records
        OrgroleModel = get_model('orgrole')
        OrgObj = OrgroleModel.get(orgroleid)
        if column == 2:
            OrgObj.users.clear()
            OrgObj.users.add(selectedList)
        else:
            OrgObj.usergroups.clear()
            OrgObj.usergroups.add(selectedList)
        return json({"status":"OK", "value":value})

    @expose('api_org_role_delete')
    def api_org_role_delete(self):
        orgid = int(request.POST.get('orgid'))
        roleid = int(request.POST.get('roleid'))
        orgroleid = int(request.POST.get('orgroleid'))
        OrgroleModel = get_model('orgrole')
        OrgroleObj = OrgroleModel.get(orgroleid)
        ret = {}
        ret['status'] = 'OK'
        OrgroleObj.delete()
        count = OrgroleModel.filter(and_(OrgroleModel.c.role == roleid, OrgroleModel.c.organization == orgid)).count()
        if count:
            ret['status'] = 'ERR'
            ret['msg'] = '删除组织角色失败'
        return json(ret)



