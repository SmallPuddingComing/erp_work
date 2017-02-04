#!/usr/bin/python
# -*- coding:utf-8 -*-
#    Copyright(c) 2015-2016 JmGo Company
#    All rights reserved.
#
#    文件名 : save.py
#    作者   : WangYi
#  电子邮箱 : ywang@jmgo.com
#    日期   : 2017/1/6 10:35
#
#     描述  : 调拨单保存
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
from config.share.share_define import WarehouseManagementAttr as WMA


def parse_request_to_dict():
    import json
    para_dict = {}
    for key, value in request.values.items():
        if key in ('invoice_number', 'invoice_date', 'remarks',
                   'invoice_type_id', 'invoice_state_id', 'allocation_type_id'):
            if value:
                para_dict[key] = value.encode()
        elif key == 'rows':
            temp = json.loads(value)
            if len(temp):
                para_dict[key] = temp
            else:
                SystemLog.pub_warninglog('PARAS ERROR: key: rows length is zero.')
                raise CodeError(ServiceCode.params_error, u'保存错误')
        else:
            try:
                if value and int(value):
                    para_dict[key] = int(value)
                else:
                    pass
            except Exception:
                SystemLog.pub_warninglog('PARAS ERROR: key:%s value:%s ' % (key, value))
                SystemLog.pub_warninglog("value:%s  %s" % (value, type(value)))
                SystemLog.pub_warninglog("key:%s" % key)
                raise
    return para_dict


class CreateInvoiceSave(MethodView):
    @staticmethod
    def post():
        return_data = None
        try:
            # 解析参数
            op = AllocationOp()
            para_dict = parse_request_to_dict()
            if op.check_invoice_number(para_dict['invoice_number']):
                op.modify_invoice(para_dict, u'新建单据', u'新建保存单据')
            else:
                op.save_invoice(para_dict, u'新建单据', u'新建保存单据')
        except CodeError as e:
            return_data = e.json_value()
        except Exception:
            SystemLog.pub_warninglog(traceback.format_exc())
            return_data = {'code': ServiceCode.params_error, 'msg': u'服务器错误'}
        else:
            return_data = {'code': ServiceCode.success}
        finally:
            return tools.en_return_data(jsonify(return_data))


class CreateInvoiceCommit(MethodView):
    @staticmethod
    def post():
        return_data = None
        try:
            # 解析参数
            op = AllocationOp()
            para_dict = parse_request_to_dict()
            if op.check_invoice_number(para_dict['invoice_number']):
                op.modify_invoice(para_dict, u'新建单据', u'新建提交单据')
            else:
                op.save_invoice(para_dict, u'新建单据', u'新建提交单据')
            op.commit_invoice(para_dict['invoice_number'])
        except CodeError as e:
            return_data = e.json_value()
        except Exception:
            SystemLog.pub_warninglog(traceback.format_exc())
            return_data = {'code': ServiceCode.params_error, 'msg': u'服务器错误'}
        else:
            return_data = {'code': ServiceCode.success}
        finally:
            return tools.en_return_data(jsonify(return_data))


class ModifyInvoiceSave(MethodView):
    @staticmethod
    def post():
        return_data = None
        try:
            op = AllocationOp()
            para_dict = parse_request_to_dict()
            # 检测状态
            if para_dict['invoice_state_id'] != WMA.TEMPORARY_STORAGE:
                raise CodeError(ServiceCode.params_error, u'已完成的单据无法重复保存.')

            if op.check_invoice_number(para_dict['invoice_number']):
                op.modify_invoice(para_dict, u'修改单据', u'修改保存单据')
            else:
                raise CodeError(ServiceCode.params_error, u'单据不存在')

        except CodeError as e:
            return_data = e.json_value()
        except Exception:
            SystemLog.pub_warninglog(traceback.format_exc())
            return_data = {'code': ServiceCode.params_error, 'msg': u'服务器错误'}
        else:
            return_data = {'code': ServiceCode.success}
        finally:
            return tools.en_return_data(jsonify(return_data))


class ModifyInvoiceCommit(MethodView):
    @staticmethod
    def post():
        return_data = None
        try:
            op = AllocationOp()
            para_dict = parse_request_to_dict()
            # 检测状态
            if para_dict['invoice_state_id'] != WMA.TEMPORARY_STORAGE:
                raise CodeError(ServiceCode.params_error, u'已完成的单据无法重复保存.')

            if op.check_invoice_number(para_dict['invoice_number']):
                op.modify_invoice(para_dict, u'修改单据', u'修改保存单据')
            else:
                raise CodeError(ServiceCode.params_error, u'单据号不存在')

            op.commit_invoice(para_dict['invoice_number'])
        except CodeError as e:
            return_data = e.json_value()
        except Exception:
            SystemLog.pub_warninglog(traceback.format_exc())
            return_data = {'code': ServiceCode.params_error, 'msg': u'服务器错误'}
        else:
            return_data = {'code': ServiceCode.success}
        finally:
            return tools.en_return_data(jsonify(return_data))


