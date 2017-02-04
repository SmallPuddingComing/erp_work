#!/usr/bin/python
# -*- coding:utf-8 -*-
#    Copyright(c) 2015-2016 JmGo Company
#    All rights reserved.
#
#    文件名 : customer_info.py
#    作者   : DengLiming
#  电子邮箱 : lmdeng@jmgo.com
#    日期   : 2016/12/30 11:48
#
#     描述  :
#
import traceback,json
from control_center.supply_chain import baseinfo, baseinfo_prefix
from control_center.admin import add_url
from public.function import tools
from public.exception.custom_exception import CodeError
from flask.views import MethodView
from control_center.supply_chain.customer_manage.control.customer_info_op import CustomerInfoOp
from flask import request
from config.service_config.returncode import ServiceCode
from public.logger.syslog import SystemLog


class CustomerInfo(MethodView):
    @staticmethod
    def get():
        return_data = None
        result = {}
        try:
            is_data = request.args.get('is_data', 0, int)
            page_number = request.args.get('page_number', 1, int)
            customer_name = request.args.get('customer_name', '')
            page_size = request.args.get('page_size', 10, int)
            c_op = CustomerInfoOp()
            res = c_op.customer_info_list(page_number=page_number, customer_name=customer_name, page_size=page_size)
            if res['code'] == ServiceCode.success:
                result = {'code': ServiceCode.success, 'total': res['total'], 'data': res['data'], 'msg': u'查询成功'}
            # if is_data:
            #     return tools.en_return_data(json.dumps(result))
            # else:
            #     return tools.en_render_template('supplyChain/customers/customersManage.html', result=json.dumps(result))
        except CodeError as e:
            return_data = e.json_value()
        except Exception:
            SystemLog.pub_warninglog(traceback.format_exc())
            return_data = {'code': ServiceCode.service_exception, 'msg': u'服务器错误'}
        else:
            return_data = result
        finally:
            if is_data:
                return tools.en_return_data(json.dumps(result))
            else:
                return tools.en_render_template('supplyChain/customers/customersManage.html',
                                                result=json.dumps(return_data))


class AddCustomerInfo(MethodView):
    @staticmethod
    def get():
        return_data = None
        result = {}
        try:
            c_op = CustomerInfoOp()
            res = c_op.get_customer_type()
            if res['code'] == ServiceCode.success:
                result['data'] = res['data']
            else:
                result['data'] = ''
            result['is_type'] = 0
            result['code'] = ServiceCode.success
            result['msg'] = '成功'
            # return tools.en_render_template('supplyChain/customers/newCustomers.html', result=tools.en_return_data(json.dumps(result)))
        except CodeError as e:
            return_data = e.json_value()
        except Exception:
            SystemLog.pub_warninglog(traceback.format_exc())
            return_data = {'code': ServiceCode.service_exception, 'msg': u'服务器错误'}
        else:
            return_data = result
        finally:
            return tools.en_render_template('supplyChain/customers/newCustomers.html', result=json.dumps(return_data))

    @staticmethod
    def post():
        return_data = None
        try:
            parameter_dict = dict()
            parameter_dict['customer_name'] = request.values.get('customer_name', '')
            parameter_dict['customer_code'] = request.values.get('customer_code', None)
            parameter_dict['province'] = request.values.get('province', '')
            parameter_dict['city'] = request.values.get('city', '')
            parameter_dict['county'] = request.values.get('county', '')
            parameter_dict['address'] = request.values.get('address', '')
            parameter_dict['customer_type_id'] = request.values.get('customer_type_id', 0, int)
            parameter_dict['customer_type'] = request.values.get('customer_type', '')
            parameter_dict['company_tel'] = request.values.get('company_tel', '')
            parameter_dict['company_fax'] = request.values.get('company_fax', '')
            parameter_dict['network_address'] = request.values.get('network_address', '')
            parameter_dict['contacts'] = request.values.get('contacts', '')
            parameter_dict['telephone'] = request.values.get('telephone', '')
            parameter_dict['remarks'] = request.values.get('remarks', '')
            if parameter_dict['customer_code'] is u'':
                parameter_dict['customer_code'] = None

            if parameter_dict.get('customer_name') and parameter_dict.get('customer_type_id') and parameter_dict.get('contacts'):
                c_op = CustomerInfoOp()
                check_name = c_op.check_customer_only(customer_name=parameter_dict['customer_name'])
                if parameter_dict['customer_code']:
                    check_code = c_op.check_customer_only(customer_code=parameter_dict['customer_code'])
                    if check_code == ServiceCode.success:
                        raise CodeError(ServiceCode.params_error, msg=u'客户编码重复')
                        # result = {'code': ServiceCode.params_error, 'msg': '客户编码重复'}
                        # return tools.en_return_data(json.dumps(result))
                if check_name == ServiceCode.success:
                    raise CodeError(ServiceCode.params_error, msg=u'客户名重复')
                    # result = {'code': ServiceCode.params_error, 'msg': '客户名重复'}
                    # return tools.en_return_data(json.dumps(result))
                res = c_op.save_customer_info(parameter_dict)
                if res['code'] == ServiceCode.success:
                    result = {'code': ServiceCode.success, 'msg': '添加成功'}
                else:
                    result = {'code': ServiceCode.params_error, 'msg': '添加失败'}
                # return tools.en_return_data(json.dumps(result))
            else:
                result = {'code': ServiceCode.params_error, 'msg': '参数错误，客户姓名,客户类型,联系人必填'}
                # return tools.en_return_data(json.dumps(result))
        except CodeError as e:
            return_data = e.json_value()
        except Exception:
            SystemLog.pub_warninglog(traceback.format_exc())
            return_data = {'code': ServiceCode.service_exception, 'msg': u'服务器错误'}
        else:
            return_data = result
        finally:
            return tools.en_return_data(json.dumps(return_data))


