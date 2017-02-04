#!/usr/bin/python
# -*- coding:utf-8 -*-
#    Copyright(c) 2015-2016 JmGo Company
#    All rights reserved.
#
#    文件名 : invoice.py
#    作者   : WangYi
#  电子邮箱 : ywang@jmgo.com
#    日期   : 2017/1/4 21:06
#
#     描述  : 创建/修改/复制/删除调拨单
#
from flask.views import MethodView
from flask import request, jsonify, session, json
import traceback
from config.service_config.returncode import ServiceCode
from public.logger.syslog import SystemLog
from public.exception.custom_exception import CodeError
from public.function import tools
from control_center.warehouse_manage import warehouse_manage, warehouse_manage_prefix
from control_center.admin import add_url
from ..control.allocation_op import AllocationOp
from config.share.share_define import WarehouseManagementAttr as WMA


def rebuilt_allocation_type():
    data_list = []
    for key, value in WMA.ALLOCATION_TYPE.items():
        data_list.append({'allocation_type_id': key,
                          'outgoing_type': value}
                         )
    return data_list


def rebuilt_invoice_state():
    data_list = []
    for key, value in WMA.INVOICE_STATE.items():
        data_list.append({'invoice_state_id': key,
                          'invoice_state': value}
                         )
    return data_list


def rebuilt_person_info():
    from .person import main
    data = main()
    data.pop('code')
    return data


def rebuilt_warehouse_info():
    from .warehouse import main
    data = main()
    data.pop('code')
    return data


def rebuilt_department_info():
    from .department import main
    data = main()
    data.pop('code')
    data.pop('msg')
    data['total'] = len(data['rows'])
    return data


class CreateInvoiceView(MethodView):
    def get(self):
        return_data = None
        try:
            import datetime
            op = AllocationOp()
            return_data = {
                'code': ServiceCode.success,
                'type': 0,
                'allocation_type_List': rebuilt_allocation_type(),
                'invoice_number': op.create_invoice(),
                'invoice_date': datetime.datetime.now().strftime('%Y-%m-%d'),
                'person_data': rebuilt_person_info(),
                'warehouse_data': rebuilt_warehouse_info(),
                'department_data': rebuilt_department_info(),
                'maker': session['user']['name'],
                'invoice_type': WMA.INVOICE_TYPE[WMA.ALLOCATION_WAREHOUSE],
                'invoice_state': WMA.INVOICE_STATE[WMA.TEMPORARY_STORAGE],
                'maker_id': session['user']['id'],
                'invoice_type_id': '12-7',
                'invoice_state_id': "13-1",
            }
        except CodeError as e:
            return_data = e.json_value()
        except Exception:
            SystemLog.pub_warninglog(traceback.format_exc())
            return_data = {'code': ServiceCode.exception_op, 'msg': u'服务器错误'}
        finally:
            if return_data.get('code', ServiceCode.exception_op) != ServiceCode.success:
                return tools.en_render_template('public/error.html',
                                                code_msg=return_data.get('msg'))
            else:
                return tools.en_render_template('warehouseManagement/stockManage/newAllotInvoice.html',
                                                result=json.dumps(return_data))


class ModifyInvoiceView(MethodView):
    def get(self):
        return_data = None
        try:
            invoice = request.values.get('invoice_number', None, str)
            if not invoice:
                raise CodeError(ServiceCode.params_error, u'请选择单据')

            op = AllocationOp()
            return_data = op.get_invoice_information(invoice)
            data, total = op.get_opreate_record(1, 5, {'invoice_number': invoice})
            # 页面类型
            return_data['code'] = ServiceCode.success
            return_data['type'] = 1
            return_data['person_data'] = rebuilt_person_info()
            return_data['warehouse_data'] = rebuilt_warehouse_info()
            return_data['department_data'] = rebuilt_department_info()
            return_data['allocation_type_List'] = rebuilt_allocation_type()
            return_data['state_type'] = 1 if return_data.get('invoice_state_id') == WMA.TEMPORARY_STORAGE else 0
            return_data['update_records'] = {
                'total': total,
                'rows': data
            }
        except CodeError as e:
            return_data = e.json_value()
        except Exception:
            SystemLog.pub_warninglog(traceback.format_exc())
            return_data = {'code': ServiceCode.exception_op, 'msg': u'服务器错误'}
        finally:
            if return_data.get('code', ServiceCode.exception_op) != ServiceCode.success:
                return tools.en_render_template('public/error.html',
                                                code_msg=return_data.get('msg'))
            else:
                return tools.en_render_template('warehouseManagement/stockManage/newAllotInvoice.html',
                                                result=json.dumps(return_data))


