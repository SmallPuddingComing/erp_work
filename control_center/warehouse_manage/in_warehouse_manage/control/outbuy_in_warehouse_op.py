#!/usr/bin/python
# -*- coding:utf-8 -*-

import traceback
import datetime
from sqlalchemy import and_, func, or_
from flask import session
from public.exception.custom_exception import CodeError
from data_mode.erp_supply.control_base.controlBase import ControlEngine
from data_mode.user_center.control.mixOp import MixUserCenterOp
from data_mode.erp_supply.mode.material_repertory_model.warehousein_purchase_detail import WarehouseInPurchaseDetail
from data_mode.erp_supply.mode.material_repertory_model.warehousein_purchase_invoice import WarehouseInPurchaseInvoice
# 加上会报错 why？
# from data_mode.erp_supply.base_op.material_op.baseinfo_op import Baseinfo_Op
from control_center.supply_chain.supplier_manage.control.supplier_baseinfo_op import SupplierBaseInfoOp
from control_center.supply_chain.material_warehosue.control.material_warehose_info_op import MaterialWarehouseInfoOp
from data_mode.erp_supply.base_op.warehouse_manage_op.warehouse_op import WarehouseManageBaseOp
from config.share.share_define import WarehouseManagementAttr
from control_center.supply_chain.material_warehosue.control.material_warehouse_mix_op import GetWarehouseInfo