class AddCustomerType(MethodView):
    @staticmethod
    def post():
        return_data = None
        try:
            customer_name = request.values.get('customer_name', '')
            if customer_name:
                c_op = CustomerInfoOp()
                res = c_op.check_customer_type_name(customer_name)
                if res == ServiceCode.success:
                    raise CodeError(ServiceCode.params_error, msg=u'客户类型名重复')
                    # result = {'code': ServiceCode.params_error, 'msg': u'客户类型名重复'}
                    # return tools.en_return_data(json.dumps(result))
                else:
                    customer_type_name = c_op.save_customer_type(customer_name)
                    if customer_type_name['code'] == ServiceCode.success:
                        result = {'code': ServiceCode.success, 'msg': '添加成功', 'data': customer_type_name['data']}
                    else:
                        result = {'code': ServiceCode.notfound, 'msg': '添加失败', 'data': ''}
            else:
                result = {'code': ServiceCode.params_error, 'msg': u'客户类型名不能为空'}

            # return tools.en_return_data(json.dumps(result))
        except CodeError as e:
            return_data = e.json_value()
        except Exception:
            SystemLog.pub_warninglog(traceback.format_exc())
            return_data = {'code': ServiceCode.service_exception, 'msg': u'服务器错误'}
        else:
            return_data = result
        finally:
            return tools.en_return_data(json.dumps(return_data))


class CheckCustomerType(MethodView):
    @staticmethod
    def post():
        return_data = None
        try:
            customer_type_name = request.values.get('customer_name', '')
            c_op = CustomerInfoOp()
            res = c_op.check_customer_type_name(customer_type_name)
            if res == ServiceCode.success:
                result = {'code': ServiceCode.notfound, 'msg': u'用户类型名重复'}
            else:
                result = {'code': ServiceCode.success, 'msg': u'用户类型名可用'}
            # return tools.en_return_data(json.dumps(result))
        except CodeError as e:
            return_data = e.json_value()
        except Exception:
            SystemLog.pub_warninglog(traceback.format_exc())
            return_data = {'code': ServiceCode.service_exception, 'msg': u'服务器错误'}
        else:
            return_data = result
        finally:
            return tools.en_return_data(json.dumps(return_data))


class CheckCustomerName(MethodView):
    @staticmethod
    def post():
        return_data = None
        try:
            customer_code = request.values.get('customer_code', '')
            customer_name = request.values.get('customer_name', '')
            customer_id = request.values.get('customer_id', 0, int)
            if customer_name is u'':
                raise CodeError(ServiceCode.notfound, msg=u'客户名称不能为空')
                # result = {'code': ServiceCode.notfound, 'msg': u'客户名称不能为空'}
                # return tools.en_return_data(json.dumps(result))
            msg = u''
            if customer_code:
                msg = u'客户编码重复'
            if customer_name:
                msg = u'客户名重复'
            c_op = CustomerInfoOp()
            res = c_op.check_customer_only(customer_name=customer_name, customer_code=customer_code, customer_id=customer_id)
            if res == ServiceCode.success:
                result = {'code': ServiceCode.notfound, 'msg': msg}
            else:
                result = {'code': ServiceCode.success, 'msg': u'可用'}
            # return tools.en_return_data(json.dumps(result))
        except CodeError as e:
            return_data = e.json_value()
        except Exception:
            SystemLog.pub_warninglog(traceback.format_exc())
            return_data = {'code': ServiceCode.service_exception, 'msg': u'服务器错误'}
        else:
            return_data = result
        finally:
            return tools.en_return_data(json.dumps(return_data))


