#!/usr/bin/python
# -*- coding:utf-8 -*-
#    Copyright(c) 2015-2016 JmGo Company
#    All rights reserved.
#
#    文件名 : outbuy_invoices.py
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
from config.share.share_define import WarehouseManagementAttr
from control_center.warehouse_manage.in_warehouse_manage.control.outbuy_in_warehouse_op import OutbuyInWarehouseOp
from data_mode.erp_supply.base_op.warehouse_manage_op.warehouse_op import WarehouseManageBaseOp
from control_center.warehouse_manage.base_view import warehouse_manage, warehouse_manage_prefix


class InOutbuyInvoice(MethodView):
    """
    外购入库
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
            page = request.values.get("page", 1)
            pagecount = request.values.get("pagecount", 10)

            wh_op = WarehouseManageBaseOp()
            outbuy_op = OutbuyInWarehouseOp()
            # 获取所有的单据状态
            state_list = wh_op.get_invoice_state(WarehouseManagementAttr.INVOICE_STATE)
            # 获取所有的单据类型
            type_list = wh_op.get_red_blue_invoice_type()
            m_list, total = outbuy_op.get_outbuy_list_info(page, pagecount)
            return_data["code"] = ServiceCode.success
            return_data["total"] = total
            return_data["rows"] = m_list
            return_data["invoice_color"] = WarehouseManagementAttr.BLUE_ORDER_DIRECTION
            return_data["start_time"] = datetime.datetime.now().strftime("%Y-%m-%d")
            return_data["stop_time"] = datetime.datetime.now().strftime("%Y-%m-%d")
            return_data["invoice_state_list"] = state_list
            return_data["invoice_type_list"] = type_list
            return_data = json.dumps(return_data)
        except CodeError as e:
            return_data = json.dumps(e.json_value())
        except Exception:
            SystemLog.pub_warninglog(traceback.format_exc())
            return_data = json.dumps(
                {'code': ServiceCode.service_exception, 'msg': u"服务器失败", 'rows': r_data})
        finally:
            return tools.en_render_template("/warehouseManagement/instorage_management/outsourcing_storage.html",
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
            search_dict["other_storage_type_id"] = request.values.get("other_storage_type_id", None, str)
            if page <= 0 or pagecount <= 0:
                raise CodeError(300, u"参数错误")
            op = OutbuyInWarehouseOp()
            outbuy_list, total = op.get_outbuy_list_info(page, pagecount, search_dict=search_dict)
            return_data = json.dumps({
                "code": ServiceCode.success,
                "total": total,
                "rows": outbuy_list
            })
            pass
        except CodeError as e:
            return_data = json.dumps(e.json_value())
        except Exception:
            SystemLog.pub_warninglog(traceback.format_exc())
            return_data = json.dumps(
                {'code': ServiceCode.service_exception, 'msg': u"服务器失败", 'rows': r_data})
        finally:
            return tools.en_return_data(return_data)


class InCreateOutbuyInvoice(MethodView):
    """
    新建外购入库单
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
            outbuy_op = OutbuyInWarehouseOp()
            return_data = outbuy_op.get_crate_outbuy_info(invoice_type_id)
            # 获取所有的人员，部门组织，供应商，仓库信息
            r_data = outbuy_op.get_all_search_info()
            return_data["code"] = ServiceCode.success
            return_data["page_type"] = 1
            return_data["person_data"] = r_data["person_data"]
            return_data["supplier_data"] = r_data["supplier_data"]
            return_data["department_data"] = r_data["department_data"]
            return_data["warehouse_data"] = r_data["warehouse_data"]
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
            return tools.en_render_template("/warehouseManagement/instorage_management/add_outsourcing_storage.html",
                                            result=json.dumps(return_data))

    @staticmethod
    def post():
        """
        外购入库单信息保存
        :return:
        """
        r_data = {}
        return_data = {}
        try:
            print "*********************SaveCreateOutbuy**************************"
            # print request.values
            invoice_info = dict()
            invoice_info["invoice_number"] = request.values.get("invoice_number", None, str)
            invoice_info["invoice_date"] = request.values.get("invoice_date", None, str)
            invoice_info["remarks"] = request.values.get("remarks", None, str)
            invoice_info["maker_id"] = request.values.get("maker_id", None, int)
            invoice_info["invoice_type_id"] = request.values.get("invoice_type_id", None, str)
            invoice_info["invoice_state_id"] = request.values.get("invoice_state_id", None, str)
            invoice_info["stock_direction_id"] = request.values.get("stock_direction_id", None, str)
            invoice_info["freight_number"] = request.values.get("freight_number", None, str)
            invoice_info["buyer_id"] = request.values.get("buyer_id", None, int)
            invoice_info["department_id"] = request.values.get("department_id", None, int)
            invoice_info["salesman_id"] = request.values.get("salesman_id", None, int)
            invoice_info["warehouse_id"] = request.values.get("warehouse_id", None, int)
            invoice_info["inspector_id"] = request.values.get("inspector_id", None, int)
            invoice_info["storeman_id"] = request.values.get("storeman_id", None, int)
            invoice_info["supplier_id"] = request.values.get("supplier_id", None, int)
            rows = request.values.get("rows", None)
            rows = json.loads(rows)
            invoice_info["rows"] = rows
            print "****************invoice_info:****************"
            print invoice_info
            op = OutbuyInWarehouseOp()
            rs = op.save_outbuy_info(invoice_info)
            print "rs:", rs

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


class InCopyOutbuyInvoice(MethodView):
    """
    外购入库单据复制
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
            return_data = outbuy_op.get_copy_outbuy_info(invoice_number)
            # 获取所有的人员，部门组织，供应商，仓库信息
            r_data = outbuy_op.get_all_search_info()
            return_data["code"] = ServiceCode.success
            return_data["page_type"] = 2
            return_data["person_data"] = r_data["person_data"]
            return_data["supplier_data"] = r_data["supplier_data"]
            return_data["department_data"] = r_data["department_data"]
            return_data["warehouse_data"] = r_data["warehouse_data"]
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
            return tools.en_render_template("/warehouseManagement/instorage_management/add_outsourcing_storage.html",
                                            result=json.dumps(return_data))

    @staticmethod
    def post():
        """
        复制--外购入库单信息保存
        :return:
        """
        r_data = {}
        return_data = {}
        try:
            print "*********************SaveCreateOutbuyInvoice**************************"
            # print request.values
            invoice_info = dict()
            invoice_info["invoice_number"] = request.values.get("invoice_number", None, str)
            invoice_info["invoice_date"] = request.values.get("invoice_date", None, str)
            invoice_info["remarks"] = request.values.get("remarks", None, str)
            invoice_info["maker_id"] = request.values.get("maker_id", None, int)
            invoice_info["invoice_type_id"] = request.values.get("invoice_type_id", None, str)
            invoice_info["invoice_state_id"] = request.values.get("invoice_state_id", None, str)
            invoice_info["stock_direction_id"] = request.values.get("stock_direction_id", None, str)
            invoice_info["freight_number"] = request.values.get("freight_number", None, str)
            invoice_info["buyer_id"] = request.values.get("buyer_id", None, int)
            invoice_info["department_id"] = request.values.get("department_id", None, int)
            invoice_info["salesman_id"] = request.values.get("salesman_id", None, int)
            invoice_info["warehouse_id"] = request.values.get("warehouse_id", None, int)
            invoice_info["inspector_id"] = request.values.get("inspector_id", None, int)
            invoice_info["storeman_id"] = request.values.get("storeman_id", None, int)
            invoice_info["supplier_id"] = request.values.get("supplier_id", None, int)
            rows = request.values.get("rows", None)
            rows = json.loads(rows)
            invoice_info["rows"] = rows
            print "****************invoice_info:****************"
            print invoice_info
            op = OutbuyInWarehouseOp()
            rs = op.save_outbuy_info(invoice_info)
            if not rs:
                raise CodeError(300, u"保存失败")
            return_data = json.dumps({'code': ServiceCode.success, 'msg': u"服务器成功", 'rows': r_data})
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


class InUpdateOutbuyInvoice(MethodView):
    """
    外购入库单据修改
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
            invoice_number = request.values.get("invoice_number", None, str)
            if invoice_number is None or invoice_number is "" or invoice_number is u"":
                raise CodeError(300, u"参数错误")

            outbuy_op = OutbuyInWarehouseOp()
            return_data = outbuy_op.get_update_outbuy_info(invoice_number)
            # 获取所有的人员，部门组织，供应商，仓库信息
            r_data = outbuy_op.get_all_search_info()
            return_data["code"] = ServiceCode.success
            return_data["page_type"] = 3
            return_data["person_data"] = r_data["person_data"]
            return_data["supplier_data"] = r_data["supplier_data"]
            return_data["department_data"] = r_data["department_data"]
            return_data["warehouse_data"] = r_data["warehouse_data"]
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
            return tools.en_render_template("/warehouseManagement/instorage_management/add_outsourcing_storage.html",
                                            result=json.dumps(return_data))

    @staticmethod
    def post():
        """
        修改--外购入库单信息保存
        :return:
        """
        r_data = {}
        return_data = {}
        try:
            print "*********************CommitCreateOutbuyInvoice**************************"
            # print request.values
            invoice_info = dict()
            invoice_info["invoice_number"] = request.values.get("invoice_number", None, str)
            invoice_info["invoice_date"] = request.values.get("invoice_date", None, str)
            invoice_info["remarks"] = request.values.get("remarks", None, str)
            invoice_info["maker_id"] = request.values.get("maker_id", None, int)
            invoice_info["invoice_type_id"] = request.values.get("invoice_type_id", None, str)
            invoice_info["invoice_state_id"] = request.values.get("invoice_state_id", None, str)
            invoice_info["stock_direction_id"] = request.values.get("stock_direction_id", None, str)
            invoice_info["freight_number"] = request.values.get("freight_number", None, str)
            invoice_info["buyer_id"] = request.values.get("buyer_id", None, int)
            invoice_info["department_id"] = request.values.get("department_id", None, int)
            invoice_info["salesman_id"] = request.values.get("salesman_id", None, int)
            invoice_info["warehouse_id"] = request.values.get("warehouse_id", None, int)
            invoice_info["inspector_id"] = request.values.get("inspector_id", None, int)
            invoice_info["storeman_id"] = request.values.get("storeman_id", None, int)
            invoice_info["supplier_id"] = request.values.get("supplier_id", None, int)
            rows = request.values.get("rows", None)
            rows = json.loads(rows)
            invoice_info["rows"] = rows
            print "****************invoice_info:****************"
            print invoice_info
            op = OutbuyInWarehouseOp()
            rs = op.update_outbuy_info(invoice_info)
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


class CommitCreateOutbuyInvoice(MethodView):
    """
    新建外购入库提交
    """
    @staticmethod
    def post():
        r_data = {}
        return_data = {}
        try:
            print "*********************CommitCreateOutbuyInvoice**************************"
            # print request.values
            invoice_info = dict()
            invoice_info["invoice_number"] = request.values.get("invoice_number", None, str)
            invoice_info["invoice_date"] = request.values.get("invoice_date", None, str)
            invoice_info["remarks"] = request.values.get("remarks", None, str)
            invoice_info["maker_id"] = request.values.get("maker_id", None, int)
            invoice_info["invoice_type_id"] = request.values.get("invoice_type_id", None, str)
            invoice_info["invoice_state_id"] = request.values.get("invoice_state_id", None, str)
            invoice_info["stock_direction_id"] = request.values.get("stock_direction_id", None, str)
            invoice_info["freight_number"] = request.values.get("freight_number", None, str)
            invoice_info["buyer_id"] = request.values.get("buyer_id", None, int)
            invoice_info["department_id"] = request.values.get("department_id", None, int)
            invoice_info["salesman_id"] = request.values.get("salesman_id", None, int)
            invoice_info["warehouse_id"] = request.values.get("warehouse_id", None, int)
            invoice_info["inspector_id"] = request.values.get("inspector_id", None, int)
            invoice_info["storeman_id"] = request.values.get("storeman_id", None, int)
            invoice_info["supplier_id"] = request.values.get("supplier_id", None, int)
            rows = request.values.get("rows", None)
            rows = json.loads(rows)
            invoice_info["rows"] = rows
            print "****************invoice_info:****************"
            print invoice_info
            op = OutbuyInWarehouseOp()
            r_check = op.check_outbuy_invoice_number(invoice_info["invoice_number"])
            if r_check:
                rs = op.update_outbuy_info(invoice_info)
            else:
                rs = op.save_outbuy_info(invoice_info)
            if not rs:
                raise CodeError(300, u"服务器失败")
            rs_commit = op.commit_outbuy_info(invoice_info)
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


class CommitCopyOutbuyInvoice(MethodView):
    """
    复制外购入库提交
    """
    @staticmethod
    def post():
        r_data = {}
        return_data = {}
        try:
            print "*********************CommitCreateOutbuyInvoice**************************"
            # print request.values
            invoice_info = dict()
            invoice_info["invoice_number"] = request.values.get("invoice_number", None, str)
            invoice_info["invoice_date"] = request.values.get("invoice_date", None, str)
            invoice_info["remarks"] = request.values.get("remarks", None, str)
            invoice_info["maker_id"] = request.values.get("maker_id", None, int)
            invoice_info["invoice_type_id"] = request.values.get("invoice_type_id", None, str)
            invoice_info["invoice_state_id"] = request.values.get("invoice_state_id", None, str)
            invoice_info["stock_direction_id"] = request.values.get("stock_direction_id", None, str)
            invoice_info["freight_number"] = request.values.get("freight_number", None, str)
            invoice_info["buyer_id"] = request.values.get("buyer_id", None, int)
            invoice_info["department_id"] = request.values.get("department_id", None, int)
            invoice_info["salesman_id"] = request.values.get("salesman_id", None, int)
            invoice_info["warehouse_id"] = request.values.get("warehouse_id", None, int)
            invoice_info["inspector_id"] = request.values.get("inspector_id", None, int)
            invoice_info["storeman_id"] = request.values.get("storeman_id", None, int)
            invoice_info["supplier_id"] = request.values.get("supplier_id", None, int)
            rows = request.values.get("rows", None)
            rows = json.loads(rows)
            invoice_info["rows"] = rows
            print "****************invoice_info:****************"
            print invoice_info
            op = OutbuyInWarehouseOp()
            r_check = op.check_outbuy_invoice_number(invoice_info["invoice_number"])
            if r_check:
                rs = op.update_outbuy_info(invoice_info)
            else:
                rs = op.save_outbuy_info(invoice_info)
            if not rs:
                raise CodeError(300, u"服务器失败")
            rs_commit = op.commit_outbuy_info(invoice_info)
            print "rs_commit:      ", rs_commit
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


class CommitUpdateOutbuyInvoice(MethodView):
    """
    修改外购入库提交
    """
    @staticmethod
    def post():
        r_data = {}
        return_data = {}
        try:
            print "*********************CommitCreateOutbuyInvoice**************************"
            # print request.values
            invoice_info = dict()
            invoice_info["invoice_number"] = request.values.get("invoice_number", None, str)
            invoice_info["invoice_date"] = request.values.get("invoice_date", None, str)
            invoice_info["remarks"] = request.values.get("remarks", None, str)
            invoice_info["maker_id"] = request.values.get("maker_id", None, int)
            invoice_info["invoice_type_id"] = request.values.get("invoice_type_id", None, str)
            invoice_info["invoice_state_id"] = request.values.get("invoice_state_id", None, str)
            invoice_info["stock_direction_id"] = request.values.get("stock_direction_id", None, str)
            invoice_info["freight_number"] = request.values.get("freight_number", None, str)
            invoice_info["buyer_id"] = request.values.get("buyer_id", None, int)
            invoice_info["department_id"] = request.values.get("department_id", None, int)
            invoice_info["salesman_id"] = request.values.get("salesman_id", None, int)
            invoice_info["warehouse_id"] = request.values.get("warehouse_id", None, int)
            invoice_info["inspector_id"] = request.values.get("inspector_id", None, int)
            invoice_info["storeman_id"] = request.values.get("storeman_id", None, int)
            invoice_info["supplier_id"] = request.values.get("supplier_id", None, int)
            rows = request.values.get("rows", None)
            rows = json.loads(rows)
            invoice_info["rows"] = rows
            print "****************invoice_info:****************"
            print invoice_info
            op = OutbuyInWarehouseOp()
            r_check = op.check_outbuy_invoice_number(invoice_info["invoice_number"])
            if r_check:
                rs = op.update_outbuy_info(invoice_info)
            else:
                rs = op.save_outbuy_info(invoice_info)
            if not rs:
                raise CodeError(300, u"服务器失败")
            rs_commit = op.commit_outbuy_info(invoice_info)
            print "rs_commit:      ", rs_commit
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


class InDeleteOutbuyInvoice(MethodView):
    """
    外购入库单据删除
    """
    @staticmethod
    def post():
        r_data = {}
        return_data = {}
        try:
            invoice_number = request.values.get("invoice_number", None, str)
            op = OutbuyInWarehouseOp()
            rs = op.outbuy_invoice_delete(invoice_number)
            if not rs:
                raise CodeError(300, u"服务器失败")
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


class InCreateOutbuyCheckInvoice(MethodView):
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
            op = OutbuyInWarehouseOp()
            rs = op.check_outbuy_invoice_number(invoice_number)
            if not rs:
                return_data = return_data = json.dumps(
                    {'code': ServiceCode.success, 'msg': u"服务器成功"})
            else:
                return_data = json.dumps(
                    {'code': ServiceCode.service_exception, 'msg': u"服务器失败", 'rows': r_data})
            pass
        except CodeError as e:
            return_data = json.dumps(e.json_value())
        except Exception:
            SystemLog.pub_warninglog(traceback.format_exc())
            return_data = json.dumps(
                {'code': ServiceCode.service_exception, 'msg': u"服务器失败", 'rows': r_data})
        finally:
            return tools.en_return_data(return_data)


class InCreateOutbuyMaterialInfo (MethodView):
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


class GetOperateInfo(MethodView):
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
            op = OutbuyInWarehouseOp()
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

