#!/usr/bin/python
# -*- coding:utf-8 -*-
#    Copyright(c) 2015-2016 JmGo Company
#    All rights reserved.
#
#    文件名 : person.py
#    作者   : WangYi
#  电子邮箱 : ywang@jmgo.com
#    日期   : 2017/1/5 11:26
#
#     描述  : 调拨单中的员工信息
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


def main():
    from data_mode.user_center.control.mixOp import MixUserCenterOp
    op = MixUserCenterOp()
    row, total = op.get_all_person_info()
    data = {
        'code': ServiceCode.success,
        'rows': row,
        'total': total
    }
    return data

class CreateInvoicePersonInformation(MethodView):
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


class ModifyInvoicePersonInformation(MethodView):
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


class CopyInvoicePersonInformation(MethodView):
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


add_url.add_url(u'新建调拨单获取员工信息',
                'warehouse_manage.allocation_create_invoice',
                add_url.TYPE_FUNC,
                warehouse_manage_prefix,
                warehouse_manage,
                '/warehouse_manage/allocation/allocation_create_invoice/person/',
                'allocation_create_invoice_person',
                CreateInvoicePersonInformation.as_view('allocation_create_invoice_person'),
                methods=['GET'])
add_url.add_url(u'修改调拨单获取员工信息',
                'warehouse_manage.allocation_modify_invoice',
                add_url.TYPE_FUNC,
                warehouse_manage_prefix,
                warehouse_manage,
                '/warehouse_manage/allocation/allocation_modify_invoice/person/',
                'allocation_modify_invoice_person',
                ModifyInvoicePersonInformation.as_view('allocation_modify_invoice_person'),
                methods=['GET'])
add_url.add_url(u'复制调拨单获取员工信息',
                'warehouse_manage.allocation_copy_invoice',
                add_url.TYPE_FUNC,
                warehouse_manage_prefix,
                warehouse_manage,
                '/warehouse_manage/allocation/allocation_copy_invoice/person/',
                'allocation_copy_invoice_person',
                CopyInvoicePersonInformation.as_view('allocation_copy_invoice_person'),
                methods=['GET'])
