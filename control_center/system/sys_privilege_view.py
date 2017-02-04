#-*-coding:utf-8-*-


from flask.views import MethodView
from flask import render_template, current_app, request, url_for
from flask import jsonify, session ,json
from public.function import tools

from data_mode.user_center.model.admin_user import AdminUser
from data_mode.user_center.model.admin_group import AdminGroup
from data_mode.user_center.model.admin_url import AdminUrl
from data_mode.user_center.model.organ_department import OrganDepartMent
from data_mode.user_center.model.organ_position import OrganPosition
from data_mode.user_center.model.admin_user_group import AdminUserGroup
import traceback

from model_data import get_organ_data

from sqlalchemy.exc import IntegrityError
from sqlalchemy import or_, not_, func
from control_center.admin import add_url
from config.service_config.returncode import ServiceCode

class PrivilegeView(MethodView):
    def get(self):
        return tools.en_render_template('system/permissions.html')

class PrivilegeDataView(MethodView):
    def get(self):
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        # redis_obj = Redis(host='127.0.0.1')
        # print 'redis_obj', redis_obj

        if per_page > 60:
            per_page = 60
        return_data = jsonify({ 'code':300 })
        try:
            from data_mode.user_center.control.mixOp import MixUserCenterOp
            db_seesion = MixUserCenterOp().get_seesion()
            total = db_seesion.query(func.count(AdminGroup.id)).scalar() - 1
            start = (page-1)*per_page
            groups = db_seesion.query(AdminGroup).order_by(AdminGroup.id).limit(per_page).offset(start)
            return_data = jsonify({ 'code':100,
                            'groups': [group.to_json(dispaly_users=True, dispaly_urls=True) for group in groups] ,
                            'count': total,
                            'feature_urls': [
                                {u"新建权限组": url_for('sys.account_create_save')}
                                ],
                            })
        except Exception, e:
            print e
        # print 'return_data=',tools.en_return_data(return_data)
        return tools.en_return_data(return_data)

class PrivilegeCreateView(MethodView):
    def get(self):
        return tools.en_render_template('system/permissionsnew.html')

class PrivilegeCreateData(MethodView):
    def get(self):
        return_data = jsonify({ 'code':300 })
        try:
            from data_mode.user_center.control.mixOp import MixUserCenterOp
            db_seesion = MixUserCenterOp().get_seesion()
            # urls = db_seesion.query(AdminUrl).filter( not_(AdminUrl.type == add_url.TYPE_FUNC)).all()
            urls = db_seesion.query(AdminUrl).all()
            return_data = jsonify({
                'code': 100,
                'feature_urls': [
                                {u"保存": url_for('sys.privilege_create')}
                                ],
                'privilege_datas': [url.to_json() for url in urls]
            })
        except Exception, e:
            print e
        # print 'return_data',[url.to_json() for url in urls]
        return tools.en_return_data(return_data)

class PrivilegeCreateSave(MethodView):
    def post(self):
        return_data = jsonify({ 'code':300 })
        from data_mode.user_center.control.mixOp import MixUserCenterOp
        db_seesion = MixUserCenterOp().get_seesion()

        try:
            name  = request.values.get('name', '')
            ids =  request.values.get('ids', '')
            # print '权限ID',ids
            group = AdminGroup(name = name)
            ids =  str(ids).split(',')
            if not len(ids):
                return_data = jsonify({'code':109})
            else:
                urls = db_seesion.query(AdminUrl).filter(AdminUrl.id.in_(ids)).all()
                group.urls = urls
                db_seesion.add(group)
                db_seesion.commit()
                return_data = jsonify({ 'code':100 })
        except IntegrityError, e:
            db_seesion.rollback()
            return_data = jsonify({ 'code':109 })
            print e
        except Exception, e:
            db_seesion.rollback()
            print e
        return tools.en_return_data(return_data)


class EditPrivilegeView(MethodView):
    def get(self):
        return tools.en_render_template('system/permissionsedit.html')

