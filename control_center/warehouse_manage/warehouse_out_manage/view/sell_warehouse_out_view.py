#!/usr/bin/python
# -*- coding:utf-8 -*-
#    Copyright(c) 2015-2016 JmGo Company
#    All rights reserved.
#
#    文件名 : warehouse_out_view.py
#    作者   : ChengQian
#  电子邮箱 : qcheng@jmgo.com
#    日期   : 2016/12/30 14:39
#
#     描述  :
#
import datetime
from flask.views import MethodView
from flask import request
import json
import traceback
from flask import session
from config.service_config.returncode import ServiceCode
from public.logger.syslog import SystemLog
from public.exception.custom_exception import CodeError
from public.function import tools
from config.share.share_define import get_key_by_value
from config.share.share_define import SupplyAttr
from control_center.warehouse_manage import warehouse_manage, warehouse_manage_prefix
from control_center.admin import add_url
from config.share.share_define import WarehouseManagementAttr
from data_mode.erp_supply.base_op.warehouse_manage_op.warehouse_op import WarehouseManageBaseOp
from control_center.warehouse_manage.warehouse_out_manage.control.sell_warehouse_out_op import SellWarehousOutOp
from control_center.warehouse_manage.warehouse_out_manage.view.other_warehouse_out_view import worker
from control_center.warehouse_manage.warehouse_out_manage.view.other_warehouse_out_view import warehouse
from control_center.warehouse_manage.warehouse_out_manage.view.other_warehouse_out_view import department
from control_center.warehouse_manage.warehouse_out_manage.view.other_warehouse_out_view import customer


# def worker():
#     from data_mode.user_center.control.mixOp import MixUserCenterOp
#     op = MixUserCenterOp()
#     row, total = op.get_all_person_info()
#     data = {
#         'rows': row,
#         'total': total
#     }
#     return data

# def warehouse():
#     from control_center.supply_chain.material_warehosue.control.material_warehouse_mix_op import GetWarehouseInfo
#     op = GetWarehouseInfo()
#     total, warehouse_data = op.get_warehouse_all()
#     # 重构
#     new_data = []
#     for element in warehouse_data:
#         new_data.append({
#             'warehouse_id': element['warehouse_id'],
#             'warehouse_code': element['warehouse_code'],
#             'warehouse_name': element['warehouse_name'],
#             'warehouse_type': op.get_warehouse_type_by_id(element['warehouse_type_id']),
#             'contacts': element['contacts'],
#             'prov': element['prov'],
#             'city': element['city'],
#             'region': element['region'],
#             'address': element['address']
#             })
#     data = {
#         'total': total,
#         'rows': new_data
#     }
#     return data

# def customer():
#     from control_center.warehouse_manage.warehouse_out_manage.control.mixOp import select_customer
#     total, customer_datas = select_customer()
#     data = {
#         'rows': customer_datas,
#         'total': total
#     }
#     return data

# def department():
#     from data_mode.user_center.control.mixOp import MixUserCenterOp
#     user_op = MixUserCenterOp()
#     department_datas = user_op.get_departments_info()
#     if department_datas:
#         data = {
#             'rows': department_datas[0].get('departMents'),
#             'total': len(department_datas[0].get('departMents'))
#         }
#     else:
#         data = {
#             'rows': [],
#             'total': 0
#         }
#     return data


class WarehouseOutManagement(MethodView):
    """
     出库管理
    """
    @staticmethod
    def get():
        return ""


class WarehouseSellView(MethodView):
    """
    销售出库页面
    """
    @staticmethod
    def get():
            return_data = None
            try:
                page = request.values.get("page", 1, int) # 分页当前页数
                pagecount = request.values.get("pagecount", 10, int) # 分页中每页显示的最多纪录数
                search_dict = {}
                search_dict['page'] = page
                search_dict['pagecount'] = pagecount

                wh_base_op = WarehouseManageBaseOp()
                sell_op = SellWarehousOutOp()
                # 访问warehouse_out_other_invoice表，获取所有的其他出库单据
                total, invoice_datas = sell_op.get_order_baseinfo(**search_dict)
                # 获取单据类型(红蓝单据)
                invoice_type_list = wh_base_op.get_red_blue_invoice_type()
                # 获取单据状态
                invoice_state_list = wh_base_op.get_invoice_state(WarehouseManagementAttr.INVOICE_STATE)
                # 获取当前时间
                start_time = (datetime.datetime.now()).strftime("%Y-%m-%d")
                stop_time = (datetime.datetime.now()).strftime("%Y-%m-%d")
                # raise CodeError(ServiceCode.check_error, u'测试错误')
            except CodeError as e:
                return_data = e.json_value()
            except Exception:
                SystemLog.pub_warninglog(traceback.format_exc())
                return_data = {'code': ServiceCode.service_exception, 'msg': u'服务器错误'}
            else:
                return_data = {
                    'code': ServiceCode.success,
                    'start_time':start_time,
                    'stop_time':stop_time,
                    'invoice_color': WarehouseManagementAttr.BLUE_ORDER_DIRECTION,
                    'total': total,
                    'invoice_type_list': invoice_type_list,
                    'invoice_state_list': invoice_state_list,
                    'rows': invoice_datas
                }
            finally:
                if return_data.get('code', ServiceCode.service_exception) != ServiceCode.success:
                    return tools.en_render_template('public/error.html',
                                                    code_msg=return_data.get('msg'))
                else:
                    # return tools.en_return_data(json.dumps(return_data))
                    return tools.en_render_template('/warehouseManagement/outstorage_management/sales_out_storage.html',
                                                    result=json.dumps(return_data))