add_url.add_url(u'外购入库',
                'warehouse_manage.InWarehouseManage',
                add_url.TYPE_ENTRY,
                warehouse_manage_prefix,
                warehouse_manage,
                '/in_outbuy_invoice/',
                'InOutbuyInvoice',
                InOutbuyInvoice.as_view('InOutbuyInvoice'),
                100,
                methods=['GET', 'POST'])

add_url.add_url(u'新建外购入库单',
                'warehouse_manage.InOutbuyInvoice',
                add_url.TYPE_FEATURE,
                warehouse_manage_prefix,
                warehouse_manage,
                '/in_create_outbuy/',
                'InCreateOutbuyInvoice',
                InCreateOutbuyInvoice.as_view('InCreateOutbuyInvoice'),
                methods=['GET', 'POST'])

add_url.add_url(u"复制外购入库单",
                'warehouse_manage.InOutbuyInvoice',
                add_url.TYPE_FEATURE,
                warehouse_manage_prefix,
                warehouse_manage,
                '/in_copy_outbuy/',
                'InCopyOutbuyInvoice',
                InCopyOutbuyInvoice.as_view('InCopyOutbuyInvoice'),
                methods=['GET', 'POST']
                )

add_url.add_url(u"修改外购入库单",
                'warehouse_manage.InOutbuyInvoice',
                add_url.TYPE_FEATURE,
                warehouse_manage_prefix,
                warehouse_manage,
                '/in_update_outbuy/',
                'InUpdateOutbuyInvoice',
                InUpdateOutbuyInvoice.as_view('InUpdateOutbuyInvoice'),
                methods=['GET', 'POST']
                )

add_url.add_url(u"删除外购入库单",
                'warehouse_manage.InOutbuyInvoice',
                add_url.TYPE_FEATURE,
                warehouse_manage_prefix,
                warehouse_manage,
                '/in_delete_outbuy/',
                'InDeleteOutbuyInvoice',
                InDeleteOutbuyInvoice.as_view('InDeleteOutbuyInvoice'),
                methods=['POST']
                )


add_url.add_url(u"新建外购入库页面单据单号唯一性检查",
                'warehouse_manage.InOutbuyInvoice',
                add_url.TYPE_FEATURE,
                warehouse_manage_prefix,
                warehouse_manage,
                '/in_check_create_outbuy/',
                'InCreateOutbuyCheckInvoice',
                InCreateOutbuyCheckInvoice.as_view('InCreateOutbuyCheckInvoice'),
                methods=['GET']
                )


add_url.add_url(u"异步获取物料信息",
                'warehouse_manage.InOutbuyInvoice',
                add_url.TYPE_FEATURE,
                warehouse_manage_prefix,
                warehouse_manage,
                '/outbuy_warehousein_material/',
                'InCreateOutbuyMaterialInfo',
                InCreateOutbuyMaterialInfo.as_view('InCreateOutbuyMaterialInfo'),
                methods=['GET']
                )

add_url.add_url(u"新建外购入库提交",
                'warehouse_manage.InOutbuyInvoice',
                add_url.TYPE_FEATURE,
                warehouse_manage_prefix,
                warehouse_manage,
                '/commit_create_outbuy/',
                'CommitCreateOutbuyInvoice',
                CommitCreateOutbuyInvoice.as_view('CommitCreateOutbuyInvoice'),
                methods=['POST']
                )

add_url.add_url(u"复制外购入库提交",
                'warehouse_manage.InOutbuyInvoice',
                add_url.TYPE_FEATURE,
                warehouse_manage_prefix,
                warehouse_manage,
                '/commit_copy_outbuy/',
                'CommitCopyOutbuyInvoice',
                CommitCopyOutbuyInvoice.as_view('CommitCopyOutbuyInvoice'),
                methods=['POST']
                )

add_url.add_url(u"修改外购入库提交",
                'warehouse_manage.InOutbuyInvoice',
                add_url.TYPE_FEATURE,
                warehouse_manage_prefix,
                warehouse_manage,
                '/commmit_update_outbuy/',
                'CommitUpdateOutbuyInvoice',
                CommitUpdateOutbuyInvoice.as_view('CommitUpdateOutbuyInvoice'),
                methods=['POST']
                )

add_url.add_url(u"获取操作记录",
                'warehouse_manage.InUpdateOutbuyInvoice',
                add_url.TYPE_FEATURE,
                warehouse_manage_prefix,
                warehouse_manage,
                '/get_record_info/',
                'GetOperateInfo',
                GetOperateInfo.as_view('GetOperateInfo'),
                methods=['POST']
                )
