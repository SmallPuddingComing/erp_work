#-*- coding:utf-8 -*-

import json
from flask.views import MethodView
from flask import session, jsonify, request
from public.function import tools

from control_center.supply_chain.supplier_manage.control.supplier_baseinfo_op import SupplierBaseInfoOp
from public.upload_download.upload_download import pub_upload_picture_to_server
from public.upload_download.upload_download import pub_upload_picture_to_qiniu
from config.service_config.returncode import ServiceCode
from data_mode.user_center.model.organ_company import OrganCompany
from data_mode.user_center.control.mixOp import MixUserCenterOp
from control_center.admin import add_url
from control_center.supply_chain import baseinfo_prefix, baseinfo


class SupplyBaseInfoView(MethodView):

    @staticmethod
    def get():
        supply_id = request.args.get('supplier_id')
        supply_op = SupplierBaseInfoOp()
        result_data = supply_op.get_supplier_base_info(supply_id)
        statedict = supply_op.get_state_all_type_info()
        result_data['stateDict'] = statedict

        db_seesion = MixUserCenterOp().get_seesion()
        companys = db_seesion.query(OrganCompany).order_by(OrganCompany.id)

        organDate = []
        for company in companys:
            company_data = company.to_json()
            departments = company.departments
            company_data['departMents'] = []
            for department in departments:
                department_data = department.to_json(company=False)
                department_data['users'] = []
                positions = department.positions
                for position in positions:
                    users = position.users
                    for user in users:
                        if not user.is_active:
                            continue
                        user_data = user.to_json_simple()
                        department_data['users'].append(user_data)
                        if position.parent_id is None:
                            department_data['leader'] = user_data
                    parttime_users = position.parttime_users
                    for parttime_user in parttime_users:
                        if not parttime_user.is_active:
                            continue
                        user_data = parttime_user.to_json_simple()
                        department_data['users'].append(user_data)
                        if position.parent_id is None:
                            department_data['leader'] = user_data

                company_data['departMents'].append(department_data)
            organDate.append(company_data)

        result = {}
        if organDate:
            result = {
                'supplier_id': supply_id,
                'result': result_data,
                'organDate': organDate
            }
            print result

        result = json.dumps(result)
        return tools.en_render_template('supplyChain/supplierManage/up-BasicInfo.html', result=result)


class SupplyOtherInfoView(MethodView):
    @staticmethod
    def get():

        supply_id = request.args.get('supplier_id')
        supply_op = SupplierBaseInfoOp()
        result_data = supply_op.get_supplier_other_info(supply_id)
        seltdatedict = supply_op.get_all_selt_date_type()
        seltmodeldict = supply_op.get_all_selt_modes_info()

        bankdict = {
            1: '中国银行',
            2: '招商银行',
            3: '工商银行',
            4: '农业银行',
            5: '建设银行',
            6: '交通银行',
            7: '浦发银行',
            8: '中信银行',
            9: '信业银行',
            10: '民生银行'
        }
        result = json.dumps({
            'supplier_id': supply_id,
            'result_data': result_data,
            'seltdateDict': seltdatedict,
            'seltmodelDict': seltmodeldict,
            'bankDict': bankdict
        })
        return tools.en_render_template('supplyChain/supplierManage/up-OtherInfo.html', result=result)


class SupplyArchievedInfoView(MethodView):
    @staticmethod
    def get():
        supply_id = request.args.get('supplier_id')
        supply_op = SupplierBaseInfoOp()
        file_dict = supply_op.get_supplier_achieve_info(supply_id)
        # file_dict['type_list'] ={
	 	# 	1 : "other",          			       #其他
	 	# 	2 :"business_lincese",                 #营业执照
	 	# 	3 :"tax_regist",                  #税务登记证
	 	# 	4 :"organize_code",                    #组织机构代码证
	 	# 	5 :"taxpayers_certificate",            #一般纳税人证书下载地址
	 	# 	6 :"bank_name_prove",                  #银行开户证明
	 	# 	7 :"supllier_survey",                  #供应商调查卷
	 	# 	8 :"on_site_review",                   #现场审查报告
	 	# 	9 :"application",                      #免现场审查申请书
        # }
        result = {
            'code': 100,
            'supplier_id': supply_id,
            'fileDict': file_dict

         }
        return tools.en_render_template('supplyChain/supplierManage/up-ArchiveInfo.html', result=json.dumps(result))


