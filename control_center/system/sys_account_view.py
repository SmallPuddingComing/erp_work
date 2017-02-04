#-*-coding:utf-8-*-

from datetime import datetime
from flask.views import MethodView
from flask import render_template, current_app, request, url_for
from flask import jsonify, session
from public.function import tools


from data_mode.user_center.model.organ_position import OrganPosition

from data_mode.user_center.model.admin_user import AdminUser
from data_mode.user_center.model.admin_group import AdminGroup


from sqlalchemy import func


from model_data import get_organ_data
from sqlalchemy import or_, not_
from sqlalchemy.exc import IntegrityError
import traceback



class AccountView(MethodView):
    def get(self):
        #return "ok"
        return tools.en_render_template('system/account.html')

class AccountDataView(MethodView):
    def get(self):
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        if per_page > 60:
            per_page = 60
        return_data = jsonify({ 'code':300 })
        try:
            from data_mode.user_center.control.mixOp import MixUserCenterOp
            db_seesion = MixUserCenterOp().get_seesion()
            #total = db_seesion.query(func.count(AdminUser.id)).scalar() - 1
            total = db_seesion.query(func.count(AdminUser.id)).filter(not_(AdminUser.is_superuser==1), AdminUser.is_active == 1).scalar()
            start = (page-1)*per_page
            users = db_seesion.query(AdminUser).filter( not_(AdminUser.is_superuser == 1), AdminUser.is_active == 1).order_by(AdminUser.id).limit(per_page).offset(start)
            return_data = jsonify({ 'code':100,
                            'users': [user.to_json() for user in users],
                            'feature_urls': [
                                {
                                    u'新建员工': url_for('sys.account_create')
                                }
                            ],
                            'count': total
                          })
        except Exception, e:
            traceback.format_exc()
            print e
        return tools.en_return_data(return_data)

class AccountCreateView(MethodView):
    def get(self):
        #return "create user"
        return tools.en_render_template('system/addUser.html')

class AccountCreateData(MethodView):
    def get(self):
        return_data = jsonify({ 'code':300 })
        try:
            # groups = AdminGroup.query.order_by(AdminGroup.id)
            # parttime_positions = OrganPosition.query.order_by(OrganPosition.id)
            from data_mode.user_center.control.mixOp import MixUserCenterOp
            db_seesion = MixUserCenterOp().get_seesion()
            groups = db_seesion.query(AdminGroup).order_by(AdminGroup.id)
            parttime_positions = db_seesion.query(OrganPosition).order_by(OrganPosition.id)
            return_data = jsonify({
                'code': 100,
                'feature_urls': [
                                {u"保存": url_for('sys.account_create_save')}
                                ],
                'companys_datas': get_organ_data(disable_users=True),
                'groups_datas': [group.to_json() for group in groups],
                'parttime_positions': [parttime_position.to_fullname_json() for parttime_position in parttime_positions]
            })
        except Exception, e:
            print traceback.format_exc()
        return tools.en_return_data(return_data)

class AccountCreateSave(MethodView):
    def post(self):
        return_data = jsonify({ 'code':300 })
        from data_mode.user_center.control.mixOp import MixUserCenterOp
        mix_op = MixUserCenterOp()
        db_seesion = mix_op.get_seesion()
        try:
            #print type(request.values)
            username = request.values.get('username', '')
            name = request.values.get('name', '')
            email = request.values.get('email', '')
            password = request.values.get('password', '')
            work_number = request.values.get('work_number', '')
            gander = request.values.get('gander', '')
            telephone = request.values.get('telephone', '')
            entry_time = request.values.get('entry_time', '')
            entry_time = datetime.strptime(entry_time, "%Y-%m-%d %H:%M:%S").date()
            position_id = request.values.get('position_id', '')
            group_ids = request.values.get('group_ids', '')
            parttime_positions_ids = request.values.get('parttime_positions_ids', '')
            user = AdminUser(email=email,password=password, username=username, name=name,
                             work_number=work_number, gander=gander, telephone=telephone,
                            entry_time=entry_time, position_id=position_id )
            ids =  group_ids.split(',')

            groups = db_seesion.query(AdminGroup).filter(AdminGroup.id.in_(ids)).all()
            user.groups = groups

            p_p_ids = parttime_positions_ids.split(',')
            parttime_positions = db_seesion.query(OrganPosition).filter(OrganPosition.id.in_(p_p_ids)).all()
            user.parttime_positions = parttime_positions

            db_seesion.add(user)
            db_seesion.commit()
            mix_op.AddUserCallback(user.id)
            return_data = jsonify({ 'code':100 })

        except IntegrityError, e:
            db_seesion.rollback()
            return_data = jsonify({ 'code':109 })
            print e
        except Exception, e:
            db_seesion.rollback()
            print e
        return tools.en_return_data(return_data)

