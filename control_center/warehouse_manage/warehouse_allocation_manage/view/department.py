#!/usr/bin/python
# -*- coding:utf-8 -*-
#    Copyright(c) 2015-2016 JmGo Company
#    All rights reserved.
#
#    文件名 : department.py
#    作者   : WangYi
#  电子邮箱 : ywang@jmgo.com
#    日期   : 2017/1/5 16:53
#
#     描述  : 调拨单中部门列表
#
from flask.views import MethodView
from flask import request, jsonify
import traceback
from config.service_config.returncode import ServiceCode
from public.logger.syslog import SystemLog
from public.exception.custom_exception import CodeError
from public.function import tools
from control_center.warehouse_manage import warehouse_manage, warehouse_manage_prefix
from control_center.admin import add_url
from data_mode.user_center.control.mixOp import MixUserCenterOp


def main():
    "通用处理, 返回return_data"
    op = MixUserCenterOp()
    return_date = {
        'code': ServiceCode.success,
        'msg': u'成功',
        'rows': op.get_departments_info()
    }
    return return_date


class CreateInvoiceDepartmentList(MethodView):
    def get(self):
        return_date = None
        try:
            return_date = main()
        except CodeError as e:
            return_date = e.json_value()
        except Exception:
            SystemLog.pub_warninglog(traceback.format_exc())
            return_date = {'code': ServiceCode.params_error, 'msg': u'服务器错误'}
        finally:
            return tools.en_return_data(jsonify(return_date))


class ModifyInvoiceDepartmentList(MethodView):
    def get(self):
        return_date = None
        try:
            return_date = main()
        except CodeError as e:
            return_date = e.json_value()
        except Exception:
            SystemLog.pub_warninglog(traceback.format_exc())
            return_date = {'code': ServiceCode.params_error, 'msg': u'服务器错误'}
        finally:
            return tools.en_return_data(jsonify(return_date))


class CopyInvoiceDepartmentList(MethodView):
    def get(self):
        return_date = None
        try:
            return_date = main()
        except CodeError as e:
            return_date = e.json_value()
        except Exception:
            SystemLog.pub_warninglog(traceback.format_exc())
            return_date = {'code': ServiceCode.params_error, 'msg': u'服务器错误'}
        finally:
            return tools.en_return_data(jsonify(return_date))


add_url.add_url(u'新建调拨单获取部门信息',
                'warehouse_manage.allocation_create_invoice',
                add_url.TYPE_FUNC,
                warehouse_manage_prefix,
                warehouse_manage,
                '/warehouse_manage/allocation/allocation_create_invoice/department/',
                'allocation_create_invoice_department',
                CreateInvoiceDepartmentList.as_view('allocation_create_invoice_department'),
                methods=['GET'])
add_url.add_url(u'修改调拨单获取部门信息',
                'warehouse_manage.allocation_modify_invoice',
                add_url.TYPE_FUNC,
                warehouse_manage_prefix,
                warehouse_manage,
                '/warehouse_manage/allocation/allocation_modify_invoice/department/',
                'allocation_modify_invoice_department',
                ModifyInvoiceDepartmentList.as_view('allocation_modify_invoice_department'),
                methods=['GET'])
add_url.add_url(u'复制调拨单获取部门信息',
                'warehouse_manage.allocation_copy_invoice',
                add_url.TYPE_FUNC,
                warehouse_manage_prefix,
                warehouse_manage,
                '/warehouse_manage/allocation/allocation_copy_invoice/department/',
                'allocation_copy_invoice_department',
                CopyInvoiceDepartmentList.as_view('allocation_copy_invoice_department'),
                methods=['GET'])