class EditPrivilegeViewData(MethodView):
    def get(self):
        return_data = jsonify({ 'code':300 })
        try:
            from data_mode.user_center.control.mixOp import MixUserCenterOp
            db_seesion = MixUserCenterOp().get_seesion()

            id = request.args.get('group_id',type=int)
            group = db_seesion.query(AdminGroup).filter(AdminGroup.id==id).first()
            urls = db_seesion.query(AdminUrl).filter( not_(AdminUrl.type == add_url.TYPE_FUNC)).all()
            group_url_map = {}
            urls_list = []
            for url in group.urls:
                group_url_map[url.id] = url.name
            for url in urls:
                url_data = url.to_json()
                if group_url_map.has_key(url_data['id']):
                    url_data['statu'] = 1
                else:
                    url_data['statu'] = 0
                urls_list.append(url_data)

            return_data = jsonify({
                'code': 100,
                'feature_urls': [
                                {u"保存编辑权限组": url_for('sys.edit_privilege_save')}
                                ],
                'privilege_datas': urls_list
            })
        except Exception, e:
            print e
        return tools.en_return_data(return_data)

class EditPrivilegeSave(MethodView):
    def post(self):
        return_data = jsonify({ 'code':300 })
        from data_mode.user_center.control.mixOp import MixUserCenterOp
        db_seesion = MixUserCenterOp().get_seesion()
        try:
            id = request.values.get('group_id', '')
            name  = request.values.get('name', '')
            ids =  request.values.get('ids', '')
            group = db_seesion.query(AdminGroup).filter(AdminGroup.id==id).first()
            if len(name):
                group.name = name

            if len(ids):
                sql = "delete from admin_group_url where group_id = %s" % group.id
                db_seesion.execute(sql)
                ids =  str(ids).split(',')
                urls = db_seesion.query(AdminUrl).filter(AdminUrl.id.in_(ids)).all()
                group.urls = urls
            db_seesion.add(group)
            db_seesion.commit()
            return_data = jsonify({ 'code':100 })
        except IntegrityError, e:
            db_seesion.rollback()
            return_data = jsonify({ 'code':109 })
            print e
        except Exception, e:
            db_seesion.rollback()
            print e
        return tools.en_return_data(return_data)



class DeletePrivilege(MethodView):
    def post(self):
        return_data = jsonify({ 'code':300 })
        from data_mode.user_center.control.mixOp import MixUserCenterOp
        db_seesion = MixUserCenterOp().get_seesion()
        try:
            id = request.values.get('group_id', '')
            password = request.values.get('password', '')
            # auth = False
            auth = True
            username = session['user']['username']
            curl_user = db_seesion.query(AdminUser).filter(AdminUser.username == username).first()
            if curl_user is not None and curl_user.verify_password(password):
                auth = True

            if auth:
                group = db_seesion.query(AdminGroup).filter(AdminGroup.id==id).first()
                size = 0
                for item in group.users:
                    size = size + 1
                    break
                if size == 0:
                    sql = "delete from admin_group_url where group_id = %s" % group.id
                    db_seesion.execute(sql)
                    db_seesion.delete(group)
                    db_seesion.commit()
                    return_data = jsonify({ 'code':100, 'msg': '删除成功' })
                else:
                    return_data = jsonify({ 'code':102, 'msg': '请先移除用户'})
            else:
                return_data = jsonify({ 'code':107, 'msg': '删除失败' })
        except IntegrityError, e:
            db_seesion.rollback()
            print e
        except Exception, e:
            db_seesion.rollback()
            print e
        return tools.en_return_data(return_data)


class PowerList(MethodView):
    def get(self):
        return_data = {}
        try:
            pl = request.args.get('pl', 0, int)
            pg = request.args.get('pg', 10, int)
            from data_mode.user_center.control.mixOp import MixUserCenterOp
            db_seesion = MixUserCenterOp().get_seesion()
            # 获取权限列表
            power_list = db_seesion.query(AdminGroup).all()
            power_list = [item.to_json() for item in power_list]
            # 获取用户列表
            user_list = db_seesion.query(AdminUser).all()
            user_list = [item.to_json() for item in user_list]
            i_list = []
            group_id_list = []
            for item in power_list:
                a = {}
                num = 0
                user_name = ''
                for item1 in (user_list):
                    if len(item1['groups']) > 0:
                        if item['id'] == item1['groups'][0]['id']:
                            num = num + 1
                            user_name = ','+item1['name'] + user_name
                            a['group_name'] = item['name']
                            a['group_id'] = item['id']
                            a['user_name'] = user_name
                            a['user_id'] = item1['id']
                            a['num'] = num
                            group_id_list.append(item['id'])
                        else:
                          pass
                    else:
                        a['group_name'] = item['name']
                        a['group_id'] = item['id']
                        a['user_name'] = '-'
                        a['user_id'] = '-'
                        a['num'] = 0

                i_list.append(a)
            start = pl*pg
            end = start + pg
            res_data = []
            for key,item in enumerate(i_list):
                if key >= start and key < end:
                    res_data.append(item)


            return_data = {'code':ServiceCode.success,'data':res_data,'total':len(i_list)}
            return tools.en_return_data(json.dumps(return_data))
        except Exception ,e:
            print traceback.format_exc()
            return_data = {'code':ServiceCode.service_exception,'msg':'服务器错误'}
            return tools.en_return_data(json.dumps(return_data))

# 权限人员详情
class UserDetails(MethodView):
    def get(self):
        return_data = {}
        try:
            group_id = request.args.get('group_id', 0, int)
            pl = request.args.get('pl', 0, int) # 页码
            pg = request.args.get('pg', 10, int)
            pl = pl -1
            if not group_id:
                return_data = {'code':ServiceCode.params_error,'msg':'参数错误'}
                return tools.en_return_data(json.dumps(return_data))
            from data_mode.user_center.control.mixOp import MixUserCenterOp
            db_seesion = MixUserCenterOp().get_seesion()
            res = db_seesion.query(AdminUser).all()
            res = [item.to_json() for item in res]
            data = []
            for item in res:
                if len(item['groups']) > 0:
                    if item['groups'][0]['id'] == group_id:
                        data.append(item)

            start = pl*pg
            end = start + pg
            if len(data) < end:
                end = len(data)
            print 'end=',end,'start=',start
            res_data = []
            if len(data) > 0:
                for key,item in enumerate(data):
                    if key >= start and key < end:
                        j = {}
                        j['ship_name'] = item['department']['name']
                        j['work_number'] = item['work_number']
                        j['user_name'] = item['name']
                        res_data.append(j)
            return_data = {'code':ServiceCode.success,'data':res_data,'total':len(data)}
            return tools.en_return_data(json.dumps(return_data))
        except Exception,e:
            print traceback.format_exc()
            return_data = {'code':ServiceCode.service_exception,'msg':'服务器错误'}
            return tools.en_return_data(json.dumps(return_data))

class PowerDetail(MethodView):
    def get(self):
        return_data = {}
        try:
            group_id = request.args.get('group_id',0,int)
            # group_id = 4
            if not group_id:
                return_data = {'code':ServiceCode.params_error,'msg':'参数错误'}
                return tools.en_return_data(json.dumps(return_data))
            from data_mode.user_center.control.mixOp import MixUserCenterOp
            db_seesion = MixUserCenterOp().get_seesion()
            res = db_seesion.execute('select url_id from admin_group_url where group_id = %d;' % (group_id))

            # print 'data',list(res)
            qx_list = []
            for item in res:
                qx_list.append(item[0])
            data = db_seesion.query(AdminUrl).filter(AdminUrl.id.in_(qx_list)).all()
            data = [item.to_json() for item in data]
            # print 'data',data
            return_data = {'code':ServiceCode.success,'data':data}
            return tools.en_render_template('system/permissionsDetail.html',result = json.dumps(return_data))

        except Exception ,e:
            print traceback.format_exc()
            return_data = {'code':ServiceCode.service_exception,'msg':'服务器错误'}
            return tools.en_return_data(json.dumps(return_data))

class UpdatePowerList(MethodView):
    def get(self):
        return_data = {}
        try:
            group_id = request.args.get('group_id',0,int)
            # group_id = 4
            if not group_id:
                return_data = {'code':ServiceCode.params_error,'msg':'参数错误'}
                return tools.en_return_data(json.dumps(return_data))
            from data_mode.user_center.control.mixOp import MixUserCenterOp
            db_seesion = MixUserCenterOp().get_seesion()
            res = db_seesion.execute('select url_id from admin_group_url where group_id = %d;' % (group_id))
            qx_list = []
            for item in res:
                qx_list.append(item[0])
            # 选中
            data_status_t = db_seesion.query(AdminUrl).filter(AdminUrl.id.in_(qx_list)).all()
            data_status_t = [item.to_json() for item in data_status_t]
            # 没有选中
            data_status_f = db_seesion.query(AdminUrl).filter(AdminUrl.id.notin_(qx_list)).all()
            data_status_f = [item.to_json() for item in data_status_f]

            # 给选中加状态
            data_status_t_s = []
            for item in data_status_t:
                item['status'] = 1
                data_status_t_s.append(item)
            # 没有选中加状态
            data_status_f_s = []
            for item in data_status_f:
                item['status'] = 0
                data_status_f_s.append(item)
            r_data = data_status_f_s + data_status_t_s
            return_data = {'code':ServiceCode.success,'data':r_data}
            return tools.en_return_data(json.dumps(return_data))
        except Exception ,e:
            print traceback.format_exc()
            return_data = {'code':ServiceCode.service_exception,'msg':'服务器错误'}
            return tools.en_return_data(json.dumps(return_data))

