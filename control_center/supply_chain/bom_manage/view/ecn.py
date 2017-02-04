#!/usr/bin/python
# -*- coding:utf-8 -*-
#    Copyright(c) 2015-2016 JmGo Company
#    All rights reserved.
#
#    文件名 : ecn.py
#    作者   : WangYi
#  电子邮箱 : ywang@jmgo.com
#    日期   : 2016/11/25 15:33
#
#     描述  : ECN相关页面
#           1.ECN管理
#           2.ECN明细
#           3.新增ECN
#
import traceback
from flask.views import MethodView
from flask import json, request
from public.logger.syslog import SystemLog
from public.exception.custom_exception import CodeError
from public.function import tools
from config.service_config.returncode import ServiceCode
from control_center.admin import add_url
from control_center.supply_chain import baseinfo, baseinfo_prefix
from control_center.supply_chain.bom_manage.control.ecn_op import EcnManageOp


class EcnManageView(MethodView):
    """
    ECN管理页面
    """
    @staticmethod
    def get():
        try:
            page = request.values.get('page', 1, int)
            page_num = request.values.get('page_num', 10, int)
            ecn_code = request.values.get('ecn_code', None, str)
            principal_id = request.values.get('principal_id', None, int)

            # tjx 2016年12月5日14:34:39
            op = EcnManageOp()
            if ecn_code is None or ecn_code is "" or ecn_code is u"":
                if principal_id is None or principal_id is "" or principal_id is u"":
                    r_data, total = op.get_ecn_info(page, page_num)
                else:
                    r_data, total = op.get_ecn_info(page, page_num, principal_id=int(principal_id))
            else:
                if principal_id is None or principal_id is "" or principal_id is u"":
                    r_data, total = op.get_ecn_info(page, page_num, e_code=ecn_code)
                else:
                    r_data, total = op.get_ecn_info(page, page_num, e_code=ecn_code, principal_id=int(principal_id))
            prin_list = op.get_principal_info()

            result = {
                'code': ServiceCode.success,
                'total': total,
                'data': r_data,
                "prin_list": prin_list
            }
        except CodeError as e:
            SystemLog.pub_warninglog(traceback.format_exc())
            return tools.en_return_data(json.dumps(e.json_value()))
        except Exception:
            SystemLog.pub_warninglog(traceback.format_exc())
            if request.is_xhr:
                return tools.en_return_data(json.dumps({'code': ServiceCode.exception_op, 'msg': u'服务器报错'}))
            else:
                raise
        else:
            if not request.is_xhr:  # 表示为ajax请求
                return tools.en_render_template(
                    'supplyChain/BOM/ECN_manager.html', result=json.dumps(result))
            else:
                return tools.en_return_data(json.dumps(result))


class EcnDetailView(MethodView):
    """
    ECN管理明细
    """
    @staticmethod
    def get():
        try:
            ecn_id = request.values.get('ecn_id', None, int)

            if ecn_id is None:
                raise CodeError(ServiceCode.params_error, u'请上送ECN相关参数')
            op = EcnManageOp()
            r_data = op.get_ecn_detail_info(ecn_id)

        except CodeError as e:
            SystemLog.pub_warninglog(traceback.format_exc())
            return tools.en_return_data(json.dumps(e.json_value()))
        except Exception:
            SystemLog.pub_warninglog(traceback.format_exc())
            raise
        else:
            return tools.en_render_template(
                'supplyChain/BOM/ECN_detail.html', result=json.dumps(r_data))

    @staticmethod
    def post():
        try:
            ecn_id = request.values.get('ecn_id', None, int)
            bom_id = request.values.get('bom_id', None, int)
            search_type = request.values.get('search_type', None, int)
            search_value = request.values.get('search_value', '', str)
            page = request.values.get('page', 1, int)
            page_num = request.values.get('page_num', 10, int)

            if ecn_id is None:
                raise CodeError(ServiceCode.params_error, u'缺少ECN的相关参数')
            elif bom_id is None:
                raise CodeError(ServiceCode.params_error, u'缺少BOM的相关参数')
            op = EcnManageOp()
            r_data, total = op.get_ecn_detail_search(page, page_num, ecn_id, bom_id,
                                                     key=search_type, value=search_value)

            result = {
                'code': ServiceCode.success,
                'bom_id': bom_id,
                'total': total,
                'rows': r_data
            }
        except CodeError as e:
            SystemLog.pub_warninglog(traceback.format_exc())
            return tools.en_return_data(json.dumps(e.json_value()))
        else:
            return tools.en_return_data(json.dumps(result))


class EcnCreateView(MethodView):
    @staticmethod
    def get():

        op = EcnManageOp()
        r_data = op.get_create_ecn_info()

        return tools.en_render_template('supplyChain/BOM/ECN_new.html', result=json.dumps(r_data))


class EcnCreateSelectBom(MethodView):
    """
    ECN新建--选择BOM
    """
    @staticmethod
    def get():
        return_data = None
        try:
            page = request.values.get('page', 1, int)
            page_num = request.values.get('page_num', 10, int)
            search_type = request.values.get('search_type', None, int)
            search_value = request.values.get('search_value', '', str)
            exist_bom_id_list = request.values.get("exist_bom_id_list", None)

            exist_bom_id_list = json.loads(exist_bom_id_list)
            op = EcnManageOp()
            r_data, total = op.get_bom_info(page, page_num, key=search_type,
                                            value=search_value, exist_bom_id_list=exist_bom_id_list)

            return_data = {
                'code': ServiceCode.success,
                'msg': u"服务器成功",
                'total': total,
                'rows': r_data
            }
        except CodeError as e:
            SystemLog.pub_warninglog(traceback.format_exc())
            return_data = e.json_value()
        except Exception:
            SystemLog.pub_warninglog(traceback.format_exc())
            return_data = {'code': ServiceCode.exception_op, 'msg': u'服务器错误'}
        finally:
            return tools.en_return_data(json.dumps(return_data))


class EcnCreateGetMaterial(MethodView):
    """
    ECN新建--获取物料信息
    """
    @staticmethod
    def post():
        return_data = None
        try:
            bom_id = request.values.get('bom_id', None, int)
            exist_material_id_list = request.values.get('exist_material_id_list', None)
            exist_material_id_list = json.loads(exist_material_id_list)
            page = request.values.get('page', 1, int)
            page_num = request.values.get('page_num', 10, int)
            search_type = request.values.get('search_type', None, int)
            search_value = request.values.get('search_value', '', str)
            function_type = request.values.get('function_type', None, int)

            if bom_id is None:
                raise CodeError(ServiceCode.params_error, u'缺少BOM相关参数')

            if function_type is None:
                raise CodeError(ServiceCode.params_error, u'请上送功能参数')
            elif function_type > 2 or function_type < 0:
                raise CodeError(ServiceCode.params_error, u'上送的功能参数值错误')
            op = EcnManageOp()
            r_data, total = op.get_material_info(page, page_num, bom_id, exist_material_id_list, function_type,
                                                 key=search_type, value=search_value)
            return_data = {
                'code': ServiceCode.success,
                'msg': u"服务器成功",
                'total': total,
                'rows': r_data
            }
        except CodeError as e:
            return_data = e.json_value()
        except Exception:
            SystemLog.pub_warninglog(traceback.format_exc())
            return_data = {'code': ServiceCode.exception_op, 'msg': u'服务器错误'}
        finally:
            return tools.en_return_data(json.dumps(return_data))


class EcnCreateSave(MethodView):
    """
    ECN新建--保存
    """
    @staticmethod
    def post():
        return_data = None
        try:
            print "************EcnCreateSave***********"
            ecn_info = dict()
            ecn_info["ecn_code"] = request.values.get("ecn_code", None, str)
            ecn_info["create_time"] = request.values.get("create_time", None, str)
            ecn_info["create_user"] = request.values.get("create_user", None, str)
            ecn_info["change_reason"] = request.values.get("change_reason", None, str)
            principal_id_list = request.values.get("principal_id_list", None)

            principal_id_list = json.loads(principal_id_list)
            if principal_id_list is None or not len(principal_id_list):
                raise CodeError(ServiceCode.service_exception, u"负责人参数非法")

            data = request.values.get("data", None)
            data = json.loads(data)
            if data is None or not len(data):
                raise CodeError(ServiceCode.service_exception, u"data 参数非法")
            op = EcnManageOp()
            op.save_ecn_info(ecn_info, principal_id_list, data)

        except CodeError as e:
            print traceback.format_exc()
            SystemLog.pub_warninglog(traceback.format_exc())
            return_data = e.json_value()
        except Exception:
            print traceback.format_exc()
            SystemLog.pub_warninglog(traceback.format_exc())
            return_data = {'code': ServiceCode.exception_op, 'msg': u'服务器错误'}
        else:
            return_data = {'code': ServiceCode.success, 'msg': u'保存成功'}
        finally:
            return tools.en_return_data(json.dumps(return_data))


add_url.add_url(u'ECN管理',
                'baseinfo.BomManage',
                add_url.TYPE_ENTRY,
                baseinfo_prefix,
                baseinfo,
                '/ecn_manage/',
                'EcnManageView',
                EcnManageView.as_view('EcnManageView'),
                20,
                methods=['GET', 'POST'])


add_url.add_url(u'ECN明细',
                'baseinfo.EcnManageView',
                add_url.TYPE_FEATURE,
                baseinfo_prefix,
                baseinfo,
                '/ecn_detail/',
                'EcnDetailView',
                EcnDetailView.as_view('EcnDetailView'),
                methods=['GET', 'POST'])

add_url.add_url(u'新建ECN',
                'baseinfo.EcnManageView',
                add_url.TYPE_FEATURE,
                baseinfo_prefix,
                baseinfo,
                '/ecn_create/',
                'EcnCreateView',
                EcnCreateView.as_view('EcnCreateView'),
                methods=['GET', 'POST'])

add_url.add_url(u'新建ECN-选择BOM',
                'baseinfo.EcnCreateView',
                add_url.TYPE_FEATURE,
                baseinfo_prefix,
                baseinfo,
                '/ecn_create_select_bom/',
                'EcnCreate_select_bom',
                EcnCreateSelectBom.as_view('EcnCreate_select_bom'),
                methods=['GET']
                )

add_url.add_url(u'ECN新建-获取物料信息',
                'baseinfo.EcnCreateView',
                add_url.TYPE_FEATURE,
                baseinfo_prefix,
                baseinfo,
                '/ecn_create_get_material/',
                'EcnCreate_get_material',
                EcnCreateGetMaterial.as_view('EcnCreate_get_material'),
                methods=['POST'])

add_url.add_url(u'ECN新建保存',
                'baseinfo.EcnCreateView',
                add_url.TYPE_FUNC,
                baseinfo_prefix,
                baseinfo,
                '/ecn_create_save/',
                'EcnCreateSave',
                EcnCreateSave.as_view('EcnCreateSave'),
                methods=['POST'])