class CreateSellWarehouseOutOrder(MethodView):
    """
    新建销售出库单页面
    """
    @staticmethod
    def get():
            return_data = None
            try:
                red_or_blue_type = request.values.get("invoice_type_id", None, str)
                wh_base_op = WarehouseManageBaseOp()
                sell_op = SellWarehousOutOp()

                blue_flag = WarehouseManagementAttr.BLUE_ORDER_DIRECTION
                red_flag = WarehouseManagementAttr.RED_ORDER_DIRECTION
                if red_or_blue_type is None:
                    raise CodeError(ServiceCode.service_exception, msg=u"红蓝单据类型参数有误")
                else:
                    is_red_invoice = wh_base_op.judge_red_blue_invoice_flag(red_or_blue_type)

                # 创建单据单号
                invoice_number = sell_op.create_sell_warehouse_number(is_red_invoice)
                # 单据保存时间
                create_time = (datetime.datetime.now()).strftime("%Y-%m-%d")
                # 获取制单人ID和名称
                maker_id = session['user']['id']
                maker_name = session['user']['name']
                # 获取单据类型ID和名称
                invoice_type = WarehouseManagementAttr.INVOICE_TYPE.get(WarehouseManagementAttr.SELL_OUT_WAREHOUSE)
                invoice_type_id = WarehouseManagementAttr.SELL_OUT_WAREHOUSE
                # 获取单据状态ID和名称
                invoice_state = WarehouseManagementAttr.INVOICE_STATE.get(WarehouseManagementAttr.TEMPORARY_STORAGE)
                invoice_state_id = WarehouseManagementAttr.TEMPORARY_STORAGE
                # 获取销售出库出库类型列表
                outgoing_type_list = wh_base_op.get_sell_outwarehouse_type(
                    WarehouseManagementAttr.SELL_OUTWAREHOUSE_TYPE)
                # 获取库存方向ID和名称
                if is_red_invoice: # 表示是红字单据
                    stock_direction_id = red_flag
                    stock_direction = WarehouseManagementAttr.REPERTORY_DIRECTION_TYPE.get(red_flag)
                else:
                    stock_direction_id = blue_flag
                    stock_direction = WarehouseManagementAttr.REPERTORY_DIRECTION_TYPE.get(blue_flag)

                # 获取人员信息
                person_data = worker()
                # 获取仓库信息
                warehouse_data = warehouse()
                # 获取部门组织信息
                department_data = department()
                # 获取客户信息
                customer_data = customer()
            except CodeError as e:
                return_data = e.json_value()
            except Exception:
                SystemLog.pub_warninglog(traceback.format_exc())
                return_data = {'code': ServiceCode.service_exception, 'msg': u'服务器错误'}
            else:
                return_data = {
                    'code': ServiceCode.success,
                    'is_red_invoice': is_red_invoice,
                    'page_type': 1,
                    'invoice_number': invoice_number,
                    'invoice_date': create_time,
                    'maker': maker_name,
                    'invoice_type': invoice_type,
                    'invoice_state': invoice_state,
                    'stock_direction': stock_direction,
                    'outgoing_type_list': outgoing_type_list,
                    'person_data': person_data,
                    'warehouse_data': warehouse_data,
                    'department_data': department_data,
                    'customer_data': customer_data,
                    'maker_id': maker_id,
                    'invoice_type_id': invoice_type_id,
                    'invoice_state_id': invoice_state_id,
                    'stock_direction_id': stock_direction_id
                }
            finally:
                return tools.en_render_template('/warehouseManagement/outstorage_management/add_sales_out_storage.html',
                                                result=json.dumps(return_data))


class CopySellWarehouseOutOrder(MethodView):
    """
    复制销售出库单页面
    """
    @staticmethod
    def get():
            return_data = None
            try:
                invoice_number = request.values.get("invoice_number", None, str)
                wh_base_op = WarehouseManageBaseOp()
                sell_op = SellWarehousOutOp()

                if invoice_number is None:
                    raise CodeError(ServiceCode.service_exception, msg=u"单据单号参数错误")
                # 根据单据号获取该单据的相关信息
                result_data = sell_op.get_invoice_baseinfo_by_invoice_number(invoice_number)
                if result_data:
                    # 根据库存方向判断红蓝单据标识
                    is_red_invoice = wh_base_op.judge_red_blue_invoice_flag(result_data.get("stock_direction_id"))
                    # 根据单据单号获取单据的物料明细信息
                    material_datas = sell_op.get_invoice_materialinfo_by_invoice_id(result_data.get("invoice_id"))
                    # 复制单据时创建新的单据号
                    new_invoice_number = sell_op.create_sell_warehouse_number(is_red_invoice)
                    result_data['invoice_number'] = new_invoice_number
                    result_data['is_red_invoice'] = is_red_invoice
                    # 复制单据时刷新单据日期
                    new_date = (datetime.datetime.now()).strftime("%Y-%m-%d")
                    result_data['invoice_date'] = new_date
                    # 复制单据时刷新制单人信息
                    maker_id = session['user']['id']
                    maker_name = session['user']['name']
                    result_data['maker'] = maker_name
                    result_data['maker_id'] = maker_id
                    # 复制单据时刷新单据状态信息为“暂存”
                    invoice_state = WarehouseManagementAttr.INVOICE_STATE.get(WarehouseManagementAttr.TEMPORARY_STORAGE)
                    invoice_state_id = WarehouseManagementAttr.TEMPORARY_STORAGE
                    result_data['invoice_state'] = invoice_state
                    result_data['invoice_state_id'] = invoice_state_id
                    # 获取其他出库出库类型列表
                    outgoing_type_list = wh_base_op.get_sell_outwarehouse_type(
                        WarehouseManagementAttr.SELL_OUTWAREHOUSE_TYPE)
                    result_data['outgoing_type_list'] = outgoing_type_list
                    result_data['rows'] = material_datas
                    # 获取人员信息
                    result_data['person_data'] = worker()
                    # 获取仓库信息
                    result_data['warehouse_data'] = warehouse()
                    # 获取部门组织信息
                    result_data['department_data'] = department()
                    # 获取客户信息
                    result_data['customer_data'] = customer()
                    result_data['code'] = ServiceCode.success
                    result_data['page_type'] = 2
                else:
                    raise CodeError(ServiceCode.service_exception, msg=u"该单据单号对应的记录不存在")

            except CodeError as e:
                return_data = e.json_value()
            except Exception:
                SystemLog.pub_warninglog(traceback.format_exc())
                return_data = {'code': ServiceCode.service_exception, 'msg': u'服务器错误'}
            else:
                return_data = result_data
            finally:
                return tools.en_render_template('/warehouseManagement/outstorage_management/add_sales_out_storage.html',
                                                result=json.dumps(return_data))


class ModifySellWarehouseOutOrder(MethodView):
    """
    修改销售出库单页面
    """
    @staticmethod
    def get():
            return_data = None
            try:
                invoice_number = request.values.get("invoice_number", None, str)
                invoice_state_id = request.values.get("invoice_state_id", None, str)
                wh_base_op = WarehouseManageBaseOp()
                sell_op = SellWarehousOutOp()
                if invoice_number is None:
                    raise CodeError(ServiceCode.service_exception, msg=u"单据单号参数错误")
                if invoice_state_id is None:
                    raise CodeError(ServiceCode.service_exception, msg=u"单据单号的单据状态参数错误")
                # 根据单据单号获取该单据的状态
                temp_state_id = WarehouseManagementAttr.TEMPORARY_STORAGE # 暂存”状态ID
                saved_invoice_state_id = sell_op.get_invoice_state(invoice_number)
                if saved_invoice_state_id != invoice_state_id:
                    raise CodeError(ServiceCode.service_exception, msg=u"单据单号的单据状态与记录不符")
                # 根据单据号获取该单据的相关信息
                result_data = sell_op.get_invoice_baseinfo_by_invoice_number(invoice_number)
                if result_data:
                    if invoice_state_id != temp_state_id: # 表示此状态不是暂存状态，数据只能查看，不能修改
                        result_data['state_type'] = 0
                    else:
                        result_data['state_type'] = 1 # 可以修改
                    # 根据库存方向判断红蓝单据标识
                    is_red_invoice = wh_base_op.judge_red_blue_invoice_flag(result_data.get("stock_direction_id"))
                    result_data['is_red_invoice'] = is_red_invoice
                    # 根据单据单号获取单据的物料明细信息
                    material_datas = sell_op.get_invoice_materialinfo_by_invoice_id(result_data.get("invoice_id"))
                    # 获取销售出库出库类型列表
                    outgoing_type_list = wh_base_op.get_sell_outwarehouse_type(
                        WarehouseManagementAttr.SELL_OUTWAREHOUSE_TYPE)
                    result_data['outgoing_type_list'] = outgoing_type_list
                    result_data['rows'] = material_datas
                    # 获取该单据单号的操作记录
                    record_total, record_datas = sell_op.get_invoice_operate_record(invoice_number)
                    update_records = {}
                    update_records['total'] = record_total
                    update_records['rows'] = record_datas
                    result_data['update_records'] = update_records
                    # 获取人员信息
                    result_data['person_data'] = worker()
                    # 获取仓库信息
                    result_data['warehouse_data'] = warehouse()
                    # 获取部门组织信息
                    result_data['department_data'] = department()
                    # 获取客户信息
                    result_data['customer_data'] = customer()
                    result_data['code'] = ServiceCode.success
                    result_data['page_type'] = 3
                else:
                    raise CodeError(ServiceCode.service_exception, msg=u"该单据单号对应的记录不存在")
            except CodeError as e:
                return_data = e.json_value()
            except Exception:
                SystemLog.pub_warninglog(traceback.format_exc())
                return_data = {'code': ServiceCode.service_exception, 'msg': u'服务器错误'}
            else:
                return_data = result_data
            finally:
                return tools.en_render_template('/warehouseManagement/outstorage_management/add_sales_out_storage.html',
                                                result=json.dumps(return_data))


class DeleteSellWarehouseOutOrder(MethodView):
    """
    删除某个销售出库单据
    """
    @staticmethod
    def post():
        return_data = None
        try:
            del_invoice_number = request.values.get("invoice_number", None, str)
            del_invoice_state_id = request.values.get("invoice_state_id", None, str)
            sell_op = SellWarehousOutOp()
            if del_invoice_number is None:
                raise CodeError(ServiceCode.service_exception, msg=u"需要被删除的单据单号参数错误")
            if del_invoice_state_id is None:
                raise CodeError(ServiceCode.service_exception, msg=u"需要被删除的单据单号的单据状态参数错误")
            # 根据单据单号获取要被删除的单据的状态
            temp_state_id = WarehouseManagementAttr.TEMPORARY_STORAGE # 暂存”状态ID
            saved_invoice_state_id = sell_op.get_invoice_state(del_invoice_number)
            if saved_invoice_state_id != del_invoice_state_id:
                raise CodeError(ServiceCode.service_exception, msg=u"需要被删除的单据单号的单据状态与记录不符")
            elif del_invoice_state_id != temp_state_id:
                raise CodeError(ServiceCode.service_exception, msg=u"需要被删除的单据单号的单据状态参数有误，"
                                                                   u"只能修改暂存状态的单据")
            # 删除该单据单号对应的单据所有信息
            sell_op.del_invoice_info_by_invoice_number(del_invoice_number)
        except CodeError as e:
            return_data = e.json_value()
        except Exception:
            SystemLog.pub_warninglog(traceback.format_exc())
            return_data = {'code': ServiceCode.service_exception, 'msg': u'服务器错误'}
        else:
            return_data = {
                    'code': ServiceCode.success,
                    'msg': u"删除成功"
                }
        finally:
            return tools.en_return_data(json.dumps(return_data))


class WarehouseSellSearchView(MethodView):
    """
    销售出库页面——搜索或分页
    """
    @staticmethod
    def post():
            return_data = None
            try:
                invoice_number = request.values.get("invoice_number", None, str) # 单据大号
                start_time = request.values.get("start_time", None, str) # 搜素开始时间
                stop_time = request.values.get("stop_time", None, str) # 搜索结束时间
                invoice_type_id = request.values.get("invoice_type", None, str) # 单据类型（红蓝单据）
                invoice_state_id = request.values.get("invoice_state", None, str) # 单据状态
                purchase_unit = request.values.get("purchase_unit", None, str) # 购货单位
                page = request.values.get("page", 1, int) # 分页当前页数
                pagecount = request.values.get("pagecount", 10, int) # 分页中每页显示的最多纪录数

                if page <=0 or pagecount <= 0:
                    raise CodeError(ServiceCode.service_exception, msg=u"分页参数page和pagecount必须是正整数")

                search_dict = {}
                search_dict['invoice_number'] = invoice_number if invoice_number else None
                search_dict['start_time'] = start_time if start_time else None
                search_dict['stop_time'] = stop_time if stop_time else None
                search_dict['invoice_type'] = invoice_type_id if invoice_type_id else None
                search_dict['invoice_state'] = invoice_state_id if invoice_state_id else None
                search_dict['purchase_unit'] = purchase_unit if purchase_unit else None
                search_dict['page'] = page
                search_dict['pagecount'] = pagecount

                sell_op = SellWarehousOutOp()
                # 访问warehouse_out_other_invoice表，获取所有的其他出库单据
                total, invoice_datas = sell_op.get_order_baseinfo(**search_dict)
            except CodeError as e:
                return_data = e.json_value()
            except Exception:
                SystemLog.pub_warninglog(traceback.format_exc())
                return_data = {'code': ServiceCode.service_exception, 'msg': u'服务器错误'}
            else:
                return_data = {
                    'code': ServiceCode.success,
                    'total': total,
                    'rows': invoice_datas
                }
            finally:
                return tools.en_return_data(json.dumps(return_data))


class SaveCreateSellWarehouseOrder(MethodView):
    """
    保存或提交新建的销售出库单
    """
    @staticmethod
    def post():
            return_data = None
            try:
                receive_data_dict = {}
                receive_data_dict['invoice_number'] = request.values.get("invoice_number", None, str)
                recv_date = request.values.get("invoice_date", None, str)
                receive_data_dict['invoice_date']= (datetime.datetime.now()).strftime("%Y-%m-%d %H:%M:%S")
                receive_data_dict['online_shop'] = request.values.get("online_shop", None, str)
                receive_data_dict['maker_id'] = request.values.get("maker_id", None, int)
                receive_data_dict['invoice_type_id'] = request.values.get("invoice_type_id", None, str)
                receive_data_dict['invoice_state_id'] = request.values.get("invoice_state_id", None, str)
                receive_data_dict['storeman_id'] = request.values.get("storeman_id", None, int)
                receive_data_dict['outgoingType_id'] = request.values.get("outgoingType_id", None, str)
                receive_data_dict['purchaseUnit_id'] = request.values.get("purchaseUnit_id", None, int)
                receive_data_dict['deliver_handler_id'] = request.values.get("deliver_handler_id", None, int)
                receive_data_dict['stock_direction_id'] = request.values.get("stock_direction_id", None, str)
                receive_data_dict['warehouse_id'] = request.values.get("warehouse_id", None, int)
                receive_data_dict['salesman_id'] = request.values.get("salesman_id", None, int)
                receive_data_dict['department_id'] = request.values.get("department_id", None, int)
                receive_data_dict['remarks'] = request.values.get("remarks", None, str)
                strmaterial_datas = request.values.get("rows")
                receive_data_dict['rows'] = json.loads(strmaterial_datas)

                if receive_data_dict.get('invoice_number') is None:
                    raise CodeError(ServiceCode.service_exception, msg=u"单据单号为None，该值错误")
                if receive_data_dict.get('maker_id') is None:
                    raise CodeError(ServiceCode.service_exception, msg=u"制单人参数为None，该值错误")
                if receive_data_dict.get('invoice_type_id') is None:
                    raise CodeError(ServiceCode.service_exception, msg=u"单据类型参数为None， 该值错误")
                if receive_data_dict.get('invoice_state_id') is None:
                    raise CodeError(ServiceCode.service_exception, msg=u"单据状态参数为None， 该值错误")
                if receive_data_dict.get('storeman_id') is None:
                    raise CodeError(ServiceCode.service_exception, msg=u"保管员参数为None， 该值错误")
                if receive_data_dict.get('outgoingType_id') is None:
                    raise CodeError(ServiceCode.service_exception, msg=u"出库类型参数为None， 该值错误")
                if receive_data_dict.get('purchaseUnit_id') is None:
                    raise CodeError(ServiceCode.service_exception, msg=u"客户参数为None， 该值错误")
                if receive_data_dict.get('deliver_handler_id') is None:
                    raise CodeError(ServiceCode.service_exception, msg=u"发货员参数为None， 该值错误")
                if receive_data_dict.get('stock_direction_id') is None:
                    raise CodeError(ServiceCode.service_exception, msg=u"库存方向参数为None， 该值错误")

                sell_op = SellWarehousOutOp()
                sell_op.save_invoice_data(receive_data_dict)
            except CodeError as e:
                return_data = e.json_value()
            except Exception:
                SystemLog.pub_warninglog(traceback.format_exc())
                return_data = {'code': ServiceCode.service_exception, 'msg': u'服务器错误'}
            else:
                return_data = {
                    'code': ServiceCode.success,
                    'msg': u"保存成功"
                }
            finally:
                return tools.en_return_data(json.dumps(return_data))


class SaveCopySellWarehouseOrder(MethodView):
    """
    保存或提交复制的销售出库单
    """
    @staticmethod
    def post():
            return_data = None
            try:
                receive_data_dict = {}
                receive_data_dict['invoice_number'] = request.values.get("invoice_number", None, str)
                recv_date = request.values.get("invoice_date", None, str)
                receive_data_dict['invoice_date']= (datetime.datetime.now()).strftime("%Y-%m-%d %H:%M:%S")
                receive_data_dict['online_shop'] = request.values.get("online_shop", None, str)
                receive_data_dict['maker_id'] = request.values.get("maker_id", None, int)
                receive_data_dict['invoice_type_id'] = request.values.get("invoice_type_id", None, str)
                receive_data_dict['invoice_state_id'] = request.values.get("invoice_state_id", None, str)
                receive_data_dict['storeman_id'] = request.values.get("storeman_id", None, int)
                receive_data_dict['outgoingType_id'] = request.values.get("outgoingType_id", None, str)
                receive_data_dict['purchaseUnit_id'] = request.values.get("purchaseUnit_id", None, int)
                receive_data_dict['deliver_handler_id'] = request.values.get("deliver_handler_id", None, int)
                receive_data_dict['stock_direction_id'] = request.values.get("stock_direction_id", None, str)
                receive_data_dict['warehouse_id'] = request.values.get("warehouse_id", None, int)
                receive_data_dict['salesman_id'] = request.values.get("salesman_id", None, int)
                receive_data_dict['department_id'] = request.values.get("department_id", None, int)
                receive_data_dict['remarks'] = request.values.get("remarks", None, str)
                strmaterial_datas = request.values.get("rows")
                receive_data_dict['rows'] = json.loads(strmaterial_datas)

                if receive_data_dict.get('invoice_number') is None:
                    raise CodeError(ServiceCode.service_exception, msg=u"单据单号为None，该值错误")
                if receive_data_dict.get('maker_id') is None:
                    raise CodeError(ServiceCode.service_exception, msg=u"制单人参数为None，该值错误")
                if receive_data_dict.get('invoice_type_id') is None:
                    raise CodeError(ServiceCode.service_exception, msg=u"单据类型参数为None， 该值错误")
                if receive_data_dict.get('invoice_state_id') is None:
                    raise CodeError(ServiceCode.service_exception, msg=u"单据状态参数为None， 该值错误")
                if receive_data_dict.get('storeman_id') is None:
                    raise CodeError(ServiceCode.service_exception, msg=u"保管员参数为None， 该值错误")
                if receive_data_dict.get('outgoingType_id') is None:
                    raise CodeError(ServiceCode.service_exception, msg=u"出库类型参数为None， 该值错误")
                if receive_data_dict.get('purchaseUnit_id') is None:
                    raise CodeError(ServiceCode.service_exception, msg=u"客户参数为None， 该值错误")
                if receive_data_dict.get('deliver_handler_id') is None:
                    raise CodeError(ServiceCode.service_exception, msg=u"发货员参数为None， 该值错误")
                if receive_data_dict.get('stock_direction_id') is None:
                    raise CodeError(ServiceCode.service_exception, msg=u"库存方向参数为None， 该值错误")

                sell_op = SellWarehousOutOp()
                sell_op.save_invoice_data(receive_data_dict)
            except CodeError as e:
                return_data = e.json_value()
            except Exception:
                SystemLog.pub_warninglog(traceback.format_exc())
                return_data = {'code': ServiceCode.service_exception, 'msg': u'服务器错误'}
            else:
                return_data = {
                    'code': ServiceCode.success,
                    'msg': u"保存成功"
                }
            finally:
                return tools.en_return_data(json.dumps(return_data))


class SaveModifySellWarehouseOrder(MethodView):
    """
    保存或提交修改的销售出库单
    """
    @staticmethod
    def post():
            return_data = None
            try:
                receive_data_dict = {}
                receive_data_dict['invoice_number'] = request.values.get("invoice_number", None, str)
                receive_data_dict['invoice_date']= recv_date = request.values.get("invoice_date", None, str)
                receive_data_dict['online_shop'] = request.values.get("online_shop", None, str)
                receive_data_dict['maker_id'] = request.values.get("maker_id", None, int)
                receive_data_dict['invoice_type_id'] = request.values.get("invoice_type_id", None, str)
                receive_data_dict['invoice_state_id'] = request.values.get("invoice_state_id", None, str)
                receive_data_dict['storeman_id'] = request.values.get("storeman_id", None, int)
                receive_data_dict['outgoingType_id'] = request.values.get("outgoingType_id", None, str)
                receive_data_dict['purchaseUnit_id'] = request.values.get("purchaseUnit_id", None, int)
                receive_data_dict['deliver_handler_id'] = request.values.get("deliver_handler_id", None, int)
                receive_data_dict['stock_direction_id'] = request.values.get("stock_direction_id", None, str)
                receive_data_dict['warehouse_id'] = request.values.get("warehouse_id", None, int)
                receive_data_dict['salesman_id'] = request.values.get("salesman_id", None, int)
                receive_data_dict['department_id'] = request.values.get("department_id", None, int)
                receive_data_dict['remarks'] = request.values.get("remarks", None, str)
                strmaterial_datas = request.values.get("rows")
                receive_data_dict['rows'] = json.loads(strmaterial_datas)

                if receive_data_dict.get('invoice_number') is None:
                    raise CodeError(ServiceCode.service_exception, msg=u"单据单号为None，该值错误")
                if receive_data_dict.get('maker_id') is None:
                    raise CodeError(ServiceCode.service_exception, msg=u"制单人参数为None，该值错误")
                if receive_data_dict.get('invoice_type_id') is None:
                    raise CodeError(ServiceCode.service_exception, msg=u"单据类型参数为None， 该值错误")
                if receive_data_dict.get('invoice_state_id') is None:
                    raise CodeError(ServiceCode.service_exception, msg=u"单据状态参数为None， 该值错误")
                if receive_data_dict.get('storeman_id') is None:
                    raise CodeError(ServiceCode.service_exception, msg=u"保管员参数为None， 该值错误")
                if receive_data_dict.get('outgoingType_id') is None:
                    raise CodeError(ServiceCode.service_exception, msg=u"出库类型参数为None， 该值错误")
                if receive_data_dict.get('purchaseUnit_id') is None:
                    raise CodeError(ServiceCode.service_exception, msg=u"客户参数为None， 该值错误")
                if receive_data_dict.get('deliver_handler_id') is None:
                    raise CodeError(ServiceCode.service_exception, msg=u"发货员参数为None， 该值错误")
                if receive_data_dict.get('stock_direction_id') is None:
                    raise CodeError(ServiceCode.service_exception, msg=u"库存方向参数为None， 该值错误")

                sell_op = SellWarehousOutOp()
                sell_op.update_invoice_data(receive_data_dict)
            except CodeError as e:
                return_data = e.json_value()
            except Exception:
                SystemLog.pub_warninglog(traceback.format_exc())
                return_data = {'code': ServiceCode.service_exception, 'msg': u'服务器错误'}
            else:
                return_data = {
                    'code': ServiceCode.success,
                    'msg': u"保存成功"
                }
            finally:
                return tools.en_return_data(json.dumps(return_data))


class CreateSellProductSelect(MethodView):
    """
    新建销售出库单页面——产品代码选择
    """
    @staticmethod
    def post():
            return_data = None
            try:
                from data_mode.erp_supply.base_op.material_op.attribute_op import Attribute_Op
                from control_center.warehouse_manage.warehouse_out_manage.control.mixOp import select_material
                material_attr_op = Attribute_Op()
                # 获取物料信息
                total, material_data_list = select_material()
                # 获取物料属性信息
                material_attr_list = material_attr_op.get_material_attribute(SupplyAttr.MATERIAL_ATTRIBUTE_TYPE)
            except CodeError as e:
                return_data = e.json_value()
            except Exception:
                SystemLog.pub_warninglog(traceback.format_exc())
                return_data = {'code': ServiceCode.service_exception, 'msg': u'服务器错误'}
            else:
                return_data = {
                    'code': ServiceCode.success,
                    'total': total,
                    'material_datas': material_data_list,
                    'material_attr_datas': material_attr_list
                }
            finally:
                return tools.en_return_data(json.dumps(return_data))


class CreateSellWarehouseSelect(MethodView):
    """
    新建销售出库单页面——发货仓库选择
    """
    @staticmethod
    def post():
            return_data = None
            try:
                pass
                # raise CodeError(ServiceCode.check_error, u'测试错误')
            except CodeError as e:
                return_data = e.json_value()
            except Exception:
                SystemLog.pub_warninglog(traceback.format_exc())
                return_data = {'code': ServiceCode.service_exception, 'msg': u'服务器错误'}
            else:
                return_data = {'code': ServiceCode.success}
            finally:
                return tools.en_return_data(json.dumps(return_data))


class CreateSellDepartmentSelect(MethodView):
    """
    新建销售出库单页面——部门组织选择
    """
    @staticmethod
    def post():
            return_data = None
            try:
                pass
                # raise CodeError(ServiceCode.check_error, u'测试错误')
            except CodeError as e:
                return_data = e.json_value()
            except Exception:
                SystemLog.pub_warninglog(traceback.format_exc())
                return_data = {'code': ServiceCode.service_exception, 'msg': u'服务器错误'}
            else:
                return_data = {'code': ServiceCode.success}
            finally:
                return tools.en_return_data(json.dumps(return_data))


class CreateSellCustomerSelect(MethodView):
    """
    新建销售出库单页面——购货单位（客户）选择
    """
    @staticmethod
    def post():
            return_data = None
            try:
                pass
                # raise CodeError(ServiceCode.check_error, u'测试错误')
            except CodeError as e:
                return_data = e.json_value()
            except Exception:
                SystemLog.pub_warninglog(traceback.format_exc())
                return_data = {'code': ServiceCode.service_exception, 'msg': u'服务器错误'}
            else:
                return_data = {'code': ServiceCode.success}
            finally:
                return tools.en_return_data(json.dumps(return_data))


class CreateSellWorkerSelect(MethodView):
    """
    新建销售出库单页面——保管员、发货员、业务员选择
    """
    @staticmethod
    def post():
            return_data = None
            try:
                pass
                # raise CodeError(ServiceCode.check_error, u'测试错误')
            except CodeError as e:
                return_data = e.json_value()
            except Exception:
                SystemLog.pub_warninglog(traceback.format_exc())
                return_data = {'code': ServiceCode.service_exception, 'msg': u'服务器错误'}
            else:
                return_data = {'code': ServiceCode.success}
            finally:
                return tools.en_return_data(json.dumps(return_data))


class CreateSellQueryCurRepertory(MethodView):
    """
    新建销售出库单页面——即时库存查询
    """
    @staticmethod
    def post():
            return_data = None
            try:
                from data_mode.erp_supply.base_op.warehouse_manage_op.inventory_op import pub_get_inventory_by_list
                material_data = request.values.get("datas_list")
                for key, value in request.values.items():
                    print("key:", key)
                    print("value:", value)
                print('material_data: ', material_data)
                print('++++++++' * 20)
                material_data_list = json.loads(material_data)
                print('material_data_list: ', material_data_list)
                print("===="* 20)
                result_datas = pub_get_inventory_by_list(material_data_list)
            except CodeError as e:
                return_data = e.json_value()
            except Exception:
                SystemLog.pub_warninglog(traceback.format_exc())
                return_data = {'code': ServiceCode.service_exception, 'msg': u'服务器错误'}
            else:
                return_data = {
                    'code': ServiceCode.success,
                    'rows': result_datas
                }
            finally:
                return tools.en_return_data(json.dumps(return_data))


class CreateSellVerifyOrderUnique(MethodView):
    """
    新建销售出库单页面——校验单据单号的唯一性
    """
    @staticmethod
    def post():
            return_data = None
            try:
                invoice_number = request.values.get("invoice_number", None, str)
                if invoice_number is None:
                    raise CodeError(ServiceCode.service_exception, msg=u"单据单号参数为None，该值错误")

                sell_op = SellWarehousOutOp()
                exist_flag = sell_op.check_invoice_number(invoice_number)
                if exist_flag:
                    strmsg = u"单据单号重复"
                else:
                    strmsg = u"单据单号未重复"
            except CodeError as e:
                return_data = e.json_value()
            except Exception:
                SystemLog.pub_warninglog(traceback.format_exc())
                return_data = {'code': ServiceCode.service_exception, 'msg': u'服务器错误'}
            else:
                return_data = {
                    'code': ServiceCode.success,
                    'msg': strmsg
                }
            finally:
                return tools.en_return_data(json.dumps(return_data))


class SubmitCreateSellWarehouseOrder(MethodView):
    """
    提交新建的其他出库单
    """
    @staticmethod
    def post():
            return_data = None
            try:
                receive_data_dict = {}
                receive_data_dict['invoice_number'] = request.values.get("invoice_number", None, str)
                recv_date = request.values.get("invoice_date", None, str)
                receive_data_dict['invoice_date']= (datetime.datetime.now()).strftime("%Y-%m-%d %H:%M:%S")
                receive_data_dict['online_shop'] = request.values.get("online_shop", None, str)
                receive_data_dict['maker_id'] = request.values.get("maker_id", None, int)
                receive_data_dict['invoice_type_id'] = request.values.get("invoice_type_id", None, str)
                receive_data_dict['invoice_state_id'] = request.values.get("invoice_state_id", None, str)
                receive_data_dict['storeman_id'] = request.values.get("storeman_id", None, int)
                receive_data_dict['outgoingType_id'] = request.values.get("outgoingType_id", None, str)
                receive_data_dict['purchaseUnit_id'] = request.values.get("purchaseUnit_id", None, int)
                receive_data_dict['deliver_handler_id'] = request.values.get("deliver_handler_id", None, int)
                receive_data_dict['stock_direction_id'] = request.values.get("stock_direction_id", None, str)
                receive_data_dict['warehouse_id'] = request.values.get("warehouse_id", None, int)
                receive_data_dict['salesman_id'] = request.values.get("salesman_id", None, int)
                receive_data_dict['department_id'] = request.values.get("department_id", None, int)
                receive_data_dict['remarks'] = request.values.get("remarks", None, str)
                strmaterial_datas = request.values.get("rows")
                receive_data_dict['rows'] = json.loads(strmaterial_datas)

                if receive_data_dict.get('invoice_number') is None:
                    raise CodeError(ServiceCode.service_exception, msg=u"单据单号为None，该值错误")
                if receive_data_dict.get('maker_id') is None:
                    raise CodeError(ServiceCode.service_exception, msg=u"制单人参数为None，该值错误")
                if receive_data_dict.get('invoice_type_id') is None:
                    raise CodeError(ServiceCode.service_exception, msg=u"单据类型参数为None， 该值错误")
                if receive_data_dict.get('invoice_state_id') is None:
                    raise CodeError(ServiceCode.service_exception, msg=u"单据状态参数为None， 该值错误")
                if receive_data_dict.get('storeman_id') is None:
                    raise CodeError(ServiceCode.service_exception, msg=u"保管员参数为None， 该值错误")
                if receive_data_dict.get('outgoingType_id') is None:
                    raise CodeError(ServiceCode.service_exception, msg=u"出库类型参数为None， 该值错误")
                if receive_data_dict.get('purchaseUnit_id') is None:
                    raise CodeError(ServiceCode.service_exception, msg=u"客户参数为None， 该值错误")
                if receive_data_dict.get('deliver_handler_id') is None:
                    raise CodeError(ServiceCode.service_exception, msg=u"发货员参数为None， 该值错误")
                if receive_data_dict.get('stock_direction_id') is None:
                    raise CodeError(ServiceCode.service_exception, msg=u"库存方向参数为None， 该值错误")

                sell_op = SellWarehousOutOp()
                save_flag = sell_op.check_invoice_number(receive_data_dict['invoice_number'])
                if save_flag:
                    sell_op.update_invoice_data(receive_data_dict)
                else:
                    sell_op.save_invoice_data(receive_data_dict)
                sell_op.commit_invoice_data(receive_data_dict['invoice_number'])
            except CodeError as e:
                return_data = e.json_value()
                print("return_data", return_data)
            except Exception:
                SystemLog.pub_warninglog(traceback.format_exc())
                return_data = {'code': ServiceCode.service_exception, 'msg': u'服务器错误'}
            else:
                return_data = {
                    'code': ServiceCode.success,
                    'msg': u"保存成功"
                }
            finally:
                    return tools.en_return_data(json.dumps(return_data))


class SubmitCopySellWarehouseOrder(MethodView):
    """
    提交复制的其他出库单
    """
    @staticmethod
    def post():
            return_data = None
            try:
                receive_data_dict = {}
                receive_data_dict['invoice_number'] = request.values.get("invoice_number", None, str)
                recv_date = request.values.get("invoice_date", None, str)
                receive_data_dict['invoice_date']= (datetime.datetime.now()).strftime("%Y-%m-%d %H:%M:%S")
                receive_data_dict['online_shop'] = request.values.get("online_shop", None, str)
                receive_data_dict['maker_id'] = request.values.get("maker_id", None, int)
                receive_data_dict['invoice_type_id'] = request.values.get("invoice_type_id", None, str)
                receive_data_dict['invoice_state_id'] = request.values.get("invoice_state_id", None, str)
                receive_data_dict['storeman_id'] = request.values.get("storeman_id", None, int)
                receive_data_dict['outgoingType_id'] = request.values.get("outgoingType_id", None, str)
                receive_data_dict['purchaseUnit_id'] = request.values.get("purchaseUnit_id", None, int)
                receive_data_dict['deliver_handler_id'] = request.values.get("deliver_handler_id", None, int)
                receive_data_dict['stock_direction_id'] = request.values.get("stock_direction_id", None, str)
                receive_data_dict['warehouse_id'] = request.values.get("warehouse_id", None, int)
                receive_data_dict['salesman_id'] = request.values.get("salesman_id", None, int)
                receive_data_dict['department_id'] = request.values.get("department_id", None, int)
                receive_data_dict['remarks'] = request.values.get("remarks", None, str)
                strmaterial_datas = request.values.get("rows")
                receive_data_dict['rows'] = json.loads(strmaterial_datas)

                if receive_data_dict.get('invoice_number') is None:
                    raise CodeError(ServiceCode.service_exception, msg=u"单据单号为None，该值错误")
                if receive_data_dict.get('maker_id') is None:
                    raise CodeError(ServiceCode.service_exception, msg=u"制单人参数为None，该值错误")
                if receive_data_dict.get('invoice_type_id') is None:
                    raise CodeError(ServiceCode.service_exception, msg=u"单据类型参数为None， 该值错误")
                if receive_data_dict.get('invoice_state_id') is None:
                    raise CodeError(ServiceCode.service_exception, msg=u"单据状态参数为None， 该值错误")
                if receive_data_dict.get('storeman_id') is None:
                    raise CodeError(ServiceCode.service_exception, msg=u"保管员参数为None， 该值错误")
                if receive_data_dict.get('outgoingType_id') is None:
                    raise CodeError(ServiceCode.service_exception, msg=u"出库类型参数为None， 该值错误")
                if receive_data_dict.get('purchaseUnit_id') is None:
                    raise CodeError(ServiceCode.service_exception, msg=u"客户参数为None， 该值错误")
                if receive_data_dict.get('deliver_handler_id') is None:
                    raise CodeError(ServiceCode.service_exception, msg=u"发货员参数为None， 该值错误")
                if receive_data_dict.get('stock_direction_id') is None:
                    raise CodeError(ServiceCode.service_exception, msg=u"库存方向参数为None， 该值错误")

                sell_op = SellWarehousOutOp()
                save_flag = sell_op.check_invoice_number(receive_data_dict['invoice_number'])
                if save_flag:
                    sell_op.update_invoice_data(receive_data_dict)
                else:
                    sell_op.save_invoice_data(receive_data_dict)
                sell_op.commit_invoice_data(receive_data_dict['invoice_number'])
            except CodeError as e:
                return_data = e.json_value()
            except Exception:
                SystemLog.pub_warninglog(traceback.format_exc())
                return_data = {'code': ServiceCode.service_exception, 'msg': u'服务器错误'}
            else:
                return_data = {
                    'code': ServiceCode.success,
                    'msg': u"保存成功"
                }
            finally:
                return tools.en_return_data(json.dumps(return_data))


class SubmitModifySellWarehouseOrder(MethodView):
    """
    提交修改的其他出库单
    """
    @staticmethod
    def post():
            return_data = None
            try:
                receive_data_dict = {}
                receive_data_dict['invoice_number'] = request.values.get("invoice_number", None, str)
                recv_date = request.values.get("invoice_date", None, str)
                receive_data_dict['invoice_date']= (datetime.datetime.now()).strftime("%Y-%m-%d %H:%M:%S")
                receive_data_dict['online_shop'] = request.values.get("online_shop", None, str)
                receive_data_dict['maker_id'] = request.values.get("maker_id", None, int)
                receive_data_dict['invoice_type_id'] = request.values.get("invoice_type_id", None, str)
                receive_data_dict['invoice_state_id'] = request.values.get("invoice_state_id", None, str)
                receive_data_dict['storeman_id'] = request.values.get("storeman_id", None, int)
                receive_data_dict['outgoingType_id'] = request.values.get("outgoingType_id", None, str)
                receive_data_dict['purchaseUnit_id'] = request.values.get("purchaseUnit_id", None, int)
                receive_data_dict['deliver_handler_id'] = request.values.get("deliver_handler_id", None, int)
                receive_data_dict['stock_direction_id'] = request.values.get("stock_direction_id", None, str)
                receive_data_dict['warehouse_id'] = request.values.get("warehouse_id", None, int)
                receive_data_dict['salesman_id'] = request.values.get("salesman_id", None, int)
                receive_data_dict['department_id'] = request.values.get("department_id", None, int)
                receive_data_dict['remarks'] = request.values.get("remarks", None, str)
                strmaterial_datas = request.values.get("rows")
                receive_data_dict['rows'] = json.loads(strmaterial_datas)

                if receive_data_dict.get('invoice_number') is None:
                    raise CodeError(ServiceCode.service_exception, msg=u"单据单号为None，该值错误")
                if receive_data_dict.get('maker_id') is None:
                    raise CodeError(ServiceCode.service_exception, msg=u"制单人参数为None，该值错误")
                if receive_data_dict.get('invoice_type_id') is None:
                    raise CodeError(ServiceCode.service_exception, msg=u"单据类型参数为None， 该值错误")
                if receive_data_dict.get('invoice_state_id') is None:
                    raise CodeError(ServiceCode.service_exception, msg=u"单据状态参数为None， 该值错误")
                if receive_data_dict.get('storeman_id') is None:
                    raise CodeError(ServiceCode.service_exception, msg=u"保管员参数为None， 该值错误")
                if receive_data_dict.get('outgoingType_id') is None:
                    raise CodeError(ServiceCode.service_exception, msg=u"出库类型参数为None， 该值错误")
                if receive_data_dict.get('purchaseUnit_id') is None:
                    raise CodeError(ServiceCode.service_exception, msg=u"客户参数为None， 该值错误")
                if receive_data_dict.get('deliver_handler_id') is None:
                    raise CodeError(ServiceCode.service_exception, msg=u"发货员参数为None， 该值错误")
                if receive_data_dict.get('stock_direction_id') is None:
                    raise CodeError(ServiceCode.service_exception, msg=u"库存方向参数为None， 该值错误")

                sell_op = SellWarehousOutOp()
                sell_op.update_invoice_data(receive_data_dict)
                sell_op.commit_invoice_data(receive_data_dict['invoice_number'])
            except CodeError as e:
                return_data = e.json_value()
            except Exception:
                SystemLog.pub_warninglog(traceback.format_exc())
                return_data = {'code': ServiceCode.service_exception, 'msg': u'服务器错误'}
            else:
                return_data = {
                    'code': ServiceCode.success,
                    'msg' : u"保存成功"
                }
            finally:
                return tools.en_return_data(json.dumps(return_data))


add_url.add_url(u'出库管理',
                'warehouse_manage.index',
                add_url.TYPE_ENTRY,
                warehouse_manage_prefix,
                warehouse_manage,
                '/warehouse_manage/warehouse_out/',
                'warehouse_out_manage',
                WarehouseOutManagement.as_view('warehouse_out_manage'),
                90,
                methods=['GET'])

add_url.add_url(u'销售出库',
                'warehouse_manage.warehouse_out_manage',
                add_url.TYPE_ENTRY,
                warehouse_manage_prefix,
                warehouse_manage,
                '/warehouse_manage/warehouse_out/sell_warehouse_out/',
                'sell_warehouse_out',
                WarehouseSellView.as_view('sell_warehouse_out'),
                100,
                methods=['GET'])

add_url.add_url(u'新建销售出库单',
                'warehouse_manage.sell_warehouse_out',
                add_url.TYPE_FEATURE,
                warehouse_manage_prefix,
                warehouse_manage,
                '/warehouse_manage/warehouse_out/sell_warehouse_out/create_warehouse_order/',
                'create_sell_warehouse_order',
                CreateSellWarehouseOutOrder.as_view('create_sell_warehouse_order'),
                methods=['GET'])

add_url.add_url(u'复制销售出库单',
                'warehouse_manage.sell_warehouse_out',
                add_url.TYPE_FEATURE,
                warehouse_manage_prefix,
                warehouse_manage,
                '/warehouse_manage/warehouse_out/sell_warehouse_out/copy_warehouse_order/',
                'copy_sell_warehouse_order',
                CopySellWarehouseOutOrder.as_view('copy_sell_warehouse_order'),
                methods=['GET'])

add_url.add_url(u'修改销售出库单',
                'warehouse_manage.sell_warehouse_out',
                add_url.TYPE_FEATURE,
                warehouse_manage_prefix,
                warehouse_manage,
                '/warehouse_manage/warehouse_out/sell_warehouse_out/modify_warehouse_order/',
                'modify_sell_warehouse_order',
                ModifySellWarehouseOutOrder.as_view('modify_sell_warehouse_order'),
                methods=['GET'])

add_url.add_url(u'删除销售出库单据',
                'warehouse_manage.sell_warehouse_out',
                add_url.TYPE_FEATURE,
                warehouse_manage_prefix,
                warehouse_manage,
                '/warehouse_manage/warehouse_out/sell_warehouse_out/delete_warehouse_order/',
                'delete_sell_warehouse_order',
                DeleteSellWarehouseOutOrder.as_view('delete_sell_warehouse_order'),
                methods=['POST'])

add_url.add_url(u'销售出库页面搜索或分页',
                'warehouse_manage.sell_warehouse_out',
                add_url.TYPE_FEATURE,
                warehouse_manage_prefix,
                warehouse_manage,
                '/warehouse_manage/warehouse_out/sell_warehouse_out/search_sell_order/',
                'search_sell_warehouse',
                WarehouseSellSearchView.as_view('search_sell_warehouse'),
                methods=['POST'])

add_url.add_url(u'保存或提交新建的销售出库单',
                'warehouse_manage.create_sell_warehouse_order',
                add_url.TYPE_FEATURE,
                warehouse_manage_prefix,
                warehouse_manage,
                '/warehouse_manage/warehouse_out/sell_warehouse_out/create_warehouse_order/save_order/',
                'save_sell_warehouse_order',
                SaveCreateSellWarehouseOrder.as_view('save_sell_warehouse_order'),
                methods=['POST'])

add_url.add_url(u'保存或提交复制的销售出库单',
                'warehouse_manage.copy_sell_warehouse_order',
                add_url.TYPE_FEATURE,
                warehouse_manage_prefix,
                warehouse_manage,
                '/warehouse_manage/warehouse_out/sell_warehouse_out/copy_warehouse_order/save_order/',
                'copy_save_sell_warehouse_order',
                SaveCopySellWarehouseOrder.as_view('copy_save_sell_warehouse_order'),
                methods=['POST'])

add_url.add_url(u'保存或提交修改的销售出库单',
                'warehouse_manage.modify_sell_warehouse_order',
                add_url.TYPE_FEATURE,
                warehouse_manage_prefix,
                warehouse_manage,
                '/warehouse_manage/warehouse_out/sell_warehouse_out/modify_warehouse_order/save_order/',
                'modify_save_sell_warehouse_order',
                SaveModifySellWarehouseOrder.as_view('modify_save_sell_warehouse_order'),
                methods=['POST'])

add_url.add_url(u'新建销售出库页面产品代码选择',
                'warehouse_manage.sell_warehouse_out',
                add_url.TYPE_FEATURE,
                warehouse_manage_prefix,
                warehouse_manage,
                '/warehouse_manage/warehouse_out/sell_warehouse_out/create_warehouse_order/select_material/',
                'select_sell_material_info',
                CreateSellProductSelect.as_view('select_sell_material_info'),
                methods=['POST'])

add_url.add_url(u'新建销售出库页面发货仓库选择',
                'warehouse_manage.sell_warehouse_out',
                add_url.TYPE_FEATURE,
                warehouse_manage_prefix,
                warehouse_manage,
                '/warehouse_manage/warehouse_out/sell_warehouse_out/create_warehouse_order/select_warehouse/',
                'select_sell_warehouse_info',
                CreateSellWarehouseSelect.as_view('select_sell_warehouse_info'),
                methods=['POST'])

add_url.add_url(u'新建销售出库页面部门组织选择',
                'warehouse_manage.sell_warehouse_out',
                add_url.TYPE_FEATURE,
                warehouse_manage_prefix,
                warehouse_manage,
                '/warehouse_manage/warehouse_out/sell_warehouse_out/create_warehouse_order/select_department/',
                'select_sell_department_info',
                CreateSellDepartmentSelect.as_view('select_sell_department_info'),
                methods=['POST'])

add_url.add_url(u'新建销售出库页面购货单位选择',
                'warehouse_manage.sell_warehouse_out',
                add_url.TYPE_FEATURE,
                warehouse_manage_prefix,
                warehouse_manage,
                '/warehouse_manage/warehouse_out/sell_warehouse_out/create_warehouse_order/select_customer/',
                'select_sell_customer_info',
                CreateSellCustomerSelect.as_view('select_sell_customer_info'),
                methods=['POST'])

add_url.add_url(u'新建销售出库单保管员发货员业务员选择',
                'warehouse_manage.sell_warehouse_out',
                add_url.TYPE_FEATURE,
                warehouse_manage_prefix,
                warehouse_manage,
                '/warehouse_manage/warehouse_out/sell_warehouse_out/create_warehouse_order/select_worker/',
                'select_sell_worker_info',
                CreateSellWorkerSelect.as_view('select_sell_worker_info'),
                methods=['POST'])

add_url.add_url(u'新建销售出库页面即时库存查询',
                'warehouse_manage.sell_warehouse_out',
                add_url.TYPE_FEATURE,
                warehouse_manage_prefix,
                warehouse_manage,
                '/warehouse_manage/warehouse_out/sell_warehouse_out/create_warehouse_order/query_current_repertory/',
                'sell_warehouse_repertory',
                CreateSellQueryCurRepertory.as_view('sell_warehouse_repertory'),
                methods=['POST'])

add_url.add_url(u'新建销售出库页面校验单据单号唯一性',
                'warehouse_manage.sell_warehouse_out',
                add_url.TYPE_FEATURE,
                warehouse_manage_prefix,
                warehouse_manage,
                '/warehouse_manage/warehouse_out/sell_warehouse_out/create_warehouse_order/verify_invoice_number/',
                'sell_warehouse_unique_order',
                CreateSellVerifyOrderUnique.as_view('sell_warehouse_unique_order'),
                methods=['POST'])

add_url.add_url(u'提交新建的销售出库单',
                'warehouse_manage.create_sell_warehouse_order',
                add_url.TYPE_FEATURE,
                warehouse_manage_prefix,
                warehouse_manage,
                '/warehouse_manage/warehouse_out/sell_warehouse_out/create_warehouse_order/submit_order/',
                'submit_sell_warehouse_order',
                SubmitCreateSellWarehouseOrder.as_view('submit_sell_warehouse_order'),
                methods=['POST'])

add_url.add_url(u'提交复制的销售出库单',
                'warehouse_manage.copy_sell_warehouse_order',
                add_url.TYPE_FEATURE,
                warehouse_manage_prefix,
                warehouse_manage,
                '/warehouse_manage/warehouse_out/sell_warehouse_out/copy_warehouse_order/submit_order/',
                'copy_submit_sell_warehouse_order',
                SubmitCopySellWarehouseOrder.as_view('copy_submit_sell_warehouse_order'),
                methods=['POST'])

add_url.add_url(u'提交修改的销售出库单',
                'warehouse_manage.modify_sell_warehouse_order',
                add_url.TYPE_FEATURE,
                warehouse_manage_prefix,
                warehouse_manage,
                '/warehouse_manage/warehouse_out/sell_warehouse_out/modify_warehouse_order/submit_order/',
                'modify_submit_sell_warehouse_order',
                SubmitModifySellWarehouseOrder.as_view('modify_submit_sell_warehouse_order'),
                methods=['POST'])

