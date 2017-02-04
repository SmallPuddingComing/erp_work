#!/usr/bin/python
# -*- coding:utf-8 -*-
#    Copyright(c) 2015-2016 JmGo Company
#    All rights reserved.
#
#    文件名 : warehouse.py
#    作者   : WangYi
#  电子邮箱 : ywang@jmgo.com
#    日期   : 2017/1/5 16:49
#
#     描述  : 调拨当中仓库列表
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
    from control_center.supply_chain.material_warehosue.control.material_warehouse_mix_op import GetWarehouseInfo
    op = GetWarehouseInfo()
    total, data = op.get_warehouse_all()
    # 重构
    new_data = []
    for element in data:
        new_data.append({
            'warehouse_id': element['warehouse_id'],
            'warehouse_code': element['warehouse_code'],
            'warehouse_name': element['warehouse_name'],
            'warehouse_type': op.get_warehouse_type_by_id(element['warehouse_type_id']),
            'contacts': element['contacts'],
            'prov': element['prov'],
            'city': element['city'],
            'region': element['region'],
            'address': element['address']
        })
    return {
        'code': ServiceCode.success,
        'rows': new_data,
        'total': total
    }


class CreateInvoiceWarehouseList(MethodView):
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


class ModifyInvoiceWarehouseList(MethodView):
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


class CopyInvoiceWarehouseList(MethodView):
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


add_url.add_url(u'新建调拨单获取仓库信息',
                'warehouse_manage.allocation_create_invoice',
                add_url.TYPE_FUNC,
                warehouse_manage_prefix,
                warehouse_manage,
                '/warehouse_manage/allocation/allocation_create_invoice/warehouse/',
                'allocation_create_invoice_warehouse',
                CreateInvoiceWarehouseList.as_view('allocation_create_invoice_warehouse'),
                methods=['GET'])
add_url.add_url(u'修改调拨单获取仓库信息',
                'warehouse_manage.allocation_modify_invoice',
                add_url.TYPE_FUNC,
                warehouse_manage_prefix,
                warehouse_manage,
                '/warehouse_manage/allocation/allocation_modify_invoice/warehouse/',
                'allocation_modify_invoice_warehouse',
                ModifyInvoiceWarehouseList.as_view('allocation_modify_invoice_warehouse'),
                methods=['GET'])
add_url.add_url(u'复制调拨单获取仓库信息',
                'warehouse_manage.allocation_copy_invoice',
                add_url.TYPE_FUNC,
                warehouse_manage_prefix,
                warehouse_manage,
                '/warehouse_manage/allocation/allocation_copy_invoice/warehouse/',
                'allocation_copy_invoice_warehouse',
                CopyInvoiceWarehouseList.as_view('allocation_copy_invoice_warehouse'),
                methods=['GET'])