class CopyInvoiceView(MethodView):
    def get(self):
        return_data = None
        try:
            import datetime
            invoice = request.values.get('invoice_number', None, str)
            if not invoice:
                raise CodeError(ServiceCode.params_error, u'请选择单据')

            op = AllocationOp()
            return_data = op.get_invoice_information(invoice)
            return_data['code'] = ServiceCode.success
            return_data['type'] = 2

            return_data['person_data'] = rebuilt_person_info()
            return_data['warehouse_data'] = rebuilt_warehouse_info()
            return_data['department_data'] = rebuilt_department_info()
            return_data['allocation_type_List'] = rebuilt_allocation_type()
            # 刷新
            return_data['invoice_number'] = op.create_invoice()
            print("return_data['invoice_number']:", return_data['invoice_number'])
            return_data['invoice_date'] = datetime.datetime.now().strftime('%Y-%m-%d')
            return_data['maker'] = session['user']['name']
            return_data['maker_id'] = session['user']['id']
            return_data['invoice_state'] = WMA.INVOICE_STATE[WMA.TEMPORARY_STORAGE]
            return_data['invoice_state_id'] = WMA.TEMPORARY_STORAGE


        except CodeError as e:
            return_data = e.json_value()
        except Exception:
            SystemLog.pub_warninglog(traceback.format_exc())
            return_data = {'code': ServiceCode.exception_op, 'msg': u'服务器错误'}
        finally:
            if return_data.get('code', ServiceCode.exception_op) != ServiceCode.success:
                return tools.en_render_template('public/error.html',
                                                code_msg=return_data.get('msg'))
            else:
                return tools.en_render_template('warehouseManagement/stockManage/newAllotInvoice.html',
                                                result=json.dumps(return_data))


class DeleteInvoiceInterface(MethodView):
    def post(self):
        return_data = None
        try:
            invoice = request.values.get('invoice_number', None, str)
            if not invoice:
                raise CodeError(ServiceCode.params_error, u'请选择单据')

            op = AllocationOp()
            op.delete_invoice(invoice)
        except CodeError as e:
            return_data = e.json_value()
        except Exception:
            SystemLog.pub_warninglog(traceback.format_exc())
            return_data = {'code': ServiceCode.exception_op, 'msg': u'服务器错误'}
        else:
            return_data = {'code': ServiceCode.success}
        finally:
            return tools.en_return_data(jsonify(return_data))


add_url.add_url(u'新建调拨单',
                'warehouse_manage.warehouse_allocation',
                add_url.TYPE_FEATURE,
                warehouse_manage_prefix,
                warehouse_manage,
                '/warehouse_manage/allocation/allocation_create_invoice/',
                'allocation_create_invoice',
                CreateInvoiceView.as_view('allocation_create_invoice'),
                100,
                methods=['GET'])
add_url.add_url(u'修改调拨单',
                'warehouse_manage.warehouse_allocation',
                add_url.TYPE_FEATURE,
                warehouse_manage_prefix,
                warehouse_manage,
                '/warehouse_manage/allocation/allocation_modify_invoice/',
                'allocation_modify_invoice',
                ModifyInvoiceView.as_view('allocation_modify_invoice'),
                90,
                methods=['GET'])
add_url.add_url(u'复制调拨单',
                'warehouse_manage.warehouse_allocation',
                add_url.TYPE_FEATURE,
                warehouse_manage_prefix,
                warehouse_manage,
                '/warehouse_manage/allocation/allocation_copy_invoice/',
                'allocation_copy_invoice',
                CopyInvoiceView.as_view('allocation_copy_invoice'),
                80,
                methods=['GET'])
add_url.add_url(u'删除调拨单',
                'warehouse_manage.warehouse_allocation',
                add_url.TYPE_FEATURE,
                warehouse_manage_prefix,
                warehouse_manage,
                '/warehouse_manage/allocation/allocation_delete_invoice/',
                'allocation_delete_invoice',
                DeleteInvoiceInterface.as_view('allocation_delete_invoice'),
                70,
                methods=['POST'])
