#!/usr/bin/python
# -*- coding:utf-8 -*-
#    Copyright(c) 2015-2016 JmGo Company
#    All rights reserved.
#
#    文件名 : warehouse_allocation.py
#    作者   : WangYi
#  电子邮箱 : ywang@jmgo.com
#    日期   : 2016/12/29 20:38
#
#     描述  : 在库调拨页面
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
from ..control.allocation_op import AllocationOp


class AllocationIndexView(MethodView):
    def get(self):
        return ''


class WarehouseAllocationView(MethodView):
    def get(self):
        return_data = None
        try:
            page = request.values.get('page', 1, int)
            page_num = request.values.get('pagecount', 10, int)

            op = AllocationOp()
            total, data = op.search(request.values, page, page_num)
            from .invoice import rebuilt_allocation_type, rebuilt_invoice_state
            return_data = {
                'code': ServiceCode.success,
                'total': total,
                'invoice_state_list': rebuilt_invoice_state(),
                'allocation_type_list': rebuilt_allocation_type(),
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
                import json
                return tools.en_render_template('warehouseManagement/stockManage/stockAllot.html',
                                                result=json.dumps(return_data))

    def post(self):
        return_data = None
        try:
            page = request.values.get('page', 1, int)
            page_num = request.values.get('pagecount', 10, int)

            op = AllocationOp()
            total, data = op.search(request.values, page, page_num)
            from .invoice import rebuilt_allocation_type, rebuilt_invoice_state
            return_data = {
                'code': ServiceCode.success,
                'total': total,
                'invoice_state_list': rebuilt_invoice_state(),
                'allocation_type_list': rebuilt_allocation_type(),
                'rows': data
            }
        except CodeError as e:
            return_data = e.json_value()
        except Exception:
            SystemLog.pub_warninglog(traceback.format_exc())
            return_data = {'code': ServiceCode.exception_op, 'msg': u'服务器错误'}
        finally:
            return tools.en_return_data(jsonify(return_data))


class OperateRecordInterface(MethodView):
    def post(self):
        return_data = None
        try:
            invoice_number = request.values.get('invoice_number', None, str)
            page = request.values.get('page', 1, int)
            page_num = request.values.get('pagecount', 5, int)

            if not invoice_number:
                raise CodeError(ServiceCode.params_error, u'参数错误。缺少单据号')

            if page < 0:
                raise CodeError(ServiceCode.params_error, u'页数不能小于0')

            if page_num < 0:
                raise CodeError(ServiceCode.params_error, u'每页显示的数量不能小于0')

            op = AllocationOp()
            data, total = op.get_opreate_record(page, page_num, {'invoice_number': invoice_number})
            return_data = {
                'code': ServiceCode.success,
                'msg': u'成功',
                'rows': data,
                'total': total
            }
        except CodeError as e:
            return_data = e.json_value()
        except Exception:
            SystemLog.pub_warninglog(traceback.format_exc())
            return_data = {'code': ServiceCode.exception_op, 'msg': u'服务器错误'}
        finally:
            return tools.en_return_data(jsonify(return_data))


add_url.add_url(u'在库管理',
                'warehouse_manage.index',
                add_url.TYPE_ENTRY,
                warehouse_manage_prefix,
                warehouse_manage,
                '/warehouse_manage/index/',
                'allocation_index',
                AllocationIndexView.as_view('allocation_index'),
                80,
                methods=['GET', 'POST'])


add_url.add_url(u'在库调拨',
                'warehouse_manage.allocation_index',
                add_url.TYPE_ENTRY,
                warehouse_manage_prefix,
                warehouse_manage,
                '/warehouse_manage/allocation/',
                'warehouse_allocation',
                WarehouseAllocationView.as_view('warehouse_allocation'),
                100,
                methods=['GET', 'POST'])


add_url.add_url(u'获取操作记录',
                'warehouse_manage.warehouse_allocation',
                add_url.TYPE_FUNC,
                warehouse_manage_prefix,
                warehouse_manage,
                '/warehouse_manage/allocation/operate_record/',
                'allocation_get_operate_record',
                OperateRecordInterface.as_view('allocation_get_operate_record'),
                methods=['POST'])