class OutbuyInWarehouseOp(ControlEngine):
    """
    外购入库op
    """
    def __init__(self):
        """
        控制引擎初始化
        :return:
        """
        ControlEngine.__init__(self)

    def get_outbuy_list_info(self, page, per_page, search_dict=None):
        """

        :param page:                第几页
        :param per_page:            每页显示记录数
        :param search_dict:{
            invoice_number:            #单据单号 没有不传
            start_time:                # 开始时间 没有不传
            stop_time:                  # 结束时间 没有不传
            invoice_type:               #单据类型 没有不传
            invoice_state:              #单据状态 没有不传
            supplier_id:                #供应商id 没有不传
        }
        :return:
        """
        try:
            start = per_page*(page-1)
            condition = and_()
            if search_dict is not None:
                invoice_number = search_dict.get("invoice_number")
                if invoice_number is not None and invoice_number is not "" and invoice_number is not u"":
                    condition.append(WarehouseInPurchaseInvoice.invoice_number == invoice_number)

                start_time = search_dict.get("start_time")
                if start_time is not None and start_time is not "" and start_time is not u"":
                    condition.append(WarehouseInPurchaseInvoice.invoice_date >= start_time)

                stop_time = search_dict.get("stop_time")
                if stop_time is not None and stop_time is not "" and stop_time is not u"":
                    condition.append(WarehouseInPurchaseInvoice.invoice_date <= stop_time)

                invoice_type_id = search_dict.get("invoice_type_id")
                # 这里的单据类型搜索实际上是库存方向的搜索
                if invoice_type_id is not None and invoice_type_id is not "" and invoice_type_id is not u"":
                    condition.append(WarehouseInPurchaseInvoice.inventory_direction_id == invoice_type_id)

                invoice_state_id = search_dict.get("invoice_state")
                if invoice_state_id is not None and invoice_state_id is not "" and invoice_state_id is not u"":
                    condition.append(WarehouseInPurchaseInvoice.invoice_state_id == invoice_state_id)

                # 供应商可能存在同名情况
                supplier = search_dict.get("supplier")
                if supplier is not None:
                    from data_mode.erp_supply.mode.supply_manage_mode.supplier_info import SupplierBaseInfo
                    condition_supplier = or_()
                    rs_supplier = self.controlsession.query(SupplierBaseInfo).filter_by(supplier_name=supplier).all()
                    for item in rs_supplier:
                        item_supplier = item.to_json()
                        condition_supplier.append(WarehouseInPurchaseInvoice.supplier_id == item_supplier["id"])
                    condition.append(condition_supplier)
                    pass

            rs = self.controlsession.query(WarehouseInPurchaseInvoice).\
                filter(condition).limit(per_page).offset(start).all()
            total = self.controlsession.query(func.count(WarehouseInPurchaseInvoice.id)).filter(condition).scalar()
            invoice_info_list = []
            user_op = MixUserCenterOp()
            supplier_op = SupplierBaseInfoOp()
            for item in rs:
                invoice_dict = {}
                item_data = item.to_json()
                invoice_dict["invoice_number"] = item_data["invoice_number"]
                # 单据类型 实际上是库存方向
                invoice_dict["invoice_type_id"] = item_data["stock_direction_id"]
                if item_data["stock_direction_id"] == "17-1":
                    invoice_dict["invoice_type"] = u"蓝色单据"
                elif item_data["stock_direction_id"] == "17-2":
                    invoice_dict["invoice_type"] = u"红色单据"
                else:
                    CodeError(300, u"单据类型错误")
                # 单据状态
                invoice_dict["invoice_state_id"] = item_data["invoice_state_id"]
                invoice_dict["invoice_state"] = WarehouseManagementAttr.INVOICE_STATE.\
                    get(item_data["invoice_state_id"])
                invoice_dict["invoice_date"] = item_data["invoice_date"]
                invoice_dict["supplier_id"] = item_data["supplier_id"]
                # 根据供应商id获取供应商信息
                if item_data["supplier_id"] is not None and item_data["supplier_id"] is not "":
                    rs_supplier = supplier_op.get_supplier_base_info(item_data["supplier_id"])
                    invoice_dict["supplier"] = rs_supplier["supplier_name"]
                else:
                    raise CodeError(300, u"获取供应商信息失败")
                # 根据部门id获取部门信息
                invoice_dict["department_organization"] = user_op.get_department_name_byID(item_data["supplier_id"])

                if item_data["storeman_id"] is not None and item_data["storeman_id"] is not "":
                    rs_storeman = user_op.get_user_info(item_data["storeman_id"])
                    invoice_dict["storeman"] = rs_storeman["name"]
                else:
                    raise CodeError(300, u"获取验收员信息失败")
                if item_data["inspector_id"] is not None and item_data["inspector_id"] is not "":
                    rs_inspector = user_op.get_user_info(item_data["inspector_id"])
                    invoice_dict["inspector"] = rs_inspector["name"]
                else:
                    raise CodeError(300, u"获取保管员信息失败")
                if item_data["salesman_id"] is None or item_data["salesman_id"] is "":
                    invoice_dict["salesman"] = ""
                else:
                    rs_salesman = user_op.get_user_info(item_data["salesman_id"])
                    invoice_dict["salesman"] = rs_salesman["name"]
                    invoice_info_list.append(invoice_dict)

        except CodeError:
            raise
        except Exception:
            raise
        return invoice_info_list, total

    def get_crate_outbuy_info(self, invoice_type_id):
        """
        获取新建外购入库所需数据
        :param invoice_type_id:   # 单据类型： 红蓝单据
        :return:
        """
        try:
            from redis_cache.public_cache.serial_number import create_number
            invoice_dict = dict()
            # 获取单号
            invoice_dict["invoice_number"] = create_number("PBIN{DATE}{SERIAL_NUMBER_4}",
                                                           db_session=self.controlsession,
                                                           table_name=WarehouseInPurchaseInvoice.__tablename__,
                                                           field="invoice_number")

            # 获取日期
            invoice_dict["invoice_date"] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            # 制单人
            invoice_dict["maker"] = session["user"]["name"]
            invoice_dict["maker_id"] = session["user"]["id"]
            # 单据类型
            invoice_dict["invoice_type_id"] = WarehouseManagementAttr.PURCHASE_IN_WAREHOUSE
            invoice_dict["invoice_type"] = WarehouseManagementAttr.INVOICE_TYPE[invoice_dict["invoice_type_id"]]

            # 单据状态
            invoice_dict["invoice_state_id"] = WarehouseManagementAttr.TEMPORARY_STORAGE
            invoice_dict["invoice_state"] = WarehouseManagementAttr.INVOICE_STATE[invoice_dict["invoice_state_id"]]
            # 库存方向

            invoice_dict["stock_direction"] = WarehouseManagementAttr.REPERTORY_DIRECTION_TYPE[invoice_type_id]
            invoice_dict["stock_direction_id"] = invoice_type_id

            # 是否是红色单据
            if invoice_type_id == WarehouseManagementAttr.BLUE_ORDER_DIRECTION:
                invoice_dict["is_red_invoice"] = 0
            elif invoice_type_id == WarehouseManagementAttr.RED_ORDER_DIRECTION:
                invoice_dict["is_red_invoice"] = 1

        except CodeError:
            raise
        except Exception:
            raise
        return invoice_dict

    def get_copy_outbuy_info(self, invoice_number):
        """
        获取复制外购入库所需数据
        :param invoice_number:
        :return:
        """
        try:
            from redis_cache.public_cache.serial_number import create_number
            invoice_dict = dict()
            # 获取单号
            invoice_dict["invoice_number"] = create_number("PBIN{DATE}{SERIAL_NUMBER_4}",
                                                           db_session=self.controlsession,
                                                           table_name=WarehouseInPurchaseInvoice.__tablename__,
                                                           field="invoice_number")

            # 获取日期
            invoice_dict["invoice_date"] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            # 制单人
            invoice_dict["maker"] = session["user"]["name"]
            invoice_dict["maker_id"] = session["user"]["id"]
            # 单据类型
            invoice_dict["invoice_type_id"] = WarehouseManagementAttr.PURCHASE_IN_WAREHOUSE
            invoice_dict["invoice_type"] = WarehouseManagementAttr.INVOICE_TYPE[invoice_dict["invoice_type_id"]]

            # 单据状态
            invoice_dict["invoice_state_id"] = WarehouseManagementAttr.TEMPORARY_STORAGE
            invoice_dict["invoice_state"] = WarehouseManagementAttr.INVOICE_STATE[invoice_dict["invoice_state_id"]]

            user_op = MixUserCenterOp()
            supplier_op = SupplierBaseInfoOp()
            from data_mode.erp_supply.base_op.material_op.baseinfo_op import Baseinfo_Op
            m_op = Baseinfo_Op()
            wh_op = MaterialWarehouseInfoOp()
            if invoice_number is not None:
                rs_invoice = self.controlsession.query(WarehouseInPurchaseInvoice).filter(
                    WarehouseInPurchaseInvoice.invoice_number == invoice_number
                ).first()
                if rs_invoice:
                    invoice_data = rs_invoice.to_json()
                    # 库存方向：
                    invoice_dict["stock_direction"] = WarehouseManagementAttr.REPERTORY_DIRECTION_TYPE[
                        invoice_data["stock_direction_id"]
                    ]
                    invoice_dict["stock_direction_id"] = invoice_data["stock_direction_id"]

                    # 是否是红蓝单据
                    if invoice_dict["stock_direction_id"] == WarehouseManagementAttr.BLUE_ORDER_DIRECTION:
                        invoice_dict["is_red_invoice"] = 0
                    elif invoice_dict["stock_direction_id"] == WarehouseManagementAttr.RED_ORDER_DIRECTION:
                        invoice_dict["is_red_invoice"] = 1

                    # 验收员
                    rs_user = user_op.get_user_info(invoice_data["inspector_id"])
                    invoice_dict["inspector"] = rs_user["name"]
                    invoice_dict["inspector_id"] = invoice_data["inspector_id"]
                    # 保管员
                    rs_user = user_op.get_user_info(invoice_data["storeman_id"])
                    invoice_dict["storeman"] = rs_user["name"]
                    invoice_dict["storeman_id"] = invoice_data["storeman_id"]
                    # 业务员
                    if invoice_data["salesman_id"] is not None:
                        rs_user = user_op.get_user_info(invoice_data["salesman_id"])
                        invoice_dict["salesman"] = rs_user["name"]
                        invoice_dict["salesman_id"] = invoice_data["storeman_id"]
                    else:
                        invoice_dict["salesman"] = ""
                        invoice_dict["storeman_id"] = ""
                    # 采购员
                    if invoice_data["buyer_id"] is not None:
                        rs_user = user_op.get_user_info(invoice_data["buyer_id"])
                        invoice_dict["buyer"] = rs_user["name"]
                        invoice_dict["buyer_id"] = invoice_data["buyer_id"]
                    else:
                        invoice_dict["buyer"] = ""
                        invoice_dict["buyer_id"] = ""
                    # 收料仓库
                    if invoice_data["warehouse_id"] is not None:
                        rs_wh = wh_op.get_warehouse_name_by_id(invoice_data["warehouse_id"])
                        invoice_dict["warehouse"] = rs_wh["warehouse_name"]
                        invoice_dict["warehouse_id"] = invoice_data["warehouse_id"]
                    else:
                        invoice_dict["warehouse"] = ""
                        invoice_dict["warehouse_id"] = ""
                    # 部门组织
                    if invoice_data["department_id"] is not None:
                        invoice_dict["department_organization"] = user_op.get_department_name_byID(
                                                                        invoice_data["department_id"])
                        invoice_dict["department_id"] = invoice_data["department_id"]
                    else:
                        invoice_dict["department_organization"] = ""
                        invoice_dict["department_id"] = ""
                    # 根据供应商id获取供应商信息
                    rs_supplier = supplier_op.get_supplier_base_info(invoice_data["supplier_id"])
                    invoice_dict["supplier"] = rs_supplier["supplier_name"]
                    invoice_dict["supplier_id"] = invoice_data["supplier_id"]
                    # 运货单号
                    invoice_dict["freight_number"] = invoice_data["freight_number"]
                    # 备注
                    invoice_dict["remarks"] = invoice_data["remarks"]
                    rs_detail = self.controlsession.query(WarehouseInPurchaseDetail).filter(
                        WarehouseInPurchaseDetail.invoice_id == rs_invoice.id).all()
                    detail_list = []
                    for item in rs_detail:
                        item_dict = item.to_json()
                        m_rs = m_op.get_baseinfo_by_id(item_dict["material_id"])
                        if m_rs[0] == 0:
                            item_dict["material_code"] = m_rs[1]["code"]
                            item_dict["material_name"] = m_rs[1]["name"]
                            item_dict["specification_model"] = m_rs[1]["specifications"]
                            item_dict["unit"] = m_rs[1]["measureunit"]
                            # 根据 item_dict["warehouse_id"] 获取仓库信息
                            wh_rs = wh_op.get_warehouse_name_by_id(item_dict["warehouse_id"])
                            item_dict["warehouse"] = wh_rs["warehouse_name"]
                            detail_list.append(item_dict)
                        else:
                            raise CodeError(300, u"查询物料信息失败")
                    invoice_dict["rows"] = detail_list
                else:
                    raise CodeError(300, u"复制单据信息失败")
        except CodeError:
            raise
        except Exception:
            raise
        return invoice_dict

    def get_update_outbuy_info(self, invoice_number):
        """
        获取修改页面所需数据
        :param invoice_number:
        :return:
        """
        try:
            invoice_data = ""
            user_op = MixUserCenterOp()
            supplier_op = SupplierBaseInfoOp()
            from data_mode.erp_supply.base_op.material_op.baseinfo_op import Baseinfo_Op
            m_op = Baseinfo_Op()
            wh_op = MaterialWarehouseInfoOp()
            if invoice_number is not None:
                rs_invoice = self.controlsession.query(WarehouseInPurchaseInvoice).filter(
                    WarehouseInPurchaseInvoice.invoice_number == invoice_number
                ).first()
                if rs_invoice:
                    invoice_data = rs_invoice.to_json()
                    # 制单人
                    user_rs = user_op.get_user_info(invoice_data["maker_id"])
                    invoice_data["maker"] = user_rs["name"]
                    # 单据状态
                    invoice_data["invoice_state"] = WarehouseManagementAttr.INVOICE_STATE[
                                                                invoice_data["invoice_state_id"]]
                    #
                    if invoice_data["invoice_state_id"] == WarehouseManagementAttr.TEMPORARY_STORAGE:
                        invoice_data["state_type"] = 1
                    elif invoice_data["invoice_state_id"] == WarehouseManagementAttr.COMPLETED:
                        invoice_data["state_type"] = 0

                    # 单据类型
                    invoice_data["invoice_type"] = WarehouseManagementAttr.INVOICE_TYPE[
                                                                invoice_data["invoice_type_id"]]
                    # 库存方向：
                    invoice_data["stock_direction"] = WarehouseManagementAttr.REPERTORY_DIRECTION_TYPE[
                                                            invoice_data["stock_direction_id"]]
                    # 是否是红蓝单据
                    if invoice_data["stock_direction_id"] == WarehouseManagementAttr.BLUE_ORDER_DIRECTION:
                        invoice_data["is_red_invoice"] = 0
                    elif invoice_data["stock_direction_id"] == WarehouseManagementAttr.RED_ORDER_DIRECTION:
                        invoice_data["is_red_invoice"] = 1

                    # 验收员
                    rs_user = user_op.get_user_info(invoice_data["inspector_id"])
                    invoice_data["inspector"] = rs_user["name"]
                    # 保管员
                    rs_user = user_op.get_user_info(invoice_data["storeman_id"])
                    invoice_data["storeman"] = rs_user["name"]
                    # 业务员
                    if invoice_data["salesman_id"] is not None:
                        rs_user = user_op.get_user_info(invoice_data["salesman_id"])
                        invoice_data["salesman"] = rs_user["name"]
                    else:
                        invoice_data["salesman"] = ""
                        invoice_data["storeman_id"] = ""
                    # 采购员
                    if invoice_data["buyer_id"] is not None:
                        rs_user = user_op.get_user_info(invoice_data["buyer_id"])
                        invoice_data["buyer"] = rs_user["name"]
                    else:
                        invoice_data["buyer"] = ""
                        invoice_data["buyer_id"] = ""
                    # 收料仓库
                    if invoice_data["warehouse_id"] is not None:
                        rs_wh = wh_op.get_warehouse_name_by_id(invoice_data["warehouse_id"])
                        invoice_data["warehouse"] = rs_wh["warehouse_name"]
                    else:
                        invoice_data["warehouse"] = ""
                        invoice_data["warehouse_id"] = ""
                    # 部门组织
                    if invoice_data["department_id"] is not None:
                        invoice_data["department_organization"] = user_op.get_department_name_byID(
                                                                        invoice_data["department_id"])
                    else:
                        invoice_data["department_organization"] = ""
                        invoice_data["department_id"] = ""
                    # 根据供应商id获取供应商信息
                    rs_supplier = supplier_op.get_supplier_base_info(invoice_data["supplier_id"])
                    invoice_data["supplier"] = rs_supplier["supplier_name"]
                    rs_detail = self.controlsession.query(WarehouseInPurchaseDetail).filter(
                        WarehouseInPurchaseDetail.invoice_id == rs_invoice.id).all()
                    detail_list = []
                    for item in rs_detail:
                        item_dict = item.to_json()
                        m_rs = m_op.get_baseinfo_by_id(item_dict["material_id"])
                        if m_rs[0] == 0:
                            item_dict["material_code"] = m_rs[1]["code"]
                            item_dict["material_name"] = m_rs[1]["name"]
                            item_dict["specification_model"] = m_rs[1]["specifications"]
                            item_dict["unit"] = m_rs[1]["measureunit"]
                            # 根据 item_dict["warehouse_id"] 获取仓库信息
                            wh_rs = wh_op.get_warehouse_name_by_id(item_dict["warehouse_id"])
                            item_dict["warehouse"] = wh_rs["warehouse_name"]
                            detail_list.append(item_dict)
                        else:
                            raise CodeError(300, u"查询物料信息失败")
                    invoice_data["rows"] = detail_list

                    # 获取操作记录
                    update_records = dict()
                    update_records["total"], update_records["rows"] = self.get_invoice_operate_record(invoice_number)
                    invoice_data["update_records"] = update_records
                else:
                    raise CodeError(300, u"修改单据信息获取失败")
            pass
        except CodeError:
            raise
        except Exception:
            raise
        return invoice_data

    def commit_outbuy_info(self, invoice_data_dict):
        """
        外购入库提交更新库存
        :param invoice_data_dict:
        :return:
        """
        try:
            from data_mode.erp_supply.base_op.warehouse_manage_op.inventory_op import \
                pub_batch_in_warehouse, pub_batch_out_warehouse
            # 根据库存方向进行入库或出库操作
            try:
                if invoice_data_dict['stock_direction_id'] == WarehouseManagementAttr.RED_ORDER_DIRECTION:
                    # 出库
                    pub_batch_out_warehouse(invoice_data_dict['invoice_number'], invoice_data_dict['rows'])

                elif invoice_data_dict['stock_direction_id'] == WarehouseManagementAttr.BLUE_ORDER_DIRECTION:
                    # 入库
                    pub_batch_in_warehouse(invoice_data_dict['invoice_number'], invoice_data_dict['rows'])
                else:
                    raise ValueError("invoice_data['stock_direction_id'] must be a value in %s" %
                                     WarehouseManagementAttr.REPERTORY_DIRECTION_TYPE.keys())
            except Exception:
                raise CodeError(300, u"提交失败")

            rs = self.controlsession.query(WarehouseInPurchaseInvoice).\
                filter_by(invoice_number=invoice_data_dict['invoice_number']).first()
            if rs:
                rs.invoice_state_id = WarehouseManagementAttr.COMPLETED
                self.controlsession.add(rs)
            else:
                raise CodeError(300, u"提交失败")
            self.controlsession.commit()
            pass
        except CodeError:
            raise
        except Exception:
            raise
        return True

    def get_invoice_operate_record(self, invoice_number, page=1, per_page=5):
        """
        获取外购入库的操作记录
        :param invoice_number:
        :param page:
        :param per_page:
        :return:
        """
        if invoice_number is None:
            raise ValueError("invoice_number can not be None")
        if not isinstance(invoice_number, str):
            raise TypeError("unsupported operand type(s) for function's parameter")

        from data_mode.erp_supply.base_op.operate_op import Operate_Op
        rs = self.controlsession.query(WarehouseInPurchaseInvoice).filter_by(invoice_number=invoice_number).first()
        if rs:
            invoice_id = rs.id
        else:
            CodeError(300, u"没有该单据")
        oper_op = Operate_Op()
        start = (page - 1) * per_page
        record_datas, total = oper_op.get_record(start, per_page, WarehouseInPurchaseInvoice.__tablename__, invoice_id)
        record_list = []
        if record_datas is None or not record_datas:
            return total, record_list
        else:
            for data in record_datas:
                temp_dict = dict()
                temp_dict['operate_name'] = data.get('operator_name')
                temp_dict['operate_time'] = data.get('operate_time')
                temp_dict['operate_content'] = data.get('detail')
                record_list.append(temp_dict)
        return total, record_list

    @staticmethod
    def get_all_search_info():
        """
        获取人员信息，仓库，供应商，部门组织的信息
        :return:
        """
        try:
            # 获取人员信息
            person_data = dict()
            from data_mode.user_center.control.mixOp import MixUserCenterOp
            user_op = MixUserCenterOp()
            person_data["rows"], person_data["total"] = user_op.get_all_person_info()
            print person_data
            # 获取供应商信息
            supplier_data = dict()
            from control_center.warehouse_manage.warehouse_out_manage.view.outsourcing_warehouse_out_view import \
                supplier
            supplier_data = supplier()
            print supplier_data
            # 获取部门组织信息
            department_data = dict()
            from data_mode.user_center.control.mixOp import MixUserCenterOp
            user_op = MixUserCenterOp()
            dp_list = user_op.get_departments_info()
            rows = []
            for item in dp_list:
                item_dict = dict()
                print "00000000001", item["departMents"]
                for dp_item in item["departMents"]:
                    print dp_item
                    # item_dict["id"] = item["id"]
                    # item_dict["pid"] = item["pid"]
                    # item_dict["name"] = item["name"]
                    rows.append(dp_item)
            department_data["rows"] = rows
            department_data["total"] = len(rows)

            # 获取仓库信息
            warehouse_data = dict()

            wh_op = GetWarehouseInfo()
            total, warehouse_data = wh_op.get_warehouse_all()
            new_data = []
            for element in warehouse_data:
                new_data.append({
                    'warehouse_id': element['warehouse_id'],
                    'warehouse_code': element['warehouse_code'],
                    'warehouse_name': element['warehouse_name'],
                    'warehouse_type': wh_op.get_warehouse_type_by_id(element['warehouse_type_id']),
                    'contacts': element['contacts'],
                    'prov': element['prov'],
                    'city': element['city'],
                    'region': element['region'],
                    'address': element['address']
                    })
            warehouse_info = {
                'total': total,
                'rows': new_data
            }
            r_data = {
                "person_data": person_data,
                "supplier_data": supplier_data,
                "department_data": department_data,
                "warehouse_data": warehouse_info
            }
            pass
        except CodeError:
            raise
        except Exception:
            raise
        return r_data

    def save_outbuy_info(self, invoice_info):
        """
        保存外购入库 新建和复制 单据信息
        :param invoice_info:
        invoice_number: str		# 单据编号
        invoice_date: str			# 单据日期
        remarks: str				# 备注
        maker_id: int			# 制单人ID
        invoice_type_id: str		# 单据类型ID
        invoice_state_id: str	# 单据状态ID
        storeman_id: int			# 保管员ID
        supplier_id: int			# 供应商ID
        inspector_id: int				# 验收员ID
        stock_direction_id: str		# 库存方向ID
        warehouse_id: int			# 收料仓库仓库ID
        salesman_id: int			# 业务员ID
        department_id: int			# 部门组织ID
        freight_number：			# 运货单号
        buyer_id:					# 采购员ID
        rows:[		#明细信息
        {
            material_id: int		# 产品ID（即物料ID）
            deliverWarehouse_id: int	# 发货仓库ID
            realHair_number: int		# 实收数量
            is_nondefective: int 	# 检验是否为良品(1:是、0:否)
        }
        ]
        }
        保存外购入库信息
        :return:
        """
        try:
            print "1111111111111111111111", invoice_info["stock_direction_id"],
            # 保存单据基本信息
            self.save_invoice_info(invoice_info, is_commit=True)
            # 查询单据id，然后保存详细信息
            print "2222222222222"
            rs_invoice = self.get_outbuy_info_by_number(invoice_info["invoice_number"])
            print "4444444444", type(rs_invoice), rs_invoice
            self.save_detail_info(rs_invoice["id"], invoice_info["rows"], is_commit=False)
            print "33333333333333"
            # 添加操作记录
            from data_mode.erp_supply.base_op.material_op.baseinfo_op import Baseinfo_Op
            material_base_op = Baseinfo_Op()
            material_base_op.add_operate_record(uid=session['user']['id'],
                                                detail=u"新增外购入库单据",
                                                id_list=rs_invoice["id"],
                                                is_commit=False,
                                                db_session=self.controlsession,
                                                tablename=WarehouseInPurchaseInvoice.__tablename__
                                                )

            self.controlsession.commit()
        except CodeError:
            rs = self.controlsession.query(WarehouseInPurchaseInvoice).filter(
                WarehouseInPurchaseInvoice.invoice_number == invoice_info["invoice_number"]
            ).first()
            if rs:
                self.controlsession.delete(rs)
                self.controlsession.commit()
            raise
        except Exception:
            rs = self.controlsession.query(WarehouseInPurchaseInvoice).filter(
                WarehouseInPurchaseInvoice.invoice_number == invoice_info["invoice_number"]
            ).first()
            if rs:
                self.controlsession.delete(rs)
                self.controlsession.commit()
            raise
        return True

    def update_outbuy_info(self, invoice_info):
        """
        修改外购入库单据信息保存
        :param invoice_info:
        is_commit: int				# 是否提交(1: 提交， 0：保存)
        invoice_number: str		    # 单据编号
        invoice_date: str			# 单据日期
        remarks: str				# 备注
        maker_id: int			    # 制单人ID
        invoice_type_id: str		# 单据类型ID
        invoice_state_id: str	    # 单据状态ID
        storeman_id: int			# 保管员ID
        supplier_id: int			# 供应商ID
        inspector_id: int			# 验收员ID
        stock_direction_id: str		# 库存方向ID
        warehouse_id: int			# 收料仓库仓库ID
        salesman_id: int			# 业务员ID
        department_id: int			# 部门组织ID
        freight_number：			    # 运货单号
        buyer_id:					# 采购员ID
        rows:[		#明细信息
        {
            material_id: int		# 产品ID（即物料ID）
            warehouse_id: int	# 发货仓库ID
            realHair_number: int		# 实收数量
            is_nondefective: int 	# 检验是否为良品(1:是、0:否)
        }
        ]
        }
        :param invoice_info:
        :return:
        """
        try:
            if invoice_info["invoice_number"] is None:
                raise CodeError(300, u"单号非法")
            rs_invoice = self.controlsession.query(WarehouseInPurchaseInvoice).filter_by(
                    invoice_number=invoice_info["invoice_number"]).first()
            print "22222222222222", rs_invoice.invoice_state_id
            if not rs_invoice:
                raise CodeError(300, u"保存失败")
            elif rs_invoice.invoice_state_id != WarehouseManagementAttr.TEMPORARY_STORAGE:
                print "1111111111111111111111111", rs_invoice.invoice_state_id
                raise CodeError(300, u"只允许修改暂存状态下的单据")
            else:
                # 先把原来的绑定的物料信息删除掉
                rs_detail = self.controlsession.query(WarehouseInPurchaseDetail).\
                    filter_by(invoice_id=rs_invoice.id).all()
                for detail_item in rs_detail:
                    self.controlsession.delete(detail_item)
                # 更新新的单据信息 单号，制单人 类型，状态，日期，库存方向 不能修改
                rs_invoice.inspector_id = invoice_info["inspector_id"]
                rs_invoice.keeper_id = invoice_info["storeman_id"]
                rs_invoice.salesman_id = invoice_info["salesman_id"]
                rs_invoice.supplier_id = invoice_info["supplier_id"]
                rs_invoice.purchaser_id = invoice_info["buyer_id"]
                rs_invoice.storage_warehouse_id = invoice_info["warehouse_id"]
                # rs_invoice.inventory_direction_id = invoice_info["stock_direction_id"]
                rs_invoice.transport_goods_number = invoice_info["freight_number"]
                rs_invoice.department_id = invoice_info["department_id"]
                rs_invoice.remark = invoice_info["remarks"]
                self.controlsession.add(rs_invoice)

                for item in invoice_info["rows"]:
                    item_obj = WarehouseInPurchaseDetail(invoice_id=rs_invoice.id,
                                                         material_id=item["material_id"],
                                                         material_num=item["inventory_number"],
                                                         warehouse_id=item["warehouse_id"],
                                                         is_good_material=item["is_nondefective"])
                    self.controlsession.add(item_obj)
                # 添加操作记录
                from data_mode.erp_supply.base_op.material_op.baseinfo_op import Baseinfo_Op
                material_base_op = Baseinfo_Op()
                material_base_op.add_operate_record(uid=session['user']['id'],
                                                    detail=u"修改外购入库单据",
                                                    id_list=rs_invoice.id,
                                                    is_commit=False,
                                                    db_session=self.controlsession,
                                                    tablename=WarehouseInPurchaseInvoice.__tablename__
                                                    )
            self.controlsession.commit()
            pass
        except CodeError:
            raise
        except Exception:
            raise
        return True

    def outbuy_invoice_delete(self, invoice_number):
        """
        删除外购入库单据
        :param invoice_number: 单据单号
        :return:
        """
        try:
            if invoice_number is None:
                raise CodeError(300, u"单据未选中")

            rs = self.controlsession.query(WarehouseInPurchaseInvoice).filter_by(invoice_number=invoice_number).first()

            if rs:
                m_rs = self.controlsession.query(WarehouseInPurchaseDetail).filter_by(invoice_id=rs.id).all()
                invoice_info = rs.to_json()
                if invoice_info["invoice_state_id"] != WarehouseManagementAttr.TEMPORARY_STORAGE:
                    raise CodeError(300, u"该单据不能被删除")
                else:
                    for item in m_rs:
                        self.controlsession.delete(item)
                    self.controlsession.delete(rs)
            else:
                raise CodeError(300, u"删除失败")
            self.controlsession.commit()
        except CodeError:
            self.controlsession.rollback()
            raise
        except Exception:
            self.controlsession.rollback()
            raise
        return True

    def check_outbuy_invoice_number(self, invoice_number):
        """
        单据单号唯一性检查
        :param invoice_number:
        :return:
        """
        from redis_cache.public_cache.serial_number import check_number_exists
        return check_number_exists(self.controlsession,
                                   WarehouseInPurchaseInvoice.__tablename__,
                                   'invoice_number',
                                   invoice_number)

    def save_invoice_info(self, invoice_info, is_commit=False):
        """
        保存外购入库单单据信息
        :param invoice_info:
        :return:
        """
        try:
            r_obj = WarehouseInPurchaseInvoice(invoice_number=invoice_info["invoice_number"],
                                               invoice_date=invoice_info["invoice_date"],
                                               invoice_type_id=invoice_info["invoice_type_id"],
                                               invoice_state_id=invoice_info["invoice_state_id"],
                                               invoice_maker_id=invoice_info["maker_id"],
                                               inspector_id=invoice_info["inspector_id"],
                                               keeper_id=invoice_info["storeman_id"],
                                               salesman_id=invoice_info["salesman_id"],
                                               supplier_id=invoice_info["supplier_id"],
                                               purchaser_id=invoice_info["buyer_id"],
                                               inventory_direction_id=invoice_info["stock_direction_id"],
                                               storage_warehouse_id = invoice_info["warehouse_id"],
                                               transport_goods_number=invoice_info["freight_number"],
                                               department_id=invoice_info["department_id"],
                                               remark=invoice_info["remarks"]
                                               )
            self.controlsession.add(r_obj)
            if is_commit:
                self.controlsession.commit()
        except Exception:
            raise

    def save_detail_info(self, invoice_id, detail_info, is_commit=False):
        """
        保存物料明细信息
        :param detail_info:
        :return:
        """
        try:
            from control_center.warehouse_manage.warehouse_allocation_manage.control.allocation_op import \
                add_warehouse_id_to_link
            op = MaterialWarehouseInfoOp()
            link_dict = {}
            material_dict = {}
            for element in detail_info:
                key = str(invoice_id) + str(element['warehouse_id']) + "_" + str(element['material_id'])
                if key in material_dict:
                    material_dict[key]['inventory_number'] += element['inventory_number']
                else:
                    material_dict[key] = element
            print "11111111111111111111111111111", material_dict
            for element in material_dict.values():
                try:
                    op.warehouse_link_status(element['warehouse_id'])
                    link_dict = add_warehouse_id_to_link(element['warehouse_id'], link_dict)

                except Exception:
                    # 回滚链接数
                    for key, value in link_dict.items():
                        for i in range(0, value):
                            op.delete_warehouse_link(key)
                    raise
                print "22222222222222222", element
            # for item in detail_info:
                item_obj = WarehouseInPurchaseDetail(invoice_id=invoice_id,
                                                     material_id=element["material_id"],
                                                     material_num=element["inventory_number"],
                                                     warehouse_id=element["warehouse_id"],
                                                     is_good_material=element["is_nondefective"])
                self.controlsession.add(item_obj)
            if is_commit:
                self.controlsession.commit()
        except Exception:
            raise

    def get_outbuy_info_by_number(self, invoice_number):
        """
        更具单据单号查询单据信息
        :param invoice_number:
        :return:
        """
        try:
            rs = self.controlsession.query(WarehouseInPurchaseInvoice).filter(
                WarehouseInPurchaseInvoice.invoice_number == invoice_number).first()
            if rs:
                r_data = rs.to_json()
            else:
                raise CodeError(300, u"单据信息查询失败")
            pass
        except CodeError:
            raise
        except Exception:
            raise
        return r_data

