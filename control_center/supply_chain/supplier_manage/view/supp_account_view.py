#!/usr/bin/python
#-*- coding:utf-8 -*-

import json
import traceback
from flask.views import MethodView
from public.function import tools
from flask import request, session, url_for, jsonify
from config.service_config.returncode import *
from control_center.supply_chain.supplier_manage.control.supplier_baseinfo_op import *
from public.upload_download.upload_download import pub_upload_picture_to_server
from public.upload_download.upload_download import pub_upload_picture_to_qiniu
from public.exception.custom_exception import CodeError
from public.sale_share.share_function import SupplyAttr

class SupplierView(MethodView):
    def get(self):
        '''
        @function: 添加物料渲染界面
        '''
        return_data = None

        from data_mode.user_center.model.organ_company import OrganCompany
        from data_mode.user_center.control.mixOp import MixUserCenterOp

        try:
            op = SupplierBaseInfoOp()
            currencyData = op.get_all_currency_info()
            stateData = op.get_state_all_type_info()
            codeData = json.loads(op.get_supplier_code_by_auto())

            db_seesion = MixUserCenterOp().get_seesion()
            companys = db_seesion.query(OrganCompany).order_by(OrganCompany.id)

            organDate = []
            for company in companys:
                company_data = company.to_json()
                departMents = company.departments
                company_data['departMents'] = []
                for departMent in departMents:
                    departMent_data = departMent.to_json(company=False)
                    print "11111111111111111111"
                    print departMent_data, departMent_data["name"]
                    departMent_data['users'] = []
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
                organDate.append(company_data)
            print '************************************************'
            print organDate
            if organDate:
                return_data = json.dumps({'currencyData': currencyData,
                                          'stateData': stateData,
                                          'codeData': codeData,
                                          'organDate': organDate,
                                          'code': ServiceCode.success})
            else:
                raise CodeError(code=ServiceCode.service_exception, msg=u"获取公司组织架构信息失败！")
        except CodeError as e:
            print traceback.format_exc()
            error_data = e.json_value()
            return_data = json.dumps({'code': ServiceCode.service_exception, 'msg': error_data.get('msg', None)})
        except Exception as e:
            print traceback.format_exc()
            return_data = json.dumps({'code': ServiceCode.service_exception, 'msg': u'服务器错误！'})
        finally:
            print "return_data: ", return_data
            return tools.flagship_render_template('supplyChain/supplierManage/add-BasicInfo.html',
                                            result=return_data)

class SkipSupplierListInfoView(MethodView):
    def get(self):
        '''
        @function : 跳转供应商列表信息界面
        :return:
        '''
        return tools.en_render_template('supplyChain/supplierManage/add-OtherInfo.html')

class SkipSupplierOtherInfoView(MethodView):
    def get(self):
        '''
        @function : 跳转其他信息界面
        :return:
        '''
        supplier_id = request.args.get('id', "")

        return tools.en_render_template('supplyChain/supplierManage/add-OtherInfo.html')

class getSupllierCode(MethodView):
    def get(self):
        '''
        @function : 获得供应商代码，按数据库顺序给
        :return: supplier_code
        '''
        op = SupplierBaseInfoOp()
        return_data = op.get_supplier_code_by_auto()
        return tools.en_return_data(jsonify(return_data))

class CheckSupplierCode(MethodView):
    def get(self):
        '''
        @function : 检查供应商代码是否重复
        :return: code
        '''
        supplier_code = request.args.get('supplier_code', "")
        op = SupplierBaseInfoOp()
        rs = op.get_clerk_info(supplier_code)
        return_data = jsonify(json.loads(rs))
        return tools.en_return_data(return_data)

class CheckSupplierName(MethodView):
    def get(self):
        '''
        @function : 检查供应商名字是否重复
        :return: code
        '''
        supplier_code = request.args.get('supplier_name', "")
        op = SupplierBaseInfoOp()
        rs = op.get_check_supplier_name_info(supplier_code)
        return_data = jsonify(json.loads(rs))
        return tools.en_return_data(return_data)

class SupplierAddBaseInfoView(MethodView):
    def post(self):
        '''
        @function : 保存供应商基础信息
        :return: code
        '''
        currency_id = request.values.get('currency_id', type=str)
        supplier_full_name = request.values.get('supplier_full_name',"").encode()
        supplier_name = request.values.get('supplier_name', "").encode()
        supplier_code = request.values.get('supplier_code',"").encode()
        principal_id = request.values.get('principal_id', "").encode()
        state_id = request.values.get('state_id', "").encode()

        print "currency_id, state_id", currency_id, state_id

        op = SupplierBaseInfoOp()
        state_show = SupplyAttr.SUPPLIER_STATE_SHOW
        rs = op.save_supplier_baseinfo(supplier_code, supplier_name, supplier_full_name, currency_id,
                                       principal_id, state_id, state_show)
        rs = json.loads(rs)
        print "rs: -----------------", rs
        if rs.get('code') == ServiceCode.success:
            return jsonify({
                'code': ServiceCode.success,
                'supplier_id': rs.get('supplier_id'),
                'currencyData': {'1-1': SupplyAttr.CURR_RMB,
                                 '1-2': SupplyAttr.CURR_DOLLORES},
                'stateData': {'2-1': SupplyAttr.STATE_USE,
                              '2-2': SupplyAttr.STATE_UNUSER,
                              '2-3': SupplyAttr.STATE_CLAM}
            })
        return jsonify({
            'code': rs.get('code')
        })

class SupplierAddOtherView(MethodView):
    def post(self):
        '''
        @function : 保存供应商其他信息
        :return: code
        '''
        selt_modes_id = request.values.get('selt_modes_id', type=str)
        selt_dater_id = request.values.get('selt_dater_id', type=str)
        vat_rates = request.values.get('vat_rates', "")
        supplier_code = request.values.get('supplier_code',"")
        supplier_country = request.values.get('supplier_country', "")
        supplier_province = request.values.get('supplier_province', "")
        supplier_city = request.values.get('supplier_city', "")
        supplier_addr = request.values.get('supplier_addr', "")
        bank_name = request.values.get('bank_name', "")
        acct_no = request.values.get('acct_no', "")
        tax_regist_no = request.values.get('tax_regist_no', "")
        business_lincese = request.values.get('business_lincese', "")
        organize_code = request.values.get('organize_code', "")
        contact_count = request.values.get('contact_count', type=int)

        #联系人信息列表
        contactAllDict = {}
        attribute_list = ['id', 'name', 'position', 'mobile', 'email', 'telphone', 'tax']
        for i in xrange(contact_count):
            str = 'contact_list' + '[' + str(i) + ']' #'contact_list[0]'
            contactInfo = {}
            for attr in attribute_list:
                contact_str = str + '[' + attr  + ']'#'contact_list[0][name]'
                contact_info = request.values.get(contact_str, "")
                contactInfo[attr] = contact_info
            contactAllDict[str] = contactInfo #{'contact_list[0]':['name','position'...]}

        #联系人id删除列表
        delContactList = []
        for key, val in request.values.items():
            if key == 'del_list':
                delContactList.append(val)

        op = SupplierBaseInfoOp()
        rs = op.save_supplier_otherinfo(supplier_code, selt_modes_id, selt_dater_id, vat_rates,
                                supplier_country, supplier_province, supplier_city,
                                supplier_addr, bank_name, acct_no, tax_regist_no,
                                business_lincese, organize_code)

        rs_1 = op.save_supplier_contact_info(supplier_code, contactAllDict, delContactList)
        rs = json.loads(rs)
        rs_1 = json.loads(rs_1)
        if rs.get('code') == ServiceCode.success and rs_1.get('code') == ServiceCode.success:
            return jsonify({
                'code': ServiceCode.success
            })
        return jsonify({
            'code': rs.get('code')
        })

