#-*-coding:utf-8-*-


from flask.views import MethodView
from flask import current_app, request, url_for, session
from flask import jsonify
from flask import json
from pprint import pprint
from public.function import tools



from data_mode.user_center.model.admin_url import AdminUrl

from data_mode.user_center.model.organ_position import OrganPosition
from data_mode.user_center.model.organ_department import OrganDepartMent



from sqlalchemy.exc import IntegrityError
from model_data import get_organ_data


class PositionView(MethodView):
    def get(self):
        #return "position"
        return tools.en_render_template('system/system-alarm.html')


class PositionDataView(MethodView):
    def get(self):
        return_data = jsonify({ 'code':300 })
        try:
            # father = AdminUrl.query.filter_by(endpoint="sys.position").first()
            # m_urls = AdminUrl.query.filter_by(parent_id = father.id, type=add_url.TYPE_FEATURE)
            from data_mode.user_center.control.mixOp import MixUserCenterOp
            db_seesion = MixUserCenterOp().get_seesion()

            father = db_seesion.query(AdminUrl).filter(AdminUrl.endpoint=="sys.position").first()
            m_urls = db_seesion.query(AdminUrl).filter(AdminUrl.parent_id == father.id, AdminUrl.type==add_url.TYPE_FEATURE)

            position_level = [
                               {"id": 1, "name": u"一级职位" } ,
                               {"id": 2, "name": u"二级职位" } ,
                               {"id": 3, "name": u"三级职位" } ,
                               {"id": 4, "name": u"四级职位" } ,
                            ]
            return_data =  jsonify({
                    'code': 100,
                    'feature_urls': [url.to_json() for url in m_urls],
                    'companys'    : get_organ_data(disable_users = True),
                    'position_level' : position_level
                })
        except Exception, e:
            print e
        return tools.en_return_data(return_data)


class PositionCreate(MethodView):
    def post(self):
        return_data = jsonify({ 'code':300 })
        from data_mode.user_center.control.mixOp import MixUserCenterOp
        db_seesion = MixUserCenterOp().get_seesion()

        try:
            name = request.values.get('name', "")
            department_id = request.values.get('department_id', "")
            position_level = request.values.get('position_level', 1)
            if len(name):
                position = None
                p = db_seesion.query(OrganPosition).filter(OrganPosition.department_id==department_id).first()
                if p is None:
                    position = OrganPosition(name = name,  position_level=position_level, department_id=department_id)
                else:
                    position = OrganPosition(name = name,  position_level=position_level, department_id=department_id, parent_id=p.id)
                db_seesion.add(position)
                db_seesion.commit()
                return_data = jsonify({ 'code':100 })
            else:
                pass
        except IntegrityError, e:
            db_seesion.rollback()
            return_data = jsonify({ 'code':109 })
            print e
        except Exception, e:
            db_seesion.rollback()
            print e
        return tools.en_return_data(return_data)


class PositionEditor(MethodView):
    def post(self):
        return_data = jsonify({ 'code':300 })
        from data_mode.user_center.control.mixOp import MixUserCenterOp
        db_seesion = MixUserCenterOp().get_seesion()
        try:
            position_id = request.values.get('id', "")
            name = request.values.get('name', "")
            department_id = request.values.get('department_id', "")
            position_level = request.values.get('position_level', "")
            if len(position_id):
                #position = OrganPosition.query.filter_by(id=position_id).first()
                position = db_seesion.query(OrganPosition).filter(OrganPosition.id==position_id ).first()
                if position is None:
                    return_data = jsonify({ 'code':101 })
                else:
                    if len(name):
                        position.name = name
                    if len(department_id):
                        position.department_id = department_id
                    if len(position_level):
                        position.position_level = position_level
                    db_seesion.add(position)
                    db_seesion.commit()
                    return_data = jsonify({ 'code':100 })
            else:
                return_data = jsonify({ 'code':101 })
        except IntegrityError, e:
            db_seesion.rollback()
            return_data = jsonify({ 'code':109 })
            print e
        except Exception, e:
            db_seesion.rollback()
            print e
        return tools.en_return_data(return_data)


class PositionDelete(MethodView):
    def post(self):
        return_data = jsonify({ 'code':300 })
        from data_mode.user_center.control.mixOp import MixUserCenterOp
        db_seesion = MixUserCenterOp().get_seesion()
        try:
            position_id = request.values.get('id', "")
            #position = OrganPosition.query.filter_by(id=position_id).first()
            position = db_seesion.query(OrganPosition).filter(OrganPosition.id==position_id).first()
            if position is None:
                return_data = jsonify({ 'code':101 })
            size = 0
            lenx =  len(position.users)

            for user in position.users:
                size = size + 1
                break
            if size > 0:
                return_data = jsonify({ 'code':102 })
            else:
                size = 0
                for pos in position.children:
                    size = size + 1
                    break
                if size > 0:
                    return_data = jsonify({ 'code':111 })
                else:
                    db_seesion.delete(position)
                    db_seesion.commit()
                    return_data = jsonify({ 'code':100 })
        except IntegrityError, e:
            return_data = jsonify({ 'code':109 })
            db_seesion.rollback()
            print e
        except Exception, e:
            db_seesion.rollback()
            print e
        return tools.en_return_data(return_data)


from . import sys, sys_prefix
from control_center.admin import add_url

add_url.add_url(u"职务管理", "sys.set", add_url.TYPE_ENTRY,  sys_prefix,
                sys, '/position/', 'position', PositionView.as_view('position'), 80,methods=['GET'])

add_url.add_url(u"职务管理页面元素", "sys.position", add_url.TYPE_FUNC,  sys_prefix,
                sys, '/position_data/', 'position_data', PositionDataView.as_view('position_data'), methods=['GET'])

add_url.add_url(u"创建职务", "sys.position", add_url.TYPE_FEATURE,  sys_prefix,
                sys, '/create_position_save/', 'create_position_save', PositionCreate.as_view('create_position_save'), methods=['POST'])

add_url.add_url(u"编辑职务", "sys.position", add_url.TYPE_FEATURE,  sys_prefix,
                sys, '/editor_position/', 'editor_position', PositionEditor.as_view('editor_position'), methods=['POST'])

add_url.add_url(u"删除职务", "sys.position", add_url.TYPE_FEATURE,  sys_prefix,
                sys, '/delete_position/', 'delete_position', PositionDelete.as_view('delete_position'), methods=['POST'])





