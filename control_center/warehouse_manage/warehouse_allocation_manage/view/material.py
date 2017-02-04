#!/usr/bin/python
# -*- coding:utf-8 -*-
#    Copyright(c) 2015-2016 JmGo Company
#    All rights reserved.
#
#    文件名 : material.py
#    作者   : WangYi
#  电子邮箱 : ywang@jmgo.com
#    日期   : 2017/1/5 14:34
#
#     描述  : 调拨单中获取物料信息
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
    from data_mode.erp_supply.base_op.material_op.baseinfo_op import Baseinfo_Op
    from data_mode.erp_supply.base_op.material_op.attribute_op import Attribute_Op
    from config.share.share_define import SupplyAttr
    op = Baseinfo_Op()
    total, material_datas =  op.get_all_material_info()
    # 重构
    new_material_datas = []
    for element in material_datas:
        new_material_datas.append({
            'material_id': element['material_id'],
            'material_code': element['material_code'],
            'material_name': element['material_name'],
            'specification_model': element['specification_model'],
            'unit': element['unit'],
            'base_attr': element['base_attr'],
            'base_attr_type': element['base_attr_type']
        })
    op = Attribute_Op()
    material_attr_datas = op.get_material_attribute(SupplyAttr.MATERIAL_ATTRIBUTE_TYPE)
    data = {
        'code': ServiceCode.success,
        'msg': u'成功',
        'material_datas': new_material_datas,
        'material_attr_datas': material_attr_datas,
        'total': total
    }
    return data


class CreateInvoiceMaterialInfo(MethodView):
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


class ModifyInvoiceMaterialInfo(MethodView):
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


class CopyInvoiceMaterialInfo(MethodView):
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


add_url.add_url(u'新建调拨单获取物料信息',
                'warehouse_manage.allocation_create_invoice',
                add_url.TYPE_FUNC,
                warehouse_manage_prefix,
                warehouse_manage,
                '/warehouse_manage/allocation/allocation_create_invoice/material/',
                'allocation_create_invoice_material',
                CreateInvoiceMaterialInfo.as_view('allocation_create_invoice_material'),
                methods=['GET'])
add_url.add_url(u'修改调拨单获取物料信息',
                'warehouse_manage.allocation_modify_invoice',
                add_url.TYPE_FUNC,
                warehouse_manage_prefix,
                warehouse_manage,
                '/warehouse_manage/allocation/allocation_modify_invoice/material/',
                'allocation_modify_invoice_material',
                ModifyInvoiceMaterialInfo.as_view('allocation_modify_invoice_material'),
                methods=['GET'])
add_url.add_url(u'复制调拨单获取物料信息',
                'warehouse_manage.allocation_copy_invoice',
                add_url.TYPE_FUNC,
                warehouse_manage_prefix,
                warehouse_manage,
                '/warehouse_manage/allocation/allocation_copy_invoice/material/',
                'allocation_copy_invoice_material',
                CopyInvoiceMaterialInfo.as_view('allocation_copy_invoice_material'),
                methods=['GET'])