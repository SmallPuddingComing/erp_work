#-*-coding:utf-8-*-


from flask.views import MethodView
from flask import current_app, request, url_for, session
from flask import jsonify
from flask import json
from pprint import pprint
from public.function import tools



from data_mode.user_center.model.admin_url import AdminUrl

from data_mode.user_center.model.organ_company import OrganCompany
from data_mode.user_center.model.organ_department import OrganDepartMent


from sqlalchemy.exc import IntegrityError


class OrganView(MethodView):
    def get(self):
        #return u"组织架构管理"
        return tools.en_render_template('system/organizational.html')
        #return render_template('main/index.html')

class OrganDataView(MethodView):
    def get(self):
        return_data = jsonify({ 'code':300 })
        try:
            from data_mode.user_center.control.mixOp import MixUserCenterOp
            db_seesion = MixUserCenterOp().get_seesion()

            father = db_seesion.query(AdminUrl).filter(AdminUrl.endpoint=="sys.organ").first()
            m_urls = db_seesion.query(AdminUrl).filter(AdminUrl.parent_id == father.id, AdminUrl.type==add_url.TYPE_FEATURE)
            companys = db_seesion.query(OrganCompany).order_by(OrganCompany.id)

            companys_datas = []
            for company in companys:
                company_data = company.to_json()
                departMents = company.departments
                company_data['departMents'] = []
                for departMent in departMents:
                    departMent_data = departMent.to_json(company=False)
                    departMent_data['users']  = []
                    positions = departMent.positions
                    for position in positions:
                        users = position.users
                        for user in users:
                            if not user.is_active:
                                continue
                            user_data = user.to_json_simple()
                            departMent_data['users'].append(user_data)
                            if position.parent_id is None:
                                departMent_data['leader'] = user_data
                        parttime_users = position.parttime_users
                        for parttime_user in parttime_users:
                            if not parttime_user.is_active:
                                continue
                            user_data = parttime_user.to_json_simple()
                            departMent_data['users'].append(user_data)
                            if position.parent_id is None:
                                departMent_data['leader'] = user_data

                    company_data['departMents'].append(departMent_data)
                companys_datas.append(company_data)


            return_data =  jsonify({
                    'code': 100,
                    'feature_urls': [url.to_json() for url in m_urls],
                    'companys'    : companys_datas
                })
        except Exception, e:
            print e

        return tools.en_return_data(return_data)



class OrganCreateCompany(MethodView):
    def post(self):
        return_data = jsonify({ 'code':300 })
        from data_mode.user_center.control.mixOp import MixUserCenterOp
        db_seesion = MixUserCenterOp().get_seesion()
        try:
            name = request.values.get('name', '')
            if len(name):
                company = OrganCompany(name = name)
                db_seesion.add(company)
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


class OrganCreateDepartment(MethodView):
    def post(self):
        return_data = jsonify({ 'code':300 })
        from data_mode.user_center.control.mixOp import MixUserCenterOp
        db_seesion = MixUserCenterOp().get_seesion()
        try:
            name = request.values.get('name', "")
            parent_id = request.values.get('parent_id', 0)
            company_id = request.values.get('company_id', 0)
            if len(name):
                if int(parent_id) != 0:
                    departMent = OrganDepartMent(name = name, parent_id=parent_id, company_id=company_id)
                else:
                    departMent = OrganDepartMent(name = name,  company_id=company_id)
                db_seesion.add(departMent)
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



class EditOrgan(MethodView):
    def post(self):
        return_data = jsonify({ 'code':300 })
        from data_mode.user_center.control.mixOp import MixUserCenterOp
        db_seesion = MixUserCenterOp().get_seesion()
        try:
            dipartment_id = request.values.get('department_id', '')
            dipartment_name = request.values.get('department_name', '')

            if len(dipartment_name) and len(dipartment_id):
                departMent = db_seesion.query(OrganDepartMent).filter(OrganDepartMent.id==dipartment_id ).first()
                departMent.name = dipartment_name
                db_seesion.add(departMent)

            company_id = request.values.get('company_id', '')
            company_name = request.values.get('company_name', '')

            if len(company_name) and len(company_id):
                company = db_seesion.query(OrganCompany).filter(OrganCompany.id==company_id ).first()
                company.name = company_name
                db_seesion.add(company)
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

def delete_department(departMent, cur_seesion):
    for child in departMent.children:
        has_child = False
        for item in child.children:
            has_child = True
        if has_child:
            delete_department(child)
        else:
            cur_seesion.delete(child)
    cur_seesion.delete(departMent)

def delete_company(company, cur_seesion):
    for department in company.departments:
        delete_department(department, cur_seesion)
    cur_seesion.delete(company)





class DeleteOrgan(MethodView):
    def post(self):
        return_data = jsonify({ 'code':300 })
        from data_mode.user_center.control.mixOp import MixUserCenterOp, get_department_users, get_company_users
        db_seesion = MixUserCenterOp().get_seesion()
        try:
            dipartment_id = request.values.get('department_id', '')
            company_id = request.values.get('company_id', '')

            if len(dipartment_id):

                departMent = db_seesion.query(OrganDepartMent).filter(OrganDepartMent.id==dipartment_id).first()
                users = get_department_users(departMent)
                if not len(users):
                    delete_department(departMent, db_seesion)
                    db_seesion.commit()
                    return_data = jsonify({ 'code':100 })
                else:
                    return_data = jsonify({ 'code':102 })

            if len(company_id):
                company = db_seesion.query(OrganCompany).filter(OrganCompany.id == company_id).first()
                users = get_company_users(company)
                if not len(users):
                    delete_company(company, db_seesion)
                    db_seesion.commit()
                    return_data = jsonify({ 'code':100 })
                else:
                    return_data = jsonify({ 'code':102 })

        except IntegrityError, e:
            db_seesion.rollback()
            print e
        except Exception, e:
            db_seesion.rollback()
            print e
        return tools.en_return_data(return_data)


from . import sys, sys_prefix
from control_center.admin import add_url

add_url.add_url(u"组织架构", "sys.set", add_url.TYPE_ENTRY,  sys_prefix,
                sys, '/organ/', 'organ', OrganView.as_view('organ'), 90,methods=['GET'])

add_url.add_url(u"组织架构页面元素", "sys.organ", add_url.TYPE_FUNC,  sys_prefix,
                sys, '/organ_data/', 'organ_data', OrganDataView.as_view('organ_data'), methods=['GET'])

add_url.add_url(u"创建公司", "sys.organ", add_url.TYPE_FEATURE,  sys_prefix,
                sys, '/create_company/', 'create_company', OrganCreateCompany.as_view('create_company'), methods=['POST'])

add_url.add_url(u"创建部门", "sys.organ", add_url.TYPE_FEATURE,  sys_prefix,
                sys, '/create_department/', 'create_department', OrganCreateDepartment.as_view('create_department'), methods=['POST'])


add_url.add_url(u"编辑组织架构", "sys.organ", add_url.TYPE_FEATURE,  sys_prefix,
                sys, '/edit_organ/', 'edit_organ', EditOrgan.as_view('edit_organ'), methods=['POST'])

add_url.add_url(u"删除组织架构", "sys.organ", add_url.TYPE_FEATURE,  sys_prefix,
                sys, '/delete_organ/', 'delete_organ', DeleteOrgan.as_view('delete_organ'), methods=['POST'])



