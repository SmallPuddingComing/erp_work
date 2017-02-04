#!/usr/bin/python
# -*- coding:utf-8 -*-
#    Copyright(c) 2015-2016 JmGo Company
#    All rights reserved.
#
#    文件名 : invoice_operate_record_view.py
#    作者   : ChengQian
#  电子邮箱 : qcheng@jmgo.com
#    日期   : 2017/1/13 17:26
#
#     描述  :
#
import datetime
import traceback

from flask.views import MethodView
from flask import request
import json
from flask import session

from config.service_config.returncode import ServiceCode
from public.logger.syslog import SystemLog
from public.exception.custom_exception import CodeError
from public.function import tools
from control_center.warehouse_manage import warehouse_manage, warehouse_manage_prefix
from control_center.admin import add_url

class SellOutInvoiceRecord(MethodView):
    @staticmethod
    def post():
            return_data = None
            from control_center.warehouse_manage.warehouse_out_manage.control.sell_warehouse_out_op import SellWarehousOutOp
            sell_op = SellWarehousOutOp()
            try:
                invoice_number = request.values.get("invoice_number", None, str)
                page = int(request.values.get("page", 1, int))
                pagecount = int(request.values.get("pagecount", 5, int))
                if invoice_number is None:
                    raise CodeError(ServiceCode.service_exception, msg=u"单据单号参数错误")
                # 根据单据单号获取单据操作记录
                total, record_list = sell_op.get_invoice_operate_record(invoice_number, page, pagecount)
            except CodeError as e:
                return_data = e.json_value()
            except Exception:
                SystemLog.pub_warninglog(traceback.format_exc())
                return_data = {'code': ServiceCode.service_exception, 'msg': u'服务器错误'}
            else:
                return_data = {
                    'code': ServiceCode.success,
                    'total': total,
                    'rows': record_list
                }
            finally:
                if return_data.get('code', ServiceCode.service_exception) != ServiceCode.success:
                    return tools.en_render_template('public/error.html',
                                                    code_msg=return_data.get('msg'))
                else:
                    return tools.en_return_data(json.dumps(return_data))


class OutsourceOutInvoiceRecord(MethodView):
    @staticmethod
    def post():
            return_data = None
            from control_center.warehouse_manage.warehouse_out_manage.control.outsource_warehouse_out_op import OutsourceWarehousOutOp
            outsource_op = OutsourceWarehousOutOp()
            try:
                invoice_number = request.values.get("invoice_number", None, str)
                page = int(request.values.get("page", 1, int))
                pagecount = int(request.values.get("pagecount", 5, int))
                if invoice_number is None:
                    raise CodeError(ServiceCode.service_exception, msg=u"单据单号参数错误")
                # 根据单据单号获取单据操作记录
                total, record_list = outsource_op.get_invoice_operate_record(invoice_number, page, pagecount)
            except CodeError as e:
                print e
                return_data = e.json_value()
            except Exception as e:
                print e
                SystemLog.pub_warninglog(traceback.format_exc())
                return_data = {'code': ServiceCode.service_exception, 'msg': u'服务器错误'}
            else:
                return_data = {
                    'code': ServiceCode.success,
                    'total': total,
                    'rows': record_list
                }
            finally:
                if return_data.get('code', ServiceCode.service_exception) != ServiceCode.success:
                    return tools.en_render_template('public/error.html',
                                                    code_msg=return_data.get('msg'))
                else:
                    return tools.en_return_data(json.dumps(return_data))


class OtherOutInvoiceRecord(MethodView):
    @staticmethod
    def post():
            return_data = None
            from control_center.warehouse_manage.warehouse_out_manage.control.other_warehouse_out_op import OtherWarehousOutOp
            other_op = OtherWarehousOutOp()
            try:
                invoice_number = request.values.get("invoice_number", None, str)
                page = int(request.values.get("page", 1, int))
                pagecount = int(request.values.get("pagecount", 5, int))
                if invoice_number is None:
                    raise CodeError(ServiceCode.service_exception, msg=u"单据单号参数错误")
                # 根据单据单号获取单据操作记录
                total, record_list = other_op.get_invoice_operate_record(invoice_number, page, pagecount)
            except CodeError as e:
                return_data = e.json_value()
            except Exception:
                SystemLog.pub_warninglog(traceback.format_exc())
                return_data = {'code': ServiceCode.service_exception, 'msg': u'服务器错误'}
            else:
                return_data = {
                    'code': ServiceCode.success,
                    'total': total,
                    'rows': record_list
                }
            finally:
                if return_data.get('code', ServiceCode.service_exception) != ServiceCode.success:
                    return tools.en_render_template('public/error.html',
                                                    code_msg=return_data.get('msg'))
                else:
                    return tools.en_return_data(json.dumps(return_data))

add_url.add_url(u'销售出库单据操作记录',
                'warehouse_manage.sell_warehouse_out',
                add_url.TYPE_FEATURE,
                warehouse_manage_prefix,
                warehouse_manage,
                '/warehouse_manage/warehouse_out/sell_warehouse_out/modify_warehouse_order/operate_record/',
                'sell_warehouse_invoice_record',
                SellOutInvoiceRecord.as_view('sell_warehouse_invoice_record'),
                methods=['POST'])

add_url.add_url(u'委外加工领料单据操作记录',
                'warehouse_manage.outsourcing_picking',
                add_url.TYPE_FEATURE,
                warehouse_manage_prefix,
                warehouse_manage,
                '/warehouse_manage/warehouse_out/outsource_warehouse_out/modify_warehouse_order/operate_record/',
                'outsource_warehouse_invoice_record',
                OutsourceOutInvoiceRecord.as_view('outsource_warehouse_invoice_record'),
                methods=['POST'])

add_url.add_url(u'其他出库单据操作记录',
                'warehouse_manage.others_warehouse_out',
                add_url.TYPE_FEATURE,
                warehouse_manage_prefix,
                warehouse_manage,
                '/warehouse_manage/warehouse_out/other_warehouse_out/modify_warehouse_order/operate_record/',
                'others_warehouse_invoice_record',
                OtherOutInvoiceRecord.as_view('others_warehouse_invoice_record'),
                methods=['POST'])