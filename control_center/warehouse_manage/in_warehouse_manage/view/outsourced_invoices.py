#!/usr/bin/python
# -*- coding:utf-8 -*-
#    Copyright(c) 2015-2016 JmGo Company
#    All rights reserved.
#
#    文件名 : outsourced_invoices.py
#    作者   : tangjinxing
#  电子邮箱 :
#    日期   : 2016年12月30日14:08:51
#
#     描述  :
#

from flask.views import MethodView
from flask import request
from flask import json
import traceback
import datetime
from public.exception.custom_exception import CodeError
from config.service_config.returncode import ServiceCode
from control_center.admin import add_url
from public.function import tools
from public.logger.syslog import SystemLog
from control_center.warehouse_manage.base_view import warehouse_manage, warehouse_manage_prefix
from control_center.warehouse_manage.in_warehouse_manage.control.outsourced_in_warehouse_op \
    import OutsourcedInWarehouseOp
from control_center.warehouse_manage.in_warehouse_manage.control.outbuy_in_warehouse_op import OutbuyInWarehouseOp
from data_mode.erp_supply.base_op.warehouse_manage_op.warehouse_op import WarehouseManageBaseOp
from config.share.share_define import WarehouseManagementAttr


class InOutSourced(MethodView):
    """
    委外加工入库
    """
    @staticmethod
    def get():
        r_data = {}
        return_data = {}
        try:
            print "*****************InOutSourced**********************"
            print request.values
            op = OutsourcedInWarehouseOp()
            invoice_list, total = op.get_outsourced_list_info(1, 10)
            wh_op = WarehouseManageBaseOp()
            outbuy_op = OutbuyInWarehouseOp()
            # 获取所有的单据状态
            state_list = wh_op.get_invoice_state(WarehouseManagementAttr.INVOICE_STATE)
            # 获取所有的单据类型
            type_list = wh_op.get_red_blue_invoice_type()
            return_data["code"] = ServiceCode.success
            return_data["total"] = total
            return_data["rows"] = invoice_list
            return_data["invoice_color"] = WarehouseManagementAttr.BLUE_ORDER_DIRECTION
            return_data["start_time"] = datetime.datetime.now().strftime("%Y-%m-%d")
            return_data["stop_time"] = datetime.datetime.now().strftime("%Y-%m-%d")
            return_data["invoice_state_list"] = state_list
            return_data["invoice_type_list"] = type_list
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
            return tools.en_render_template("/warehouseManagement/instorage_management/outsourcedProcessing.html",
                                            result=return_data)

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
            search_dict["invoice_type_id"] = request.values.get("invoice_type_id", None, str)
            search_dict["invoice_state_id"] = request.values.get("invoice_state_id", None, str)
            search_dict["processing_unit"] = request.values.get("processing_unit", None, str)
            if page <= 0 or pagecount <= 0:
                raise CodeError(300, u"参数错误")
            op = OutsourcedInWarehouseOp()
            outbuy_list, total = op.get_outsourced_list_info(page, pagecount, search_dict=search_dict)
            return_data = json.dumps({
                "code": ServiceCode.success,
                "total": total,
                "rows": outbuy_list
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


class InCreateOutSourced(MethodView):
    """
    新建委外加工入库单
    """
    @staticmethod
    def get():
        r_data = {}
        return_data = {}
        try:
            print "*******************InCreateOutbuyInvoice*********************"
            print request.values
            invoice_type_id = request.values.get("invoice_type_id", None, str)
            # page_type = request.values.get("page_type", 1, int)
            outsourced_op = OutsourcedInWarehouseOp()
            outbuy_op = OutbuyInWarehouseOp()
            return_data = outsourced_op.get_crate_outsourced_info(invoice_type_id)
            # 获取所有的人员，部门组织，供应商，仓库信息
            r_data = outbuy_op.get_all_search_info()
            return_data["code"] = ServiceCode.success
            return_data["page_type"] = 1
            return_data["person_data"] = r_data["person_data"]
            return_data["supplier_data"] = r_data["supplier_data"]
            return_data["department_data"] = r_data["department_data"]
            return_data["warehouse_data"] = r_data["warehouse_data"]
            # 获取委外类型
            return_data["outsourcing_type_list"] = outsourced_op.get_outsourced__type()
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
            return tools.en_render_template("/warehouseManagement/instorage_management/newOutsourcedProcessing.html",
                                            result=return_data)

    @staticmethod
    def post():
        """
        委外入库单信息保存
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
            invoice_info["outsource_type_id"] = request.values.get("outsource_type_id", None, str)
            invoice_info["supplier_id"] = request.values.get("supplier_id", None, int)
            invoice_info["storeman_id"] = request.values.get("storeman_id", None, int)
            invoice_info["stock_direction_id"] = request.values.get("stock_direction_id", None, str)
            invoice_info["warehouse_id"] = request.values.get("warehouse_id", None, int)
            invoice_info["salesman_id"] = request.values.get("salesman_id", None, int)
            invoice_info["processing_unit_id"] = request.values.get("processing_unit_id", None, int)
            invoice_info["remarks"] = request.values.get("remarks", None, str)
            invoice_info["freight_number"] = request.values.get("freight_number", None, str)

            rows = request.values.get("rows", None)
            rows = json.loads(rows)
            invoice_info["rows"] = rows
            op = OutsourcedInWarehouseOp()
            rs = op.save_outsourced_info(invoice_info)
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


class InCopyOutsourcedInvoice(MethodView):
    """
    委外加工入库单据复制
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
            print request.values
            invoice_number = request.values.get("invoice_number", None, str)
            if invoice_number is None or invoice_number is "" or invoice_number is u"":
                raise CodeError(300, u"参数错误")
            outbuy_op = OutbuyInWarehouseOp()
            outsourced_op = OutsourcedInWarehouseOp()
            return_data = outsourced_op.get_copy_outsourced_info(invoice_number)
            # 获取所有的人员，部门组织，供应商，仓库信息
            r_data = outbuy_op.get_all_search_info()
            return_data["code"] = ServiceCode.success
            return_data["page_type"] = 2
            return_data["person_data"] = r_data["person_data"]
            return_data["supplier_data"] = r_data["supplier_data"]
            return_data["department_data"] = r_data["department_data"]
            return_data["warehouse_data"] = r_data["warehouse_data"]
            # 获取委外类型
            return_data["outsourcing_type_list"] = outsourced_op.get_outsourced__type()
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
            return tools.en_render_template("/warehouseManagement/instorage_management/newOutsourcedProcessing.html",
                                            result=return_data)

    @staticmethod
    def post():
        """
        复制--委外入库单信息保存
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
            invoice_info["outsource_type_id"] = request.values.get("outsource_type_id", None, str)
            invoice_info["supplier_id"] = request.values.get("supplier_id", None, int)
            invoice_info["storeman_id"] = request.values.get("storeman_id", None, int)
            invoice_info["stock_direction_id"] = request.values.get("stock_direction_id", None, str)
            invoice_info["warehouse_id"] = request.values.get("warehouse_id", None, int)
            invoice_info["salesman_id"] = request.values.get("salesman_id", None, int)
            invoice_info["processing_unit_id"] = request.values.get("processing_unit_id", None, int)
            invoice_info["remarks"] = request.values.get("remarks", None, str)
            invoice_info["freight_number"] = request.values.get("freight_number", None, str)

            rows = request.values.get("rows", None)
            rows = json.loads(rows)
            invoice_info["rows"] = rows
            op = OutsourcedInWarehouseOp()
            rs = op.save_outsourced_info(invoice_info)
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


class InUpdateOutsourcedInvoice(MethodView):
    """
    委外加工入库单据修改
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
            print request.values
            invoice_number = request.values.get("invoice_number", None, str)
            if invoice_number is None or invoice_number is "" or invoice_number is u"":
                raise CodeError(300, u"参数错误")
            outbuy_op = OutbuyInWarehouseOp()
            outsourced_op = OutsourcedInWarehouseOp()
            return_data = outsourced_op.get_update_outsourced_info(invoice_number)
            # 获取所有的人员，部门组织，供应商，仓库信息
            r_data = outbuy_op.get_all_search_info()
            return_data["code"] = ServiceCode.success
            return_data["page_type"] = 3
            return_data["person_data"] = r_data["person_data"]
            return_data["supplier_data"] = r_data["supplier_data"]
            return_data["department_data"] = r_data["department_data"]
            return_data["warehouse_data"] = r_data["warehouse_data"]
            # 获取委外类型
            return_data["outsourcing_type_list"] = outsourced_op.get_outsourced__type()
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
            return tools.en_render_template("/warehouseManagement/instorage_management/newOutsourcedProcessing.html",
                                            result=return_data)

    @staticmethod
    def post():
        """
        修改--委外入库单信息保存
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
            invoice_info["outsource_type_id"] = request.values.get("outsource_type_id", None, str)
            invoice_info["supplier_id"] = request.values.get("supplier_id", None, int)
            invoice_info["storeman_id"] = request.values.get("storeman_id", None, int)
            invoice_info["stock_direction_id"] = request.values.get("stock_direction_id", None, str)
            invoice_info["warehouse_id"] = request.values.get("warehouse_id", None, int)
            invoice_info["salesman_id"] = request.values.get("salesman_id", None, int)
            invoice_info["processing_unit_id"] = request.values.get("processing_unit_id", None, int)
            invoice_info["remarks"] = request.values.get("remarks", None, str)
            invoice_info["freight_number"] = request.values.get("freight_number", None, str)

            rows = request.values.get("rows", None)
            rows = json.loads(rows)
            invoice_info["rows"] = rows
            op = OutsourcedInWarehouseOp()
            rs = op.update_outsourced_info(invoice_info)
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
        else:
            return_data = json.dumps(
                {'code': ServiceCode.success, 'msg': u"服务器成功", 'rows': r_data})
        finally:
            return tools.en_return_data(return_data)


class InDeleteOutsourcedInvoice(MethodView):
    """
    委外加工入库单据删除
    """
    @staticmethod
    def post():
        r_data = {}
        return_data = {}
        try:
            invoice_number = request.values.get("invoice_number", None, str)
            op = OutsourcedInWarehouseOp()
            rs = op.outsourced_invoice_delete(invoice_number)
            if not rs:
                raise CodeError(300, u"服务器失败")
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


class InCreateOutsourcedMaterialInfo(MethodView):
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
        finally:
            return tools.en_return_data(return_data)


class CommitCreateOutsourcedInvoice(MethodView):
    """
    新建外购入库提交
    """
    @staticmethod
    def post():
        r_data = {}
        return_data = {}
        try:
            print "*********************CommitCreateOutsourcedInvoice**************************"
            # print request.values
            invoice_info = dict()
            invoice_info["invoice_number"] = request.values.get("invoice_number", None, str)
            invoice_info["invoice_date"] = request.values.get("invoice_date", None, str)
            invoice_info["maker_id"] = request.values.get("maker_id", None, str)
            invoice_info["invoice_type_id"] = request.values.get("invoice_type_id", None, str)
            invoice_info["invoice_state_id"] = request.values.get("invoice_state_id", None, str)
            invoice_info["inspector_id"] = request.values.get("inspector_id", None, int)
            invoice_info["outsource_type_id"] = request.values.get("outsource_type_id", None, str)
            invoice_info["supplier_id"] = request.values.get("supplier_id", None, int)
            invoice_info["storeman_id"] = request.values.get("storeman_id", None, int)
            invoice_info["stock_direction_id"] = request.values.get("stock_direction_id", None, str)
            invoice_info["warehouse_id"] = request.values.get("warehouse_id", None, int)
            invoice_info["salesman_id"] = request.values.get("salesman_id", None, int)
            invoice_info["processing_unit_id"] = request.values.get("processing_unit_id", None, int)
            invoice_info["remarks"] = request.values.get("remarks", None, str)
            invoice_info["freight_number"] = request.values.get("freight_number", None, str)
            rows = request.values.get("rows", None)
            rows = json.loads(rows)
            invoice_info["rows"] = rows
            print "****************invoice_info:****************"
            print invoice_info
            op = OutsourcedInWarehouseOp()
            r_check = op.check_outsourced_invoice_number(invoice_info["invoice_number"])
            if r_check:
                rs = op.update_outsourced_info(invoice_info)
            else:
                rs = op.save_outsourced_info(invoice_info)
            if not rs:
                raise CodeError(300, u"服务器失败")
            rs_commit = op.commit_outsourced_info(invoice_info)
            print "rs_commit:", rs_commit
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


class CommitCopyOutsourcedInvoice(MethodView):
    """
    复制外购入库提交
    """
    @staticmethod
    def post():
        r_data = {}
        return_data = {}
        try:
            print "*********************CommitCreateOutsourcedInvoice**************************"
            # print request.values
            invoice_info = dict()
            invoice_info["invoice_number"] = request.values.get("invoice_number", None, str)
            invoice_info["invoice_date"] = request.values.get("invoice_date", None, str)
            invoice_info["maker_id"] = request.values.get("maker_id", None, str)
            invoice_info["invoice_type_id"] = request.values.get("invoice_type_id", None, str)
            invoice_info["invoice_state_id"] = request.values.get("invoice_state_id", None, str)
            invoice_info["inspector_id"] = request.values.get("inspector_id", None, int)
            invoice_info["outsource_type_id"] = request.values.get("outsource_type_id", None, str)
            invoice_info["supplier_id"] = request.values.get("supplier_id", None, int)
            invoice_info["storeman_id"] = request.values.get("storeman_id", None, int)
            invoice_info["stock_direction_id"] = request.values.get("stock_direction_id", None, str)
            invoice_info["warehouse_id"] = request.values.get("warehouse_id", None, int)
            invoice_info["salesman_id"] = request.values.get("salesman_id", None, int)
            invoice_info["processing_unit_id"] = request.values.get("processing_unit_id", None, int)
            invoice_info["remarks"] = request.values.get("remarks", None, str)
            invoice_info["freight_number"] = request.values.get("freight_number", None, str)
            rows = request.values.get("rows", None)
            rows = json.loads(rows)
            invoice_info["rows"] = rows
            print "****************invoice_info:****************"
            print invoice_info
            op = OutsourcedInWarehouseOp()
            r_check = op.check_outsourced_invoice_number(invoice_info["invoice_number"])
            if r_check:
                rs = op.update_outsourced_info(invoice_info)
            else:
                rs = op.save_outsourced_info(invoice_info)
            if not rs:
                raise CodeError(300, u"服务器失败")
            rs_commit = op.commit_outsourced_info(invoice_info)
            print "rs_commit:", rs_commit
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


class CommitUpdateOutsourcedInvoice(MethodView):
    """
    修改外购入库提交
    """
    @staticmethod
    def post():
        r_data = {}
        return_data = {}
        try:
            print "*********************CommitCreateOutsourcedInvoice**************************"
            # print request.values
            invoice_info = dict()
            invoice_info["invoice_number"] = request.values.get("invoice_number", None, str)
            invoice_info["invoice_date"] = request.values.get("invoice_date", None, str)
            invoice_info["maker_id"] = request.values.get("maker_id", None, str)
            invoice_info["invoice_type_id"] = request.values.get("invoice_type_id", None, str)
            invoice_info["invoice_state_id"] = request.values.get("invoice_state_id", None, str)
            invoice_info["inspector_id"] = request.values.get("inspector_id", None, int)
            invoice_info["outsource_type_id"] = request.values.get("outsource_type_id", None, str)
            invoice_info["supplier_id"] = request.values.get("supplier_id", None, int)
            invoice_info["storeman_id"] = request.values.get("storeman_id", None, int)
            invoice_info["stock_direction_id"] = request.values.get("stock_direction_id", None, str)
            invoice_info["warehouse_id"] = request.values.get("warehouse_id", None, int)
            invoice_info["salesman_id"] = request.values.get("salesman_id", None, int)
            invoice_info["processing_unit_id"] = request.values.get("processing_unit_id", None, int)
            invoice_info["remarks"] = request.values.get("remarks", None, str)
            invoice_info["freight_number"] = request.values.get("freight_number", None, str)
            rows = request.values.get("rows", None)
            rows = json.loads(rows)
            invoice_info["rows"] = rows
            print "****************invoice_info:****************"
            print invoice_info
            op = OutsourcedInWarehouseOp()
            r_check = op.check_outsourced_invoice_number(invoice_info["invoice_number"])
            if r_check:
                print "1111111111111111"
                rs = op.update_outsourced_info(invoice_info)
            else:
                print "2222222222222222"
                rs = op.save_outsourced_info(invoice_info)
            if not rs:
                raise CodeError(300, u"服务器失败")
            rs_commit = op.commit_outsourced_info(invoice_info)
            print "rs_commit:", rs_commit
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


class InCreateOutsourcedCheckInvoice(MethodView):
    """
    新建--单据单号唯一性检查
    """
    @staticmethod
    def get():
        r_data = {}
        return_data = {}
        try:
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


class GetOutsourcedOperateInfo(MethodView):
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
            op = OutsourcedInWarehouseOp()
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


add_url.add_url(u'委外加工入库',
                'warehouse_manage.InWarehouseManage',
                add_url.TYPE_ENTRY,
                warehouse_manage_prefix,
                warehouse_manage,
                '/in_outsourced/',
                'InOutSourced',
                InOutSourced.as_view('InOutSourced'),
                90,
                methods=['GET', 'POST'])

add_url.add_url(u'新建委外加工入库单',
                'warehouse_manage.InOutSourced',
                add_url.TYPE_FEATURE,
                warehouse_manage_prefix,
                warehouse_manage,
                '/in_create_outsourced/',
                'InCreateOutSourced',
                InCreateOutSourced.as_view('InCreateOutSourced'),
                methods=['GET', 'POST'])
add_url.add_url(u"复制委外加工入库单",
                'warehouse_manage.InOutSourced',
                add_url.TYPE_FEATURE,
                warehouse_manage_prefix,
                warehouse_manage,
                '/in_copy_outsourced/',
                'InCopyOutsourcedInvoice',
                InCopyOutsourcedInvoice.as_view('InCopyOutsourcedInvoice'),
                methods=['GET', 'POST']
                )

add_url.add_url(u"修改委外加工入库单",
                'warehouse_manage.InOutSourced',
                add_url.TYPE_FEATURE,
                warehouse_manage_prefix,
                warehouse_manage,
                '/in_update_outsourced/',
                'InUpdateOutsourcedInvoice',
                InUpdateOutsourcedInvoice.as_view('InUpdateOutsourcedInvoice'),
                methods=['GET', 'POST']
                )

add_url.add_url(u"删除委外入库单",
                'warehouse_manage.InOutSourced',
                add_url.TYPE_FEATURE,
                warehouse_manage_prefix,
                warehouse_manage,
                '/in_delete_outsourced/',
                'InDeleteOutsourcedInvoice',
                InDeleteOutsourcedInvoice.as_view('InDeleteOutsourcedInvoice'),
                methods=['GET', 'POST']
                )

add_url.add_url(u"新建委外加工入库页面物料信息的获取",
                'warehouse_manage.InCreateOutSourced',
                add_url.TYPE_FEATURE,
                warehouse_manage_prefix,
                warehouse_manage,
                '/in_create_outsourced_material/',
                'InCreateOutsourcedMaterialInfo',
                InCreateOutsourcedMaterialInfo.as_view('InCreateOutsourcedMaterialInfo'),
                methods=['GET']
                )


add_url.add_url(u"新建委外加工入库页面单据单号唯一性检查",
                'warehouse_manage.InCreateOutSourced',
                add_url.TYPE_FEATURE,
                warehouse_manage_prefix,
                warehouse_manage,
                '/in_check_create_outsourced/',
                'InCreateOutsourcedCheckInvoice',
                InCreateOutsourcedCheckInvoice.as_view('InCreateOutsourcedCheckInvoice'),
                methods=['GET']
                )

add_url.add_url(u"新建委外加工入库提交",
                'warehouse_manage.InCreateOutSourced',
                add_url.TYPE_FEATURE,
                warehouse_manage_prefix,
                warehouse_manage,
                '/commit_create_outsourced/',
                'CommitCreateOutsourcedInvoice',
                CommitCreateOutsourcedInvoice.as_view('CommitCreateOutsourcedInvoice'),
                methods=['POST']
                )

add_url.add_url(u"复制委外加工入库提交",
                'warehouse_manage.InCopyOutsourcedInvoice',
                add_url.TYPE_FEATURE,
                warehouse_manage_prefix,
                warehouse_manage,
                '/commit_copy_outsourced/',
                'CommitCopyOutsourcedInvoice',
                CommitCopyOutsourcedInvoice.as_view('CommitCopyOutsourcedInvoice'),
                methods=['POST']
                )

add_url.add_url(u"修改委外加工入库提交",
                'warehouse_manage.InUpdateOutsourcedInvoice',
                add_url.TYPE_FEATURE,
                warehouse_manage_prefix,
                warehouse_manage,
                '/commmit_update_outsourced/',
                'CommitUpdateOutsourcedInvoice',
                CommitUpdateOutsourcedInvoice.as_view('CommitUpdateOutsourcedInvoice'),
                methods=['POST']
                )

add_url.add_url(u"获取委外加工入库操作记录",
                'warehouse_manage.InUpdateOutsourcedInvoice',
                add_url.TYPE_FEATURE,
                warehouse_manage_prefix,
                warehouse_manage,
                '/get_outsourced_record_info/',
                'GetOutsourcedOperateInfo',
                GetOutsourcedOperateInfo.as_view('GetOutsourcedOperateInfo'),
                methods=['POST']
                )