class UpdateCustomerInfo(MethodView):
    @staticmethod
    def get():
        return_data = None
        result = {}
        try:
            result['is_type'] = 1
            customer_id = request.values.get('customer_id', 0, int)
            if customer_id:
                c_op = CustomerInfoOp()
                customer_infos = c_op.get_customer_id(customer_id)
                customer_type_infos = c_op.get_customer_type()

                if customer_infos['code'] == ServiceCode.success and customer_type_infos['code']:
                    result['data'] = customer_type_infos['data']
                    result['code'] = ServiceCode.success
                    result['msg'] = customer_infos['msg']
                    result['info_list'] = customer_infos['data']
                else:
                    result['info_list'] = []
                    result['data'] = []
                    result['code'] = ServiceCode.service_exception
                    result['msg'] = u'查询失败'

            else:
                result['msg'] = u'用户ID不能为空'
            # return tools.en_render_template('supplyChain/customers/newCustomers.html', result=json.dumps(result))
        except CodeError as e:
            return_data = e.json_value()
        except Exception:
            SystemLog.pub_warninglog(traceback.format_exc())
            return_data = {'code': ServiceCode.service_exception, 'msg': u'服务器错误'}
        else:
            return_data = result
        finally:
            return tools.en_render_template('/supplyChain/customers/newCustomers.html', result=json.dumps(return_data))

    @staticmethod
    def post():
        return_data = None
        result = {'code': ServiceCode.service_exception, 'msg': u'修改失败'}
        try:
            parameter_dict = dict()
            parameter_dict['customer_id'] = request.values.get('id', 0, int)
            parameter_dict['customer_name'] = request.values.get('customer_name', '')
            parameter_dict['customer_code'] = request.values.get('customer_code', None)
            parameter_dict['province'] = request.values.get('province', '')
            parameter_dict['city'] = request.values.get('city', '')
            parameter_dict['county'] = request.values.get('county', '')
            parameter_dict['address'] = request.values.get('address', '')
            parameter_dict['customer_type_id'] = request.values.get('customer_type_id', 0, int)
            parameter_dict['customer_type'] = request.values.get('customer_type', '')
            parameter_dict['company_tel'] = request.values.get('company_tel', '')
            parameter_dict['company_fax'] = request.values.get('company_fax', '')
            parameter_dict['network_address'] = request.values.get('network_address', '')
            parameter_dict['contacts'] = request.values.get('contacts', '')
            parameter_dict['telephone'] = request.values.get('telephone', '')
            parameter_dict['remarks'] = request.values.get('remarks', '')
            if parameter_dict['customer_id']:
                if parameter_dict['customer_code'] is u'':
                    parameter_dict['customer_code'] = None
                if parameter_dict.get('customer_name') and parameter_dict.get('customer_type_id') and parameter_dict.get('contacts'):
                    c_op = CustomerInfoOp()
                    check_name = c_op.check_customer_only(customer_name=parameter_dict['customer_name'],
                                                          customer_id=parameter_dict['customer_id'])
                    if parameter_dict['customer_code']:
                        check_code = c_op.check_customer_only(customer_code=parameter_dict['customer_code'],
                                                              customer_id=parameter_dict['customer_id'])
                        if check_code == ServiceCode.success:
                            raise CodeError(ServiceCode.params_error, msg=u"客户编码重复")
                            # result = {'code': ServiceCode.params_error, 'msg': '客户编码重复'}
                            # return tools.en_return_data(json.dumps(result))
                    if check_name == ServiceCode.success:
                        raise CodeError(ServiceCode.params_error, msg=u'客户名重复')
                        # result = {'code': ServiceCode.params_error, 'msg': '客户名重复'}
                        # return tools.en_return_data(json.dumps(result))
                    res = c_op.save_update_info(parameter_dict)
                    if res['code'] == ServiceCode.success:
                        result = {'code': ServiceCode.success, 'msg': '修改成功'}
                    else:
                        result = {'code': ServiceCode.params_error, 'msg': '修改失败'}
                    # return tools.en_return_data(json.dumps(result))
                else:
                    result = {'code': ServiceCode.params_error, 'msg': u'参数错误，客户姓名,客户类型,联系人必填'}
            else:
                result = {'code': ServiceCode.params_error, 'msg': u'修改失败,客户ID不能为空'}

            # return tools.en_return_data(json.dumps(result))
        except CodeError as e:
            return_data = e.json_value()
        except Exception:
            SystemLog.pub_warninglog(traceback.format_exc())
            return_data = {'code': ServiceCode.service_exception, 'msg': u'服务器错误'}
        else:
            return_data = result
        finally:
            return tools.en_return_data(json.dumps(return_data))