class SaveSupplyBaseView(MethodView):
    @staticmethod
    def post():
        return_data = jsonify({'code': 300})
        try:

            # @function : 保存供应商基本信息
            # :param sup_id: 供应商id
            # :param supplier_code: 供应商代码
            # :param supplier_name: 供应商名称
            # :param supplier_full_name: 供应商全称
            # :param currency_id: 币种
            # :param principal_id: 采购对接人
            # :param state: 状态
            # :return: bool.

            # sup_id = request.values.get('sup_id', '')
            sup_code = request.values.get('supplier_code', '')
            sup_name = request.values.get('supplier_name', '')
            sup_full_name = request.values.get('supplier_full_name', '')
            currency_id = request.values.get('currency_id', '')
            principal_id = request.values.get('principal_id', '')
            state = request.values.get('state', '')

            supply_op = SupplierBaseInfoOp()
            show_state = supply_op.StateShow
            supply_op.save_supplier_baseinfo(sup_code, sup_name, sup_full_name,
                                             currency_id, principal_id, state, show_state)

            return_data = jsonify({'code': ServiceCode.success})

        except Exception, e:
            print e
            return_data = jsonify({'code': ServiceCode.service_exception})
        return tools.en_return_data(return_data)


class SaveSupplyOtherView(MethodView):
    @staticmethod
    def post():

        # :param sup_id: 供应商id
        # :param selt_modes_id: 结算方式id
        # :param selt_dater_id: 结算日期id
        # :param vat_rates: 增值税率
        # :param supplier_country: 所属国家
        # :param supplier_province: 所属省份
        # :param supplier_city: 所属城市
        # :param bank_name: 开户银行
        # :param acct_no: 银行账号
        # :param tax_regist_no: 税务登记号
        # :param business_lincese: 营业执照注册号
        # :param organize_code: 组织机构代码

        return_data = jsonify({'code': 300})
        try:
            selt_modes_id = request.values.get('selt_modes_id', type=str)
            selt_dater_id = request.values.get('selt_dater_id', type=str)
            vat_rates = request.values.get('vat_rates', "")
            supplier_id = request.values.get('supplier_id', "")
            supplier_country = request.values.get('supplier_country', "")
            supplier_province = request.values.get('supplier_province', "")
            supplier_city = request.values.get('supplier_city', "")
            supplier_addr = request.values.get('supplier_addr', "")
            bank_name = request.values.get('bank_name', "")
            acct_no = request.values.get('acct_no', "")
            tax_regist_no = request.values.get('tax_regist_no', "")
            business_lincese = request.values.get('business_lincese', "")
            organize_code = request.values.get('organize_code', "")

            op = SupplierBaseInfoOp()
            rs = op.save_supplier_otherinfo(supplier_id, selt_modes_id, selt_dater_id, vat_rates,
                                supplier_country, supplier_province, supplier_city,
                                supplier_addr, bank_name, acct_no, tax_regist_no,
                                business_lincese, organize_code)

            #联系人信息列表
            contactAlllist = request.values.get('link_info', '')
            print contactAlllist, type(contactAlllist)
            contactalllistinfo = json.loads(contactAlllist)
            rs = op.save_supplier_contact_info(supplier_id, contactalllistinfo)
            return_data = jsonify({'code': ServiceCode.success})

        except Exception, e:
            print e
            return_data = jsonify({'code': ServiceCode.service_exception})
        return tools.en_return_data(return_data)


class DeleteContactinfo(MethodView):
    @staticmethod
    def post():
        return_data = jsonify({'code': ServiceCode.service_exception})
        try:
            contact_id = request.values.get('contact_id', "")
            op = SupplierBaseInfoOp()
            rs = op.del_supplier_contact_by_id(contact_id)
            return_data = jsonify({'code': ServiceCode.success})
        except Exception, e:
            print e
            return_data = jsonify({'code': ServiceCode.service_exception})
        return tools.en_return_data(return_data)


