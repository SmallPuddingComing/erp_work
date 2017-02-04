#!/usr/bin/python
# -*- coding:utf-8 -*-
#    Copyright(c) 2015-2016 JmGo Company
#    All rights reserved.
#
#    文件名 : other_invoices.py
#    作者   : tangjinxing
#  电子邮箱 :
#    日期   : 2016年12月30日14:08:51
#
#     描述  :
#

import datetime
from flask.views import MethodView
from flask import request
from flask import json
import traceback
from public.exception.custom_exception import CodeError
from config.service_config.returncode import ServiceCode
from control_center.admin import add_url
from public.function import tools
from public.logger.syslog import SystemLog
from control_center.warehouse_manage.base_view import warehouse_manage, warehouse_manage_prefix
from control_center.warehouse_manage.in_warehouse_manage.control.other_in_warehouse_op import OtherInWarehouseOp
from config.share.share_define import WarehouseManagementAttr
from data_mode.erp_supply.base_op.warehouse_manage_op.warehouse_op import WarehouseManageBaseOp


class InOtherInStock(MethodView):
    """
    其它入库
    """
    @staticmethod
    def get():
        r_data = {}
        return_data = {}
        try:
            print "*************InOtherInStock******************"
            print request.values
            wh_op = WarehouseManageBaseOp()
            other_op = OtherInWarehouseOp()
            # 获取所有的单据状态
            state_list = wh_op.get_invoice_state(WarehouseManagementAttr.INVOICE_STATE)
            # 获取所有的单据类型
            type_list = wh_op.get_red_blue_invoice_type()
            m_list, total = other_op.get_other_list_info(1, 10)
            # 其它入库类型
            other_storage_type_list = wh_op.get_other_warehousein_type()

            return_data["other_storage_type_list"] = other_storage_type_list
            return_data["code"] = ServiceCode.success
            return_data["total"] = total
            return_data["rows"] = m_list
            return_data["invoice_color"] = WarehouseManagementAttr.BLUE_ORDER_DIRECTION
            return_data["invoice_state_list"] = state_list
            return_data["invoice_type_list"] = type_list
            return_data["start_time"] = datetime.datetime.now().strftime("%Y-%m-%d")
            return_data["stop_time"] = datetime.datetime.now().strftime("%Y-%m-%d")
            pass
        except CodeError as e:
            print traceback.format_exc()
            return_data = json.dumps(e.json_value())
        except Exception:
            print traceback.format_exc()
            SystemLog.pub_warninglog(traceback.format_exc())
            return_data = json.dumps(
                {'code': ServiceCode.service_exception, 'msg': u"服务器失败", 'rows': r_data})
        finally:
            return tools.en_render_template("/warehouseManagement/instorage_management/other_inStock.html",
                                            result=json.dumps(return_data))

    @staticmethod
    def post():
        """
        搜搜 翻页
        :return:
        """
        r_data = {}
        return_data = {}
        try:
            print "****************搜索翻页***************************"
            print request.values
            search_dict = dict()
            page = request.values.get("page", 1, int)
            pagecount = request.values.get("pagecount", 10, int)
            search_dict["invoice_number"] = request.values.get("invoice_number", None, str)
            search_dict["start_time"] = request.values.get("start_time", None, str)
            search_dict["stop_time"] = request.values.get("stop_time", None, str)
            search_dict["invoice_type_id"] = request.values.get("invoice_type", None, str)
            search_dict["invoice_state_id"] = request.values.get("invoice_state", None, str)
            search_dict["other_storage_type_id"] = request.values.get("other_storage_type_id", None, str)
            if page <= 0 or pagecount <= 0:
                raise CodeError(300, u"参数错误")

            other_op = OtherInWarehouseOp()
            m_list, total = other_op.get_other_list_info(page, pagecount, search_dict=search_dict)
            return_data = json.dumps({
                "code": ServiceCode.success,
                "total": total,
                "rows": m_list
            })

            pass
        except CodeError as e:
            print traceback.format_exc()
            return_data = json.dumps(e.json_value())
        except Exception:
            print traceback.format_exc()
            SystemLog.pub_warninglog(traceback.format_exc())
            return_data = json.dumps(
                {'code': ServiceCode.service_exception, 'msg': u"服务器失败", 'rows': r_data})
        finally:
            return tools.en_return_data(return_data)


class InCreateOtherCheckInvoice(MethodView):
    """
    新建--单据单号唯一性检查
    """
    @staticmethod
    def get():
        r_data = {}
        return_data = {}
        try:
            invoice_number = request.values.get("invoice_number", None, str)
            if invoice_number is None or invoice_number is "" or invoice_number is u"":
                raise CodeError(300, u"参数错误")
            op = OtherInWarehouseOp()
            rs = op.check_other_invoice_number(invoice_number)
            if not rs:
                return_data = return_data = json.dumps(
                    {'code': ServiceCode.success, 'msg': u"服务器成功"})
            else:
                return_data = json.dumps(
                    {'code': ServiceCode.service_exception, 'msg': u"服务器失败", 'rows': r_data})
            pass
        except CodeError as e:
            print traceback.format_exc()
            return_data = json.dumps(e.json_value())
        except Exception:
            print traceback.format_exc()
            SystemLog.pub_warninglog(traceback.format_exc())
            return_data = json.dumps(
                {'code': ServiceCode.service_exception, 'msg': u"服务器失败", 'rows': r_data})
        finally:
            return tools.en_return_data(return_data)


class InCreateOtherInStock(MethodView):
    """
    新建其它入库单
    """
    @staticmethod
    def get():
        r_data = {}
        return_data = {}
        try:
            print "*******************InCreateOtherInStock*********************"
            print request.values
            invoice_type_id = request.values.get("invoice_type_id", None, str)

            other_op = OtherInWarehouseOp()
            wh_op = WarehouseManageBaseOp()
            return_data = other_op.get_crate_other_info(invoice_type_id)
            # 获取所有的人员，部门组织，供应商，仓库信息
            r_data = other_op.get_all_search_info()
            return_data["code"] = ServiceCode.success
            return_data["page_type"] = 1
            return_data["person_data"] = r_data["person_data"]
            return_data["supplier_data"] = r_data["supplier_data"]
            return_data["department_data"] = r_data["department_data"]
            return_data["warehouse_data"] = r_data["warehouse_data"]
            # 其它入库类型
            other_storage_type_list = wh_op.get_other_warehousein_type()
            return_data["other_storage_type_list"] = other_storage_type_list
            return_data = json.dumps(return_data)
            pass
        except CodeError as e:
            print traceback.format_exc()
            return_data = json.dumps(e.json_value())
        except Exception:
            print traceback.format_exc()
            SystemLog.pub_warninglog(traceback.format_exc())
            return_data = json.dumps(
                {'code': ServiceCode.service_exception, 'msg': u"服务器失败", 'rows': r_data})
        finally:
            print '_____________________________________________________'
            return tools.en_render_template("/warehouseManagement/instorage_management/addOther_inStock.html",
                                            result=return_data)

    @staticmethod
    def post():
        """
        新建其它入库单信息保存
        :return:
        """
        r_data = {}
        return_data = {}
        try:
            print "***********save_other_invoice**************"
            print request.values
            invoice_info = dict()
            invoice_info["invoice_number"] = request.values.get("invoice_number", None, str)
            invoice_info["invoice_date"] = request.values.get("invoice_date", None, str)
            invoice_info["maker_id"] = request.values.get("maker_id", None, str)
            invoice_info["invoice_type_id"] = request.values.get("invoice_type_id", None, str)
            invoice_info["invoice_state_id"] = request.values.get("invoice_state_id", None, str)
            invoice_info["inspector_id"] = request.values.get("inspector_id", None, int)
            invoice_info["other_storage_type_id"] = request.values.get("other_storage_type_id", None, str)
            invoice_info["supplier_id"] = request.values.get("supplier_id", None, int)
            invoice_info["storeman_id"] = request.values.get("storeman_id", None, int)
            invoice_info["stock_direction_id"] = request.values.get("stock_direction_id", None, str)
            invoice_info["warehouse_id"] = request.values.get("warehouse_id", None, int)
            invoice_info["salesman_id"] = request.values.get("salesman_id", None, int)
            invoice_info["department_id"] = request.values.get("department_id", None, int)
            invoice_info["remarks"] = request.values.get("remarks", None, int)
            rows = request.values.get("rows", None)
            rows = json.loads(rows)
            invoice_info["rows"] = rows
            op = OtherInWarehouseOp()
            rs = op.save_other_info(invoice_info)
            if not rs:
                raise CodeError(ServiceCode.service_exception, u"服务器失败")
            return_data = json.dumps(
                {'code': ServiceCode.success, 'msg': u"服务器成功", 'rows': r_data})
            pass
        except CodeError as e:
            print traceback.format_exc()
            return_data = json.dumps(e.json_value())
        except Exception:
            print traceback.format_exc()
            SystemLog.pub_warninglog(traceback.format_exc())
            return_data = json.dumps(
                {'code': ServiceCode.service_exception, 'msg': u"服务器失败", 'rows': r_data})
        finally:
            return tools.en_return_data(return_data)


class InCopyOtherInStock(MethodView):
    """
    其它入库单据复制
    """
    @staticmethod
    def get():
        """
        页面渲染
        :return:
        """
        r_data = {}
        return_data = {}
        try:
            print "***********************InCopyOtherInStock***********************"
            print request.values
            invoice_number = request.values.get("invoice_number", None, str)

            other_op = OtherInWarehouseOp()
            wh_op = WarehouseManageBaseOp()
            return_data = other_op.get_copy_other_info(invoice_number)
            # 获取所有的人员，部门组织，供应商，仓库信息
            r_data = other_op.get_all_search_info()
            return_data["code"] = ServiceCode.success
            return_data["page_type"] = 2
            return_data["person_data"] = r_data["person_data"]
            return_data["supplier_data"] = r_data["supplier_data"]
            return_data["department_data"] = r_data["department_data"]
            return_data["warehouse_data"] = r_data["warehouse_data"]
            # 其它入库类型
            other_storage_type_list = wh_op.get_other_warehousein_type()
            return_data["other_storage_type_list"] = other_storage_type_list
            return_data = json.dumps(return_data)
            pass
        except CodeError as e:
            print traceback.format_exc()
            return_data = json.dumps(e.json_value())
        except Exception:
            print traceback.format_exc()
            SystemLog.pub_warninglog(traceback.format_exc())
            return_data = json.dumps(
                {'code': ServiceCode.service_exception, 'msg': u"服务器失败", 'rows': r_data})
        finally:
            return tools.en_render_template("/warehouseManagement/instorage_management/addOther_inStock.html",
                                            result=return_data)

    @staticmethod
    def post():
        """
        复制--其它入库单信息保存
        :return:
        """
        r_data = {}
        return_data = {}
        try:
            print "***********save_other_invoice**************"
            print request.values
            invoice_info = dict()
            invoice_info["invoice_number"] = request.values.get("invoice_number", None, str)
            invoice_info["invoice_date"] = request.values.get("invoice_date", None, str)
            invoice_info["maker_id"] = request.values.get("maker_id", None, str)
            invoice_info["invoice_type_id"] = request.values.get("invoice_type_id", None, str)
            invoice_info["invoice_state_id"] = request.values.get("invoice_state_id", None, str)
            invoice_info["inspector_id"] = request.values.get("inspector_id", None, int)
            invoice_info["other_storage_type_id"] = request.values.get("other_storage_type_id", None, str)
            invoice_info["supplier_id"] = request.values.get("supplier_id", None, int)
            invoice_info["storeman_id"] = request.values.get("storeman_id", None, int)
            invoice_info["stock_direction_id"] = request.values.get("stock_direction_id", None, str)
            invoice_info["warehouse_id"] = request.values.get("warehouse_id", None, int)
            invoice_info["salesman_id"] = request.values.get("salesman_id", None, int)
            invoice_info["department_id"] = request.values.get("department_id", None, int)
            invoice_info["remarks"] = request.values.get("remarks", None, int)
            rows = request.values.get("rows", None)
            rows = json.loads(rows)
            invoice_info["rows"] = rows
            op = OtherInWarehouseOp()
            rs = op.save_other_info(invoice_info)
            if not rs:
                raise CodeError(ServiceCode.service_exception, u"服务器失败")
            return_data = json.dumps(
                {'code': ServiceCode.success, 'msg': u"服务器成功", 'rows': r_data})
            pass
        except CodeError as e:
            print traceback.format_exc()
            return_data = json.dumps(e.json_value())
        except Exception:
            print traceback.format_exc()
            SystemLog.pub_warninglog(traceback.format_exc())
            return_data = json.dumps(
                {'code': ServiceCode.service_exception, 'msg': u"服务器失败", 'rows': r_data})
        finally:
            return tools.en_return_data(return_data)


class InUpdateOtherInStock(MethodView):
    """
    其它入库单据修改
    """
    @staticmethod
    def get():
        """
        页面渲染
        :return:
        """
        r_data = {}
        return_data = {}
        try:
            print "***********************InUpdateOtherInStock***********************"
            print request.values
            invoice_number = request.values.get("invoice_number", None, str)

            other_op = OtherInWarehouseOp()
            wh_op = WarehouseManageBaseOp()
            return_data = other_op.get_update_other_info(invoice_number)
            # 获取所有的人员，部门组织，供应商，仓库信息
            r_data = other_op.get_all_search_info()
            return_data["code"] = ServiceCode.success
            return_data["page_type"] = 3
            return_data["person_data"] = r_data["person_data"]
            return_data["supplier_data"] = r_data["supplier_data"]
            return_data["department_data"] = r_data["department_data"]
            return_data["warehouse_data"] = r_data["warehouse_data"]
            # 其它入库类型
            other_storage_type_list = wh_op.get_other_warehousein_type()
            return_data["other_storage_type_list"] = other_storage_type_list
            return_data = json.dumps(return_data)
            pass
        except CodeError as e:
            print traceback.format_exc()
            return_data = json.dumps(e.json_value())
        except Exception:
            print traceback.format_exc()
            SystemLog.pub_warninglog(traceback.format_exc())
            return_data = json.dumps(
                {'code': ServiceCode.service_exception, 'msg': u"服务器失败", 'rows': r_data})
        finally:
            return tools.en_render_template("/warehouseManagement/instorage_management/addOther_inStock.html",
                                            result=return_data)

    @staticmethod
    def post():
        """
        修改--其它入库单信息保存
        :return:
        """
        r_data = {}
        return_data = {}
        try:
            print "***********save_other_invoice**************"
            print request.values
            invoice_info = dict()
            invoice_info["invoice_number"] = request.values.get("invoice_number", None, str)
            invoice_info["invoice_date"] = request.values.get("invoice_date", None, str)
            invoice_info["maker_id"] = request.values.get("maker_id", None, str)
            invoice_info["invoice_type_id"] = request.values.get("invoice_type_id", None, str)
            invoice_info["invoice_state_id"] = request.values.get("invoice_state_id", None, str)
            invoice_info["inspector_id"] = request.values.get("inspector_id", None, int)
            invoice_info["other_storage_type_id"] = request.values.get("other_storage_type_id", None, str)
            invoice_info["supplier_id"] = request.values.get("supplier_id", None, int)
            invoice_info["storeman_id"] = request.values.get("storeman_id", None, int)
            invoice_info["stock_direction_id"] = request.values.get("stock_direction_id", None, str)
            invoice_info["warehouse_id"] = request.values.get("warehouse_id", None, int)
            invoice_info["salesman_id"] = request.values.get("salesman_id", None, int)
            invoice_info["department_id"] = request.values.get("department_id", None, int)
            invoice_info["remarks"] = request.values.get("remarks", None, int)
            rows = request.values.get("rows", None)
            rows = json.loads(rows)
            invoice_info["rows"] = rows
            op = OtherInWarehouseOp()
            rs = op.update_other_info(invoice_info)
            if not rs:
                raise CodeError(ServiceCode.service_exception, u"服务器失败")
            return_data = json.dumps(
                {'code': ServiceCode.success, 'msg': u"服务器成功", 'rows': r_data})
            pass
        except CodeError as e:
            print traceback.format_exc()
            return_data = json.dumps(e.json_value())
        except Exception:
            print traceback.format_exc()
            SystemLog.pub_warninglog(traceback.format_exc())
            return_data = json.dumps(
                {'code': ServiceCode.service_exception, 'msg': u"服务器失败", 'rows': r_data})
        finally:
            return tools.en_return_data(return_data)


class CommitOtherInCreate(MethodView):
    """
    新建其它入库提交
    """
    @staticmethod
    def post():
        return_data = {}
        r_data = {}
        try:
            print "***********commit_other_invoice_create**************"
            print request.values
            invoice_info = dict()
            invoice_info["invoice_number"] = request.values.get("invoice_number", None, str)
            invoice_info["invoice_date"] = request.values.get("invoice_date", None, str)
            invoice_info["maker_id"] = request.values.get("maker_id", None, str)
            invoice_info["invoice_type_id"] = request.values.get("invoice_type_id", None, str)
            invoice_info["invoice_state_id"] = request.values.get("invoice_state_id", None, str)
            invoice_info["inspector_id"] = request.values.get("inspector_id", None, int)
            invoice_info["other_storage_type_id"] = request.values.get("other_storage_type_id", None, str)
            invoice_info["supplier_id"] = request.values.get("supplier_id", None, int)
            invoice_info["storeman_id"] = request.values.get("storeman_id", None, int)
            invoice_info["stock_direction_id"] = request.values.get("stock_direction_id", None, str)
            invoice_info["warehouse_id"] = request.values.get("warehouse_id", None, int)
            invoice_info["salesman_id"] = request.values.get("salesman_id", None, int)
            invoice_info["department_id"] = request.values.get("department_id", None, int)
            invoice_info["remarks"] = request.values.get("remarks", None, int)
            rows = request.values.get("rows", None)
            rows = json.loads(rows)
            invoice_info["rows"] = rows
            op = OtherInWarehouseOp()
            r_check = op.check_other_invoice_number(invoice_info["invoice_number"])
            if r_check:
                rs = op.update_other_info(invoice_info)
            else:
                rs = op.save_other_info(invoice_info)
            # 更新库存
            rs_commit = op.commit_other_info(invoice_info)
            if not rs:
                raise CodeError(ServiceCode.service_exception, u"服务器失败")
            return_data = json.dumps(
                {'code': ServiceCode.success, 'msg': u"服务器成功", 'rows': r_data})
            pass
        except CodeError as e:
            print traceback.format_exc()
            SystemLog.pub_warninglog(traceback.format_exc())
            return_data = json.dumps(e.json_value())
        except Exception:
            print traceback.format_exc()
            SystemLog.pub_warninglog(traceback.format_exc())
            return_data = json.dumps(
                {'code': ServiceCode.service_exception, 'msg': u"服务器失败", 'rows': r_data})
        return tools.en_return_data(return_data)


class CommitOtherInCopy(MethodView):
    """
    复制其它入库提交
    """
    @staticmethod
    def post():
        return_data = {}
        r_data = {}
        try:
            print "***********commit_other_invoice_copy**************"
            print request.values
            invoice_info = dict()
            invoice_info["invoice_number"] = request.values.get("invoice_number", None, str)
            invoice_info["invoice_date"] = request.values.get("invoice_date", None, str)
            invoice_info["maker_id"] = request.values.get("maker_id", None, str)
            invoice_info["invoice_type_id"] = request.values.get("invoice_type_id", None, str)
            invoice_info["invoice_state_id"] = request.values.get("invoice_state_id", None, str)
            invoice_info["inspector_id"] = request.values.get("inspector_id", None, int)
            invoice_info["other_storage_type_id"] = request.values.get("other_storage_type_id", None, str)
            invoice_info["supplier_id"] = request.values.get("supplier_id", None, int)
            invoice_info["storeman_id"] = request.values.get("storeman_id", None, int)
            invoice_info["stock_direction_id"] = request.values.get("stock_direction_id", None, str)
            invoice_info["warehouse_id"] = request.values.get("warehouse_id", None, int)
            invoice_info["salesman_id"] = request.values.get("salesman_id", None, int)
            invoice_info["department_id"] = request.values.get("department_id", None, int)
            invoice_info["remarks"] = request.values.get("remarks", None, int)
            rows = request.values.get("rows", None)
            rows = json.loads(rows)
            invoice_info["rows"] = rows
            op = OtherInWarehouseOp()
            r_check = op.check_other_invoice_number(invoice_info["invoice_number"])
            if r_check:
                rs = op.update_other_info(invoice_info)
            else:
                rs = op.save_other_info(invoice_info)
            # 更新库存
            rs_commit = op.commit_other_info(invoice_info)
            if not rs:
                raise CodeError(ServiceCode.service_exception, u"服务器失败")
            return_data = json.dumps(
                {'code': ServiceCode.success, 'msg': u"服务器成功", 'rows': r_data})
            pass
        except CodeError as e:
            print traceback.format_exc()
            SystemLog.pub_warninglog(traceback.format_exc())
            return_data = json.dumps(e.json_value())
        except Exception:
            print traceback.format_exc()
            SystemLog.pub_warninglog(traceback.format_exc())
            return_data = json.dumps(
                {'code': ServiceCode.service_exception, 'msg': u"服务器失败", 'rows': r_data})
        return tools.en_return_data(return_data)


class CommitOtherInUpdate(MethodView):
    """
    修改其它入库提交
    """
    @staticmethod
    def post():
        return_data = {}
        r_data = {}
        try:
            print "***********commit_other_invoice_update**************"
            print request.values
            invoice_info = dict()
            invoice_info["invoice_number"] = request.values.get("invoice_number", None, str)
            invoice_info["invoice_date"] = request.values.get("invoice_date", None, str)
            invoice_info["maker_id"] = request.values.get("maker_id", None, str)
            invoice_info["invoice_type_id"] = request.values.get("invoice_type_id", None, str)
            invoice_info["invoice_state_id"] = request.values.get("invoice_state_id", None, str)
            invoice_info["inspector_id"] = request.values.get("inspector_id", None, int)
            invoice_info["other_storage_type_id"] = request.values.get("other_storage_type_id", None, str)
            invoice_info["supplier_id"] = request.values.get("supplier_id", None, int)
            invoice_info["storeman_id"] = request.values.get("storeman_id", None, int)
            invoice_info["stock_direction_id"] = request.values.get("stock_direction_id", None, str)
            invoice_info["warehouse_id"] = request.values.get("warehouse_id", None, int)
            invoice_info["salesman_id"] = request.values.get("salesman_id", None, int)
            invoice_info["department_id"] = request.values.get("department_id", None, int)
            invoice_info["remarks"] = request.values.get("remarks", None, int)
            rows = request.values.get("rows", None)
            rows = json.loads(rows)
            invoice_info["rows"] = rows
            op = OtherInWarehouseOp()
            r_check = op.check_other_invoice_number(invoice_info["invoice_number"])
            if r_check:
                rs = op.update_other_info(invoice_info)
            else:
                rs = op.save_other_info(invoice_info)
            # 更新库存
            rs_commit = op.commit_other_info(invoice_info)
            if not rs:
                raise CodeError(ServiceCode.service_exception, u"服务器失败")
            return_data = json.dumps(
                {'code': ServiceCode.success, 'msg': u"服务器成功", 'rows': r_data})
            pass
        except CodeError as e:
            print traceback.format_exc()
            SystemLog.pub_warninglog(traceback.format_exc())
            return_data = json.dumps(e.json_value())
        except Exception:
            print traceback.format_exc()
            SystemLog.pub_warninglog(traceback.format_exc())
            return_data = json.dumps(
                {'code': ServiceCode.service_exception, 'msg': u"服务器失败", 'rows': r_data})
        return tools.en_return_data(return_data)


class InDeleteOtherInStock(MethodView):
    """
    其它入库单据删除
    """
    @staticmethod
    def post():
        r_data = {}
        return_data = {}
        try:
            print "*********************InDeleteOtherInStock**********************"
            invoice_number = request.values.get("invoice_number", None, str)

            op = OtherInWarehouseOp()
            rs = op.other_invoice_delete(invoice_number)
            pass
        except CodeError as e:
            return_data = json.dumps(e.json_value())
        except Exception:
            SystemLog.pub_warninglog(traceback.format_exc())
            return_data = json.dumps(
                {'code': ServiceCode.service_exception, 'msg': u"服务器失败", 'rows': r_data})
        else:
            return_data = json.dumps(
                {'code': ServiceCode.success, 'msg': u"服务器成功", 'rows': r_data})
        finally:
            return tools.en_return_data(return_data)


class InCreateOtherMaterialInfo(MethodView):
    """
    新建页面 获取物料信息
    """
    @staticmethod
    def get():
        r_data = {}
        return_data = {}
        try:
            from data_mode.erp_supply.base_op.material_op.baseinfo_op import Baseinfo_Op
            baseinfo_op = Baseinfo_Op()
            total, full_material_datas = baseinfo_op.get_all_material_info()

            from data_mode.erp_supply.base_op.material_op.attribute_op import Attribute_Op
            from config.share.share_define import SupplyAttr
            material_attr_op = Attribute_Op()
            material_attr_list = material_attr_op.get_material_attribute(SupplyAttr.MATERIAL_ATTRIBUTE_TYPE)
            return_data = json.dumps({
                    'code': ServiceCode.success,
                    'total': total,
                    'material_datas': full_material_datas,
                    'material_attr_datas': material_attr_list
                })
            pass
        except CodeError as e:
            print traceback.format_exc()
            return_data = json.dumps(e.json_value())
        except Exception:
            print traceback.format_exc()
            SystemLog.pub_warninglog(traceback.format_exc())
            return_data = json.dumps(
                {'code': ServiceCode.service_exception, 'msg': u"服务器失败", 'rows': r_data})
        else:
            return_data = json.dumps(
                {'code': ServiceCode.success, 'msg': u"服务器成功", 'rows': r_data})
        finally:
            return tools.en_return_data(return_data)


class GetOtherOperateInfo(MethodView):
    """
    获取操作记录
    """
    @staticmethod
    def post():
        return_data = {}
        r_data = {}
        try:
            invoice_number = request.values.get("invoice_number", None, str)
            page = request.values.get("page", 1, int)
            pagecount = request.values.get("pagecount", 5, int)
            op = OtherInWarehouseOp()
            total, record_list = op.get_invoice_operate_record(invoice_number, page=page, per_page=pagecount)
            return_data = json.dumps({
                "code": ServiceCode.success,
                "total": total,
                "rows": record_list
            })
            pass
        except CodeError as e:
            print traceback.format_exc()
            return_data = json.dumps(e.json_value())
        except Exception:
            print traceback.format_exc()
            SystemLog.pub_warninglog(traceback.format_exc())
            return_data = json.dumps(
                {'code': ServiceCode.service_exception, 'msg': u"服务器失败", 'rows': r_data})
        finally:
            return tools.en_return_data(return_data)


add_url.add_url(u'其它入库',
                'warehouse_manage.InWarehouseManage',
                add_url.TYPE_ENTRY,
                warehouse_manage_prefix,
                warehouse_manage,
                '/in_other_instock/',
                'InOtherInStock',
                InOtherInStock.as_view('InOtherInStock'),
                80,
                methods=['GET', 'POST'])

add_url.add_url(u'新建其它入库单',
                'warehouse_manage.InOtherInStock',
                add_url.TYPE_FEATURE,
                warehouse_manage_prefix,
                warehouse_manage,
                '/in_create_other_instock/',
                'InCreateOtherInStock',
                InCreateOtherInStock.as_view('InCreateOtherInStock'),
                methods=['GET', 'POST'])

add_url.add_url(u"复制其它入库单",
                'warehouse_manage.InOtherInStock',
                add_url.TYPE_FEATURE,
                warehouse_manage_prefix,
                warehouse_manage,
                '/in_copy_other_instock/',
                'InCopyOtherInStock',
                InCopyOtherInStock.as_view('InCopyOtherInStock'),
                methods=['GET', 'POST']
                )

add_url.add_url(u"修改其它入库单",
                'warehouse_manage.InOtherInStock',
                add_url.TYPE_FEATURE,
                warehouse_manage_prefix,
                warehouse_manage,
                '/in_update_other/',
                'InUpdateOtherInStock',
                InUpdateOtherInStock.as_view('InUpdateOtherInStock'),
                methods=['GET', 'POST']
                )

add_url.add_url(u"删除其它入库单",
                'warehouse_manage.InOtherInStock',
                add_url.TYPE_FEATURE,
                warehouse_manage_prefix,
                warehouse_manage,
                '/in_delete_other_instock/',
                'InDeleteOtherInStock',
                InDeleteOtherInStock.as_view('InDeleteOtherInStock'),
                methods=['GET', 'POST']
                )


add_url.add_url(u"异步获取物料信息",
                'warehouse_manage.InOtherInStock',
                add_url.TYPE_FEATURE,
                warehouse_manage_prefix,
                warehouse_manage,
                '/in_create_other_material/',
                'InCreateOtherMaterialInfo',
                InCreateOtherMaterialInfo.as_view('InCreateOtherMaterialInfo'),
                methods=['GET']
                )


add_url.add_url(u"其它入库页面单据单号唯一性检查",
                'warehouse_manage.InOtherInStock',
                add_url.TYPE_FEATURE,
                warehouse_manage_prefix,
                warehouse_manage,
                '/in_check_create_other/',
                'InCreateOtherCheckInvoice',
                InCreateOtherCheckInvoice.as_view('InCreateOtherCheckInvoice'),
                methods=['GET']
                )

add_url.add_url(u"新建其它入库提交",
                'warehouse_manage.InCreateOtherInStock',
                add_url.TYPE_FEATURE,
                warehouse_manage_prefix,
                warehouse_manage,
                '/commit_other_in_create/',
                'CommitOtherInCreate',
                CommitOtherInCreate.as_view('CommitOtherInCreate'),
                methods=['POST']
                )

add_url.add_url(u"复制其它入库提交",
                'warehouse_manage.InCopyOtherInStock',
                add_url.TYPE_FEATURE,
                warehouse_manage_prefix,
                warehouse_manage,
                '/commit_other_in_copy/',
                'CommitOtherInCopy',
                CommitOtherInCopy.as_view('CommitOtherInCopy'),
                methods=['POST']
                )

add_url.add_url(u"修改其它入库提交",
                'warehouse_manage.InUpdateOtherInStock',
                add_url.TYPE_FEATURE,
                warehouse_manage_prefix,
                warehouse_manage,
                '/commit_other_in_update/',
                'CommitOtherInUpdate',
                CommitOtherInUpdate.as_view('CommitOtherInUpdate'),
                methods=['POST']
                )


add_url.add_url(u"获取其它入库操作记录",
                'warehouse_manage.InUpdateOutbuyInvoice',
                add_url.TYPE_FEATURE,
                warehouse_manage_prefix,
                warehouse_manage,
                '/get_other_record_info/',
                'GetOtherOperateInfo',
                GetOtherOperateInfo.as_view('GetOtherOperateInfo'),
                methods=['POST']
                )
