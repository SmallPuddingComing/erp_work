#!/usr/bin/python
# -*- coding:utf-8 -*-
#    Copyright(c) 2015-2016 JmGo Company
#    All rights reserved.
#
#    文件名 : inventory.py
#    作者   : WangYi
#  电子邮箱 : ywang@jmgo.com
#    日期   : 2017/1/5 17:00
#
#     描述  : 调拨单获取即时库存
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


def main(m_request):
    from data_mode.erp_supply.base_op.warehouse_manage_op.inventory_op import pub_get_inventory_by_list
    import json
    m_list_temp = m_request.values.get('datas_list', None)
    if m_list_temp is None:
        raise CodeError(ServiceCode.params_error, u'请上送查询库存参数列表')

    m_list = json.loads(m_list_temp)
    if not len(m_list):
        raise CodeError(ServiceCode.params_error, u'查询即时库存参数列表不能为空')

    return pub_get_inventory_by_list(m_list)


class CreateInvoiceInventory(MethodView):
    def post(self):
        return_date = None
        try:
            return_date = {
                'code': ServiceCode.success,
                'msg': u'成功',
                'rows': main(request)
            }
        except CodeError as e:
            return_date = e.json_value()
        except Exception:
            SystemLog.pub_warninglog(traceback.format_exc())
            return_date = {'code': ServiceCode.params_error, 'msg': u'服务器错误'}
        finally:
            return tools.en_return_data(jsonify(return_date))


class ModifyInvoiceInventory(MethodView):
    def post(self):
        return_date = None
        try:
            return_date = {
                'code': ServiceCode.success,
                'msg': u'成功',
                'rows': main(request)
            }
        except CodeError as e:
            return_date = e.json_value()
        except Exception:
            SystemLog.pub_warninglog(traceback.format_exc())
            return_date = {'code': ServiceCode.params_error, 'msg': u'服务器错误'}
        finally:
            return tools.en_return_data(jsonify(return_date))


class CopyInvoiceInventory(MethodView):
    def post(self):
        return_date = None
        try:
            return_date = {
                'code': ServiceCode.success,
                'msg': u'成功',
                'rows': main(request)
            }
        except CodeError as e:
            return_date = e.json_value()
        except Exception:
            SystemLog.pub_warninglog(traceback.format_exc())
            return_date = {'code': ServiceCode.params_error, 'msg': u'服务器错误'}
        finally:
            return tools.en_return_data(jsonify(return_date))


add_url.add_url(u'新建调拨单获取即时库存',
                'warehouse_manage.allocation_create_invoice',
                add_url.TYPE_FUNC,
                warehouse_manage_prefix,
                warehouse_manage,
                '/warehouse_manage/allocation/allocation_create_invoice/inventory/',
                'allocation_create_invoice_inventory',
                CreateInvoiceInventory.as_view('allocation_create_invoice_inventory'),
                methods=['POST'])
add_url.add_url(u'修改调拨单获取即时库存',
                'warehouse_manage.allocation_modify_invoice',
                add_url.TYPE_FUNC,
                warehouse_manage_prefix,
                warehouse_manage,
                '/warehouse_manage/allocation/allocation_modify_invoice/inventory/',
                'allocation_modify_invoice_inventory',
                ModifyInvoiceInventory.as_view('allocation_modify_invoice_inventory'),
                methods=['POST'])
add_url.add_url(u'复制调拨单获取即时库存',
                'warehouse_manage.allocation_copy_invoice',
                add_url.TYPE_FUNC,
                warehouse_manage_prefix,
                warehouse_manage,
                '/warehouse_manage/allocation/allocation_copy_invoice/inventory/',
                'allocation_copy_invoice_inventory',
                CopyInvoiceInventory.as_view('allocation_copy_invoice_inventory'),
                methods=['POST'])