class SaveSupplyArchievedView(MethodView):
    @staticmethod
    def post():
        return_data = jsonify({'code': ServiceCode.service_exception})
        try:
            supplier_id = request.values.get('supplier_id', '')
            file_info_dict_info = request.values.get('normal', '')
            file_info_dict_info = json.loads(file_info_dict_info)
            other = request.values.get('other', '')
            other = json.loads(other)

            file_info_dict = {
                'other': other,
                'file_info_dict': file_info_dict_info
            }
            op = SupplierBaseInfoOp()
            for item in other:
                if item['id']:
                    rs = op.save_achieve_info_new(supplier_id, item['id'], item['file_url'],
                                                    item['file_name'], item['file_path'],
                                                    item['file_type_id'])
            for item in file_info_dict_info:
                if item:
                    rs = op.save_achieve_info_new(supplier_id, item['id'], item['file_url'],
                                                    item['file_name'], item['file_path'],
                                                    item['file_type_id'])

            return_data = jsonify({'code': ServiceCode.success})
        except Exception, e:
            print e
            return_data = jsonify({'code': ServiceCode.service_exception})
        return tools.en_return_data(return_data)


class UploadSupplyPic(MethodView):
    @staticmethod
    def post():
        try:
            upload_file = request.files.get('file', '')
            state = pub_upload_picture_to_server()
            s, path = pub_upload_picture_to_qiniu(state)
            local_path = state['path']
            if not s:
                data = {'code': 300}
            else:
                data = {'code': 100, 'pic': path, 'filename': upload_file.filename, 'path': local_path}
            return tools.en_return_data(jsonify(data))
        except Exception as ex:
                print(ex)
                data = {'code': 300}
                return tools.en_return_data(jsonify(data))

add_url.add_url(u"编辑供应商基本信息", "baseinfo.show_view", add_url.TYPE_FEATURE, baseinfo_prefix,
                baseinfo, '/supply/baseinfo/', 'SupplyBaseInfoView',
                SupplyBaseInfoView.as_view('SupplyBaseInfoView'), methods=['GET'])

add_url.add_url(u"编辑供应商其它信息", "baseinfo.show_view", add_url.TYPE_FEATURE, baseinfo_prefix,
                baseinfo, '/supply/otherinfo/', 'SupplyOtherInfoView',
                SupplyOtherInfoView.as_view('SupplyOtherInfoView'), methods=['GET'])

add_url.add_url(u"编辑供应商存档信息", "baseinfo.show_view", add_url.TYPE_FEATURE, baseinfo_prefix,
                baseinfo, '/supply/archivevedinfo/', 'SupplyArchievedInfoView',
                SupplyArchievedInfoView.as_view('SupplyArchievedInfoView'), methods=['GET'])

add_url.add_url(u"保存供应商基本信息", "baseinfo.SupplyBaseInfoView", add_url.TYPE_FEATURE, baseinfo_prefix,
                baseinfo, '/supply/save_base_info/', 'SaveSupplyBaseView',
                SaveSupplyBaseView.as_view('SaveSupplyBaseView'), methods=['POST'])

add_url.add_url(u"保存供应商其它信息", "baseinfo.SupplyOtherInfoView", add_url.TYPE_FEATURE, baseinfo_prefix,
                baseinfo, '/supply/save_other_info/', 'SaveSupplyOtherView',
                SaveSupplyOtherView.as_view('SaveSupplyOtherView'), methods=['POST'])

add_url.add_url(u"保存供应商存档信息", "baseinfo.SupplyArchievedInfoView", add_url.TYPE_FEATURE, baseinfo_prefix,
                baseinfo, '/supply/save_achieved_info/', 'SaveSupplyArchievedView',
                SaveSupplyArchievedView.as_view('SaveSupplyArchievedView'), methods=['POST'])

add_url.add_url(u"添加供应商附件", "baseinfo.SupplyArchievedInfoView", add_url.TYPE_FEATURE, baseinfo_prefix,
                baseinfo, '/supply/up_load_pic/', 'UploadSupplyPic',
                UploadSupplyPic.as_view('UploadSupplyPic'), methods=['POST'])

add_url.add_url(u"删除联系人", "baseinfo.SupplyOtherInfoView", add_url.TYPE_FEATURE, baseinfo_prefix,
                baseinfo, '/supply/del_contact/', 'DeleteContactinfo',
                DeleteContactinfo.as_view('DeleteContactinfo'), methods=['POST'])