class PersonalAcconutView(MethodView):
    def get(self):
        id = request.args.get('id')

        return tools.en_render_template('system/check-user.html', edit_id = id )

class PersonalAcconut(MethodView):
    def get(self):
        return_data = jsonify({ 'code':300 })
        try:
            id = request.args.get('id',type=int)

            from data_mode.user_center.control.mixOp import MixUserCenterOp
            db_seesion = MixUserCenterOp().get_seesion()
            user = db_seesion.query(AdminUser).filter(AdminUser.id==id).first()

            return_data = jsonify({ 'code':100,
                                    'userinfo': user.to_json()
                                    })
        except Exception, e:
            print e
        return tools.en_return_data(return_data)

class EditPersonalAcconutView(MethodView):
    def get(self):
        id = request.args.get('id')
        return tools.en_render_template('system/updateUser.html', edit_id=id)

class EditPersonalAcconut(MethodView):
    def post(self):
        return_data = jsonify({ 'code':300 })
        from data_mode.user_center.control.mixOp import MixUserCenterOp
        db_seesion = MixUserCenterOp().get_seesion()
        try:
            id = request.values.get('id', '')

            user = db_seesion.query(AdminUser).filter(AdminUser.id==id).first()

            #user = AdminUser.query.filter_by(id=id).first()

            name = request.values.get('name', '')
            if len(name):
                user.name = name
            email = request.values.get('email', '')
            if len(email):
                user.email = email
            password = request.values.get('password', '')
            if len(password):
                user.password = password
            work_number = request.values.get('work_number', '')
            if len(work_number):
                user.work_number = work_number
            gander = request.values.get('gander', '')
            if len(gander):
                user.gander = gander
            telephone = request.values.get('telephone', '')
            if len(telephone):
                user.telephone = telephone
            entry_time = request.values.get('entry_time', '')
            if len(entry_time):
                entry_time = datetime.strptime(entry_time, "%Y-%m-%d %H:%M:%S").date()
                user.entry_time = entry_time
            position_id = request.values.get('position_id', '')
            if len(position_id):
                user.position_id = position_id

            group_ids = request.values.get('group_ids', '')
            if len(group_ids):
                ids =  group_ids.split(',')
                groups = db_seesion.query(AdminGroup).filter(AdminGroup.id.in_(ids)).all()
                sql = "delete from admin_user_group where user_id = %s" % user.id
                db_seesion.execute(sql)
                user.groups = groups

            parttime_positions_ids = request.values.get('parttime_positions_ids', '')
            if len(parttime_positions_ids):
                p_p_ids = parttime_positions_ids.split(',')
                #positions = OrganPosition.query.filter(OrganPosition.id.in_(p_p_ids)).all()
                positions = db_seesion.query(OrganPosition).filter(OrganPosition.id.in_(p_p_ids)).all()
                sql = "delete from admin_user_parttime_position where user_id = %s" % user.id
                db_seesion.execute(sql)
                user.parttime_positions = positions

            db_seesion.add(user)
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