class CopyInvoiceSave(MethodView):
    @staticmethod
    def post():
        return_data = None
        try:
            # 解析参数
            op = AllocationOp()
            para_dict = parse_request_to_dict()
            if op.check_invoice_number(para_dict['invoice_number']):
                op.modify_invoice(para_dict, u'复制单据', u'复制保存单据')
            else:
                op.save_invoice(para_dict, u'复制单据', u'复制保存单据')
        except CodeError as e:
            return_data = e.json_value()
        except Exception:
            SystemLog.pub_warninglog(traceback.format_exc())
            return_data = {'code': ServiceCode.params_error, 'msg': u'服务器错误'}
        else:
            return_data = {'code': ServiceCode.success}
        finally:
            return tools.en_return_data(jsonify(return_data))


class CopyInvoiceCommit(MethodView):
    def post(self):
        return_data = None
        try:
            op = AllocationOp()
            para_dict = parse_request_to_dict()
            if op.check_invoice_number(para_dict['invoice_number']):
                op.modify_invoice(para_dict, u'复制单据', u'复制保存单据')
            else:
                op.save_invoice(para_dict, u'复制单据', u'复制保存单据')
            op.commit_invoice(para_dict['invoice_number'])
        except CodeError as e:
            return_data = e.json_value()
        except Exception:
            SystemLog.pub_warninglog(traceback.format_exc())
            return_data = {'code': ServiceCode.params_error, 'msg': u'服务器错误'}
        else:
            return_data = {'code': ServiceCode.success}
        finally:
            return tools.en_return_data(jsonify(return_data))


add_url.add_url(u'新建调拨单保存',
                'warehouse_manage.allocation_create_invoice',
                add_url.TYPE_FUNC,
                warehouse_manage_prefix,
                warehouse_manage,
                '/warehouse_manage/allocation/allocation_create_invoice/save/',
                'allocation_create_invoice_save',
                CreateInvoiceSave.as_view('allocation_create_invoice_save'),
                methods=['POST'])

add_url.add_url(u'新建调拨单提交',
                'warehouse_manage.allocation_create_invoice',
                add_url.TYPE_FUNC,
                warehouse_manage_prefix,
                warehouse_manage,
                '/warehouse_manage/allocation/allocation_create_invoice/commit/',
                'allocation_create_invoice_commit',
                CreateInvoiceCommit.as_view('allocation_create_invoice_commit'),
                methods=['POST'])

add_url.add_url(u'修改调拨单保存',
                'warehouse_manage.allocation_modify_invoice',
                add_url.TYPE_FUNC,
                warehouse_manage_prefix,
                warehouse_manage,
                '/warehouse_manage/allocation/allocation_modify_invoice/save/',
                'allocation_modify_invoice_save',
                ModifyInvoiceSave.as_view('allocation_modify_invoice_save'),
                methods=['POST'])


add_url.add_url(u'修改调拨单提交',
                'warehouse_manage.allocation_modify_invoice',
                add_url.TYPE_FUNC,
                warehouse_manage_prefix,
                warehouse_manage,
                '/warehouse_manage/allocation/allocation_modify_invoice/commit/',
                'allocation_modify_invoice_commit',
                ModifyInvoiceCommit.as_view('allocation_modify_invoice_commit'),
                methods=['POST'])


add_url.add_url(u'复制调拨单保存',
                'warehouse_manage.allocation_copy_invoice',
                add_url.TYPE_FUNC,
                warehouse_manage_prefix,
                warehouse_manage,
                '/warehouse_manage/allocation/allocation_copy_invoice/save/',
                'allocation_copy_invoice_save',
                CopyInvoiceSave.as_view('allocation_copy_invoice_save'),
                methods=['POST'])

add_url.add_url(u'复制调拨单提交',
                'warehouse_manage.allocation_copy_invoice',
                add_url.TYPE_FUNC,
                warehouse_manage_prefix,
                warehouse_manage,
                '/warehouse_manage/allocation/allocation_copy_invoice/commit/',
                'allocation_copy_invoice_commit',
                CopyInvoiceCommit.as_view('allocation_copy_invoice_commit'),
                methods=['POST'])
