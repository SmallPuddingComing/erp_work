#!/usr/bin/python
# -*- coding:utf-8 -*-
#    Copyright(c) 2015-2016 JmGo Company
#    All rights reserved.
#
#    文件名 : verification.py
#    作者   : WangYi
#  电子邮箱 : ywang@jmgo.com
#    日期   : 2017/1/5 18:13
#
#     描述  : 调拨单内校验的视图
#
from flask.views import MethodView
from flask import jsonify, request
import traceback
from config.service_config.returncode import ServiceCode
from public.logger.syslog import SystemLog
from public.exception.custom_exception import CodeError
from public.function import tools
from control_center.warehouse_manage import warehouse_manage, warehouse_manage_prefix
from control_center.admin import add_url


def main(m_request):
    from control_center.warehouse_manage.warehouse_allocation_manage.control.allocation_op import AllocationOp

    op = AllocationOp()
    invoice_number = m_request.values.get('invoice_number', None, str)
    if not invoice_number:
        raise CodeError(ServiceCode.params_error, u'单号不能为空')
    if op.check_invoice_number(invoice_number):
        raise CodeError(ServiceCode.check_error, u'单号已被使用')
    return {'code': ServiceCode.success}

class CreateInvoiceVerification(MethodView):
    def get(self):
        return_date = None
        try:
            return_date = main(request)
        except CodeError as e:
            return_date = e.json_value()
        except Exception:
            SystemLog.pub_warninglog(traceback.format_exc())
            return_date = {'code': ServiceCode.params_error, 'msg': u'服务器错误'}
        finally:
            return tools.en_return_data(jsonify(return_date))


class ModifyInvoiceVerification(MethodView):
    def get(self):
        return_date = None
        try:
            return_date = main(request)
        except CodeError as e:
            return_date = e.json_value()
        except Exception:
            SystemLog.pub_warninglog(traceback.format_exc())
            return_date = {'code': ServiceCode.params_error, 'msg': u'服务器错误'}
        finally:
            return tools.en_return_data(jsonify(return_date))


class CopyInvoiceVerification(MethodView):
    def get(self):
        return_date = None
        try:
            return_date = main(request)
        except CodeError as e:
            return_date = e.json_value()
        except Exception:
            SystemLog.pub_warninglog(traceback.format_exc())
            return_date = {'code': ServiceCode.params_error, 'msg': u'服务器错误'}
        finally:
            return tools.en_return_data(jsonify(return_date))


add_url.add_url(u'新建调拨单校验单据号',
                'warehouse_manage.allocation_create_invoice',
                add_url.TYPE_FUNC,
                warehouse_manage_prefix,
                warehouse_manage,
                '/warehouse_manage/allocation/allocation_create_invoice/verification/',
                'allocation_create_invoice_verification',
                CreateInvoiceVerification.as_view('allocation_create_invoice_verification'),
                methods=['GET'])
add_url.add_url(u'修改调拨单校验单据号',
                'warehouse_manage.allocation_modify_invoice',
                add_url.TYPE_FUNC,
                warehouse_manage_prefix,
                warehouse_manage,
                '/warehouse_manage/allocation/allocation_modify_invoice/verification/',
                'allocation_modify_invoice_verification',
                ModifyInvoiceVerification.as_view('allocation_modify_invoice_verification'),
                methods=['GET'])
add_url.add_url(u'复制调拨单校验单据号',
                'warehouse_manage.allocation_copy_invoice',
                add_url.TYPE_FUNC,
                warehouse_manage_prefix,
                warehouse_manage,
                '/warehouse_manage/allocation/allocation_copy_invoice/verification/',
                'allocation_copy_invoice_verification',
                CopyInvoiceVerification.as_view('allocation_copy_invoice_verification'),
                methods=['GET'])