class DeletePersonalAcconut(MethodView):
    def post(self):
        return_data = jsonify({ 'code':300 })
        from data_mode.user_center.control.mixOp import MixUserCenterOp
        db_seesion = MixUserCenterOp().get_seesion()
        try:
            id = request.values.get('id', "")
            password = request.values.get('password', '')

            auth = False
            username = session['user']['username']


            #curl_user = AdminUser.query.filter_by(username = username).first()
            curl_user = db_seesion.query(AdminUser).filter(AdminUser.username==username).first()
            if curl_user is not None and curl_user.verify_password(password):
                auth = True
            if auth:
                user = db_seesion.query(AdminUser).filter(AdminUser.id == id).first()
                if user is None:
                    return_data = jsonify({ 'code':101 })
                else:
                    sql1 = "delete from admin_user_group where user_id = %s" % user.id
                    db_seesion.execute(sql1)
                    sql2 = "delete from admin_user_parttime_position where user_id = %s" % user.id
                    db_seesion.execute(sql2)
                    #db_seesion.delete(user)
                    user.is_active = False
                    user.position_id = None
                    db_seesion.add(user)
                    db_seesion.commit()
                    return_data = jsonify({ 'code':100 })
            else:
                return_data = jsonify({ 'code':107 })
        except IntegrityError, e:
            db_seesion.rollback()
            print e
        except Exception, e:
            db_seesion.rollback()
            print e
        return tools.en_return_data(return_data)



from . import sys, sys_prefix
from control_center.admin import add_url

add_url.add_url(u"账号管理", 'sys.set', add_url.TYPE_ENTRY, sys_prefix,
                sys, '/account/', 'account', AccountView.as_view('account'), 100,methods=['GET'])

add_url.add_url(u"账号管理页面元素", "sys.account", add_url.TYPE_FUNC,  sys_prefix,
                sys, '/account_data/', 'account_data', AccountDataView.as_view('account_data'), methods=['GET'])

add_url.add_url(u"新增账号", "sys.account", add_url.TYPE_FEATURE,  sys_prefix,
                sys, '/account_create/', 'account_create', AccountCreateView.as_view('account_create'), methods=['GET'])

add_url.add_url(u"新增账号页面元素", "sys.account_create", add_url.TYPE_FUNC,  sys_prefix,
                sys, '/account_create_data/', 'account_create_data', AccountCreateData.as_view('account_create_data'), methods=['GET'])

add_url.add_url(u"保存新增账号", "sys.account_create", add_url.TYPE_FEATURE,  sys_prefix,
                sys, '/account_create_save/', 'account_create_save', AccountCreateSave.as_view('account_create_save'), methods=['POST'])

add_url.add_url(u"获得个人账号页面", "sys.account", add_url.TYPE_FEATURE,  sys_prefix,
                sys, '/personal_acconut/', 'personal_acconut', PersonalAcconutView.as_view('personal_acconut'), methods=['GET'])

add_url.add_url(u"获得个人账号信息", "sys.account", add_url.TYPE_FUNC,  sys_prefix,
                sys, '/personal_acconut_data/', 'personal_acconut_data', PersonalAcconut.as_view('personal_acconut_data'), methods=['GET'])

add_url.add_url(u"编辑个人账号页面", "sys.account", add_url.TYPE_FEATURE,  sys_prefix,
                sys, '/edit_personal/', 'edit_personal', EditPersonalAcconutView.as_view('edit_personal'), methods=['GET'])

add_url.add_url(u"编辑个人账号保存", "sys.account", add_url.TYPE_FEATURE,  sys_prefix,
                sys, '/edit_personal_save/', 'edit_personal_save', EditPersonalAcconut.as_view('edit_personal_save'), methods=['POST'])

add_url.add_url(u"删除个人账号", "sys.account", add_url.TYPE_FEATURE,  sys_prefix,
                sys, '/delete_personal/', 'delete_personal', DeletePersonalAcconut.as_view('delete_personal'), methods=['POST'])