class DelCustomerInfo(MethodView):
    @staticmethod
    def post():
        return_data = None
        try:
            customer_id = request.values.get('customer_id', 0, int)
            if customer_id:
                c_op = CustomerInfoOp()
                res = c_op.del_customer_info(customer_id)
                if res['code'] == ServiceCode.success:
                    result = {'code': ServiceCode.success, 'msg': u'删除成功'}
                else:
                    result = {'code': res['code'], 'msg': res['msg']}
                # return tools.en_return_data(json.dumps(result))
            else:
                result = {'code': ServiceCode.service_exception, 'msg': u'用户ID不能为空'}
        except CodeError as e:
            return_data = e.json_value()
        except Exception:
            SystemLog.pub_warninglog(traceback.format_exc())
            return_data = {'code': ServiceCode.service_exception, 'msg': u'服务器错误'}
        else:
            return_data = result
        finally:
            return tools.en_return_data(json.dumps(return_data))


class Customer(MethodView):
    """
     客户二级导航
    """
    @staticmethod
    def get():
        return ""

add_url.add_url(u'客户',
                "baseinfo.index",
                add_url.TYPE_ENTRY,
                baseinfo_prefix,
                baseinfo,
                "/customer_info/",
                "customer",
                Customer.as_view('customer'),
                methods=['POST', 'GET'])

add_url.add_url(u'客户信息',
                "baseinfo.customer",
                add_url.TYPE_ENTRY,
                baseinfo_prefix,
                baseinfo,
                "/show_customer_info/",
                "CustomerInfo",
                CustomerInfo.as_view('CustomerInfo'),
                methods=['POST', 'GET'])

add_url.add_url(u'新增客户',
                "baseinfo.CustomerInfo",
                add_url.TYPE_FUNC,
                baseinfo_prefix,
                baseinfo,
                "/add_customer_info/",
                "AddCustomerInfo",
                AddCustomerInfo.as_view("AddCustomerInfo"),
                methods=['POST', 'GET'])

add_url.add_url(u'添加客户类型',
                "baseinfo.AddCustomerInfo",
                add_url.TYPE_FUNC,
                baseinfo_prefix,
                baseinfo,
                "/add_customer_type/",
                "AddCustomerType",
                AddCustomerType.as_view("AddCustomerType"),
                methods=['POST', 'GET'])

add_url.add_url(u'检测客户类型名唯一',
                "baseinfo.AddCustomerInfo",
                add_url.TYPE_FUNC,
                baseinfo_prefix,
                baseinfo,
                "/check_customer_type/",
                "CheckCustomerType",
                CheckCustomerType.as_view("CheckCustomerType"),
                methods=['POST', 'GET'])

add_url.add_url(u'检测客户姓名/客户编码唯一',
                "baseinfo.AddCustomerInfo",
                add_url.TYPE_FUNC,
                baseinfo_prefix,
                baseinfo,
                "/check_customer_name/",
                "CheckCustomerName",
                CheckCustomerName.as_view("CheckCustomerName"),
                methods=['POST', 'GET'])

add_url.add_url(u'修改客户信息',
                "baseinfo.CustomerInfo",
                add_url.TYPE_FUNC,
                baseinfo_prefix,
                baseinfo,
                "/update_customer_info/",
                "UpdateCustomerInfo",
                UpdateCustomerInfo.as_view('UpdateCustomerInfo'),
                methods=['POST', 'GET'])

add_url.add_url(u'删除客户',
                "baseinfo.CustomerInfo",
                add_url.TYPE_FUNC,
                baseinfo_prefix,
                baseinfo,
                "/del_customer_info/",
                "DelCustomerInfo",
                DelCustomerInfo.as_view("DelCustomerInfo"),
                methods=['POST', 'GET'])