class SupplierAddAchiveView(MethodView):
    def post(self):
        '''
        @function : 保存供应商存档信息
        :return: code
        '''
        business_lincese_url = request.values.get('business_lincese_url', "")
        tax_regist_url = request.values.get('tax_regist_url', "")
        organize_code_url = request.values.get('organize_code_url', "")
        supplier_code = request.values.get('supplier_code',"")
        taxpayers_certificate_url = request.values.get('taxpayers_certificate_url', "")
        bank_name_prove_url = request.values.get('bank_name_prove_url', "")
        supllier_survey_url = request.values.get('supllier_survey_url', "")
        on_site_review_url = request.values.get('on_site_review_url', "")
        other_qualification_count = request.values.get('qualification_count', "")
        del_other_quality_list = request.values.get('del_other_quality_list', "")

        otherQualityAllDict = {}
        attribute_list = ['id', 'url']
        for i in xrange(other_qualification_count):
            str = 'quality_list' + '[' + str(i) + ']' #'contact_list[0]'
            qualityInfo = {}
            for attr in attribute_list:
                quality_str = str + '[' + attr  + ']'#'contact_list[0][name]'
                quality_info = request.values.get(quality_str, "")
                qualityInfo[attr] = quality_info
            otherQualityAllDict[str] = qualityInfo #{'contact_list[0]':['name','position'...]}

        #删除其他资质证书id列表
        delQualityList = []
        for key, val in request.values.items():
            if key == 'del_list':
                delQualityList.append(val)

        op = SupplierBaseInfoOp()
        rs = op.save_achieve_info(supplier_code, business_lincese_url, tax_regist_url, organize_code_url,
                                        taxpayers_certificate_url, bank_name_prove_url, supllier_survey_url, on_site_review_url)

        rs_1 = op.save_more_qualification_info(supplier_code, otherQualityAllDict, del_other_quality_list)
        rs = json.loads(rs)
        rs_1 = json.loads(rs_1)
        if rs.get('code')==ServiceCode.success and rs_1.get('code')==ServiceCode.success:
            return jsonify({
                'code': ServiceCode.success
            })
        return jsonify({
            'code': rs.get('code')
        })

class AddSupllierImageInfo(MethodView):
    def post(self):
        '''
        @function : 保存供应商存档信息图片
        :return:    {code， pic_path}
        '''

        try:
            state = pub_upload_picture_to_server()
            s, path = pub_upload_picture_to_qiniu(state)
            if not s:
                data = {'code': ServiceCode.authcode_error}
            else:
                data = {'code': ServiceCode.success, 'pic': path}

            return tools.en_return_data(jsonify(data))
        except Exception as ex:
            print(ex)
            print(traceback.format_exc())
            data = {'code': ServiceCode.service_exception, 'msg': u'服务器错误'}
            return tools.en_return_data(jsonify(data))

class SupplierRebackAddBaseInfoView(MethodView):
    def get(self):
        '''
        @function : 暂时不用
        :return:
        '''
        pass

class SupplierRebackAddOtherView(MethodView):
    def get(self):
        '''
        @function : 暂时不用
        :return:
        '''
        pass

from control_center.admin import add_url
from control_center.supply_chain import baseinfo_prefix, baseinfo


add_url.add_url(u"新增供应商", "baseinfo.supplier_index", add_url.TYPE_ENTRY, baseinfo_prefix,
                baseinfo, '/show_view/', 'show_view', SupplierView.as_view('show_view'), methods=['GET'])

add_url.add_url(u"检查供应商代码", "baseinfo.show_view", add_url.TYPE_FEATURE, baseinfo_prefix,
                baseinfo, '/show_view/check_code/', 'check_code', CheckSupplierCode.as_view('check_code'), methods=['GET', 'POST'])

# add_url.add_url(u"获得供应商代码", "supplier_manager.show_view", add_url.TYPE_FEATURE, supplier_prefix,
#                 supplier, '/show_view/get_code/', 'get_code', getSupllierCode.as_view('get_code'), methods=['GET'])

add_url.add_url(u"检查供应商名字", "baseinfo.show_view", add_url.TYPE_FEATURE, baseinfo_prefix,
                baseinfo, '/show_view/check_supplier_name/', 'check_supplier_name', CheckSupplierName.as_view('check_supplier_name'), methods=['GET', 'POST'])

add_url.add_url(u"跳转供应商列表界面", "baseinfo.show_view", add_url.TYPE_FEATURE,  baseinfo_prefix,
                baseinfo, '/show_view/skip_supplier_list_info/', 'skip_supplier_list_info', SkipSupplierListInfoView.as_view('skip_supplier_list_info'), methods=['GET'])

add_url.add_url(u"跳转其他信息界面", "baseinfo.show_view", add_url.TYPE_FEATURE,  baseinfo_prefix,
                baseinfo, '/show_view/skip_other_info/', 'skip_other_info', SkipSupplierOtherInfoView.as_view('skip_other_info'), methods=['GET'])

add_url.add_url(u"供应商第一步提交", "baseinfo.show_view", add_url.TYPE_FEATURE,  baseinfo_prefix,
                baseinfo, '/show_view/add_base_info/', 'add_base_info', SupplierAddBaseInfoView.as_view('add_base_info'), methods=['POST'])