class PowerIdList(MethodView):
    def get(self):
        return_data = {}
        try:
            group_id = request.args.get('group_id', 0, int)
            if not group_id:
                return_data = {'code': ServiceCode.params_error, 'msg': '参数错误'}
                return tools.en_return_data(json.dumps(return_data))

        except Exception, e:
            print traceback.format_exc()
            return_data = {"code": ServiceCode.service_exception, 'msg': '服务器错误'}
            return tools.en_return_data(json.dumps(return_data))

from control_center.system import sys, sys_prefix
from control_center.admin import add_url

add_url.add_url(u"操作权限", 'sys.set', add_url.TYPE_ENTRY, sys_prefix,
                sys, '/privilege/', 'privilege', PrivilegeView.as_view('privilege'), 70,methods=['GET'])

add_url.add_url(u"权限管理页面元素", "sys.privilege", add_url.TYPE_FUNC,  sys_prefix,
                sys, '/privilege_data/', 'privilege_data', PrivilegeDataView.as_view('privilege_data'), methods=['GET'])

add_url.add_url(u"新增权限组", "sys.privilege", add_url.TYPE_FEATURE,  sys_prefix,
                sys, '/privilege_create/', 'privilege_create', PrivilegeCreateView.as_view('privilege_create'), methods=['GET'])

add_url.add_url(u"新增权限组页面元素", "sys.privilege_create", add_url.TYPE_FUNC,  sys_prefix,
                sys, '/privilege_create_data/', 'privilege_create_data', PrivilegeCreateData.as_view('privilege_create_data'), methods=['GET'])

add_url.add_url(u"保存新增权限组", "sys.privilege_create", add_url.TYPE_FEATURE,  sys_prefix,
                sys, '/privilege_create_save/', 'privilege_create_save', PrivilegeCreateSave.as_view('privilege_create_save'), methods=['POST'])

add_url.add_url(u"编辑权限组页面", "sys.privilege", add_url.TYPE_FEATURE,  sys_prefix,
                sys, '/edit_privilege/', 'edit_privilege', EditPrivilegeView.as_view('edit_privilege'), methods=['GET'])

add_url.add_url(u"编辑权限组页面元素", "sys.edit_privilege", add_url.TYPE_FUNC,  sys_prefix,
                sys, '/edit_privilege_data/', 'edit_privilege_data', EditPrivilegeViewData.as_view('edit_privilege_data'), methods=['GET'])

add_url.add_url(u"编辑编辑权限组保存", "sys.edit_privilege", add_url.TYPE_FEATURE,  sys_prefix,
                sys, '/edit_privilege_save/', 'edit_privilege_save', EditPrivilegeSave.as_view('edit_privilege_save'), methods=['POST'])

add_url.add_url(u"删除权限组", "sys.privilege", add_url.TYPE_FEATURE,  sys_prefix,
                sys, '/delete_privilege/', 'delete_privilege', DeletePrivilege.as_view('delete_privilege'), methods=['POST'])

add_url.add_url(u"新权限列表", "sys.privilege", add_url.TYPE_FEATURE,  sys_prefix,
                sys, '/new_privilege/', 'PowerList', PowerList.as_view('PowerList'), methods=['POST', 'GET'])


add_url.add_url(u"权限人员详情", "sys.PowerList", add_url.TYPE_FEATURE,  sys_prefix,
                sys, '/user_details/', 'UserDetails', UserDetails.as_view('UserDetails'), methods=['POST', 'GET'])

add_url.add_url(u"权限详情", "sys.PowerList", add_url.TYPE_FEATURE,  sys_prefix,
                sys, '/power_detail/', 'PowerDetail', PowerDetail.as_view('PowerDetail'), methods=['POST', 'GET'])

add_url.add_url(u"编辑权限列表", "sys.PowerList", add_url.TYPE_FEATURE,  sys_prefix,
                sys, '/update_power_list/', 'UpdatePowerList', UpdatePowerList.as_view('UpdatePowerList'), methods=['POST', 'GET'])



if __name__ == '__main__':
    p = UpdatePowerList()
    # p.get()



