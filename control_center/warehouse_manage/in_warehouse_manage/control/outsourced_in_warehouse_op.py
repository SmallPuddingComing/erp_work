#!/usr/bin/python
# -*- coding:utf-8 -*-

import traceback
import datetime
from sqlalchemy import and_, func, or_
from flask import session
from public.exception.custom_exception import CodeError
from data_mode.erp_supply.control_base.controlBase import ControlEngine
from data_mode.user_center.control.mixOp import MixUserCenterOp
from data_mode.erp_supply.mode.material_repertory_model.warehousein_outsourcing_detail \
    import WarehouseInOutsourcingDetail
from data_mode.erp_supply.mode.material_repertory_model.warehousein_outsourcing_invoice \
    import WarehouseInOutsourcingInvoice
from control_center.supply_chain.supplier_manage.control.supplier_baseinfo_op import SupplierBaseInfoOp
from control_center.supply_chain.material_warehosue.control.material_warehose_info_op import MaterialWarehouseInfoOp
from config.share.share_define import WarehouseManagementAttr


class OutsourcedInWarehouseOp(ControlEngine):
    """
    委外加工入库op
    """
    def __init__(self):
        """
        控制引擎初始化
        :return:
        """
        ControlEngine.__init__(self)

    def get_outsourced_list_info(self, page, per_page, search_dict=None):
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
            print "search_dict:::::::::::::::::::::::", search_dict
            if search_dict is not None:
                invoice_number = search_dict.get("invoice_number")
                if invoice_number is not None and invoice_number is not "" and invoice_number is not u"":
                    condition.append(WarehouseInOutsourcingInvoice.invoice_number == invoice_number)
                start_time = search_dict.get("start_time")
                if start_time is not None and start_time is not "" and start_time is not u"":
                    condition.append(WarehouseInOutsourcingInvoice.invoice_date >= start_time)
                stop_time = search_dict.get("stop_time")
                if stop_time is not None and stop_time is not "" and stop_time is not u"":
                    condition.append(WarehouseInOutsourcingInvoice.invoice_date <= stop_time)
                invoice_type_id = search_dict.get("invoice_type_id")
                # 这里的单据类型搜索实际上是库存方向的搜索
                if invoice_type_id is not None and invoice_type_id is not "" and invoice_type_id is not u"":
                    condition.append(WarehouseInOutsourcingInvoice.inventory_direction_id == invoice_type_id)

                invoice_state_id = search_dict.get("invoice_state")
                invoice_state_id = search_dict.get("invoice_state_id")
                if invoice_state_id is not None and invoice_state_id is not u"" and invoice_state_id is not "":
                    condition.append(WarehouseInOutsourcingInvoice.invoice_state_id == invoice_state_id)
                # 供应商可能存在同名情况
                pro_unit_name = search_dict.get("processing_unit")
                if pro_unit_name is not None:
                    from data_mode.erp_supply.mode.supply_manage_mode.supplier_info import SupplierBaseInfo
                    condition_pro = or_()
                    rs_supplier = self.controlsession.query(SupplierBaseInfo).filter_by(supplier_name=pro_unit_name).all()
                    for item in rs_supplier:
                        item_supplier = item.to_json()
                        condition_pro.append(WarehouseInOutsourcingInvoice.process_company_id == item_supplier["id"])
                    condition.append(condition_pro)
            print condition
            rs = self.controlsession.query(WarehouseInOutsourcingInvoice).\
                filter(condition).limit(per_page).offset(start).all()
            total = self.controlsession.query(func.count(WarehouseInOutsourcingInvoice.id)).filter(condition).scalar()
            invoice_info_list = []
            user_op = MixUserCenterOp()
            supplier_op = SupplierBaseInfoOp()
            print "22222222222222222222222222", len(rs)
            for item in rs:
                invoice_dict = {}
                item_data = item.to_json()
                print item_data["invoice_number"]
                invoice_dict["invoice_number"] = item_data["invoice_number"]
                # 单据类型 实际上是库存方向
                invoice_dict["invoice_type_id"] = item_data["stock_direction_id"]
                if item_data["stock_direction_id"] == "17-1":
                    invoice_dict["invoice_type"] = u"蓝色单据"
                elif item_data["stock_direction_id"] == "17-2":
                    invoice_dict["invoice_type"] = u"红色单据"
                else:
                    CodeError(300, u"单据类型错误")
                invoice_dict["invoice_state_id"] = item_data["invoice_state_id"]
                invoice_dict["invoice_state"] = WarehouseManagementAttr.INVOICE_STATE.\
                    get(item_data["invoice_state_id"])
                invoice_dict["invoice_date"] = item_data["invoice_date"]
                invoice_dict["processing_unit_id"] = item_data["processing_unit_id"]
                # 根据供应商id获取供应商信息
                if item_data["processing_unit_id"] is not None and item_data["processing_unit_id"] is not "":
                    rs_supplier = supplier_op.get_supplier_base_info(item_data["processing_unit_id"])
                    invoice_dict["processing_unit"] = rs_supplier["supplier_name"]
                else:
                    raise CodeError(300, u"获取供应商信息失败")

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
            print "len:           ", len(invoice_info_list)
        except CodeError:
            raise
        except Exception:
            raise
        return invoice_info_list, total

    @staticmethod
    def get_outsourced__type():
        """
        获取所有的委外入库类型
        :return:
        """
        from config.share.share_define import translate_dict_to_list
        from config.share.share_define import WarehouseManagementAttr
        sell_outwarehouse_type_list = translate_dict_to_list(WarehouseManagementAttr.OUTSOURCING_TYPE)
        sorted_type_list = []
        for data in sell_outwarehouse_type_list:
            temp_dict = dict()
            temp_dict['outsource_type_id'] = data.get("id")
            temp_dict["outsourcing_type"] = data.get("name")
            sorted_type_list.append(temp_dict)
        return sorted_type_list

    def get_crate_outsourced_info(self, invoice_type_id):
        """
        获取委外加工入库新建页所需数据
        :param invoice_type_id:         单据类型 红蓝单据
        :return:
        """
        try:
            from redis_cache.public_cache.serial_number import create_number
            invoice_dict = dict()
            # 获取单号
            invoice_dict["invoice_number"] = create_number("PBIN{DATE}{SERIAL_NUMBER_4}",
                                                           db_session=self.controlsession,
                                                           table_name=WarehouseInOutsourcingInvoice.__tablename__,
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

    def get_copy_outsourced_info(self, invoice_number):
        """
        获取委外加工入库所需数据
        :param invoice_number:
        :return:
        """
        try:
            from redis_cache.public_cache.serial_number import create_number
            invoice_dict = dict()
            # 获取单号
            invoice_dict["invoice_number"] = create_number("PBIN{DATE}{SERIAL_NUMBER_4}",
                                                           db_session=self.controlsession,
                                                           table_name=WarehouseInOutsourcingInvoice.__tablename__,
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
            from data_mode.erp_supply.base_op.material_op.baseinfo_op import Baseinfo_Op
            m_op = Baseinfo_Op()
            wh_op = MaterialWarehouseInfoOp()
            supplier_op = SupplierBaseInfoOp()
            if invoice_number is not None:
                rs_invoice = self.controlsession.query(WarehouseInOutsourcingInvoice).filter(
                    WarehouseInOutsourcingInvoice.invoice_number == invoice_number
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
                    # 加工单位
                    invoice_dict["processing_unit_id"] = invoice_data["processing_unit_id"]
                    rs_pro = supplier_op.get_supplier_base_info(invoice_data["processing_unit_id"])
                    invoice_dict["processing_unit"] = rs_pro["supplier_name"]
                    # 收料仓库
                    if invoice_data["warehouse_id"] is not None:
                        rs_wh = wh_op.get_warehouse_name_by_id(invoice_data["warehouse_id"])
                        invoice_dict["warehouse"] = rs_wh["warehouse_name"]
                        invoice_dict["warehouse_id"] = invoice_data["warehouse_id"]
                    else:
                        invoice_dict["warehouse"] = ""
                        invoice_dict["warehouse_id"] = ""
                    # 委外类型
                    invoice_dict["outsourcing_type"] = WarehouseManagementAttr.OUTSOURCING_TYPE[
                                                                    invoice_data["outsource_type_id"]]
                    invoice_dict["outsource_type_id"] = invoice_data["outsource_type_id"]
                    # 运货单号
                    invoice_dict["freight_number"] = invoice_data["freight_number"]
                    # 备注
                    invoice_dict["remarks"] = invoice_data["remarks"]

                    rs_detail = self.controlsession.query(WarehouseInOutsourcingDetail).filter(
                        WarehouseInOutsourcingDetail.invoice_id == rs_invoice.id).all()
                    detail_list = []
                    for item in rs_detail:
                        item_dict = item.to_json()
                        m_rs = m_op.get_baseinfo_by_id(item_dict["material_id"])
                        if m_rs[0] == 0:
                            item_dict["material_code"] = m_rs[1]["code"]
                            item_dict["material_name"] = m_rs[1]["name"]
                            item_dict["specification_model"] = m_rs[1]["specifications"]
                            item_dict["unit"] = m_rs[1]["measureunit"]
                        else:
                            raise CodeError(300, u"查询物料信息失败")
                        # 根据 item_dict["warehouse_id"] 获取仓库信息
                        rs_wh = wh_op.get_warehouse_name_by_id(item_dict["warehouse_id"])
                        item_dict["warehouse"] = rs_wh["warehouse_name"]
                        detail_list.append(item_dict)
                    invoice_dict["rows"] = detail_list
            pass
        except CodeError:
            raise
        except Exception:
            raise
        return invoice_dict

    def get_update_outsourced_info(self, invoice_number):
        """
        获取委外加工入库所需数据
        :param invoice_number:
        :return:
        """
        try:
            user_op = MixUserCenterOp()
            from data_mode.erp_supply.base_op.material_op.baseinfo_op import Baseinfo_Op
            m_op = Baseinfo_Op()
            wh_op = MaterialWarehouseInfoOp()
            supplier_op = SupplierBaseInfoOp()
            if invoice_number is not None:
                rs_invoice = self.controlsession.query(WarehouseInOutsourcingInvoice).filter(
                    WarehouseInOutsourcingInvoice.invoice_number == invoice_number
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
                    # 加工单位
                    rs_pro = supplier_op.get_supplier_base_info(invoice_data["processing_unit_id"])
                    invoice_data["processing_unit"] = rs_pro["supplier_name"]
                    # 收料仓库
                    if invoice_data["warehouse_id"] is not None:
                        rs_wh = wh_op.get_warehouse_name_by_id(invoice_data["warehouse_id"])
                        invoice_data["warehouse"] = rs_wh["warehouse_name"]
                    else:
                        invoice_data["warehouse"] = ""
                        invoice_data["warehouse_id"] = ""
                    # 委外类型
                    invoice_data["outsourcing_type"] = WarehouseManagementAttr.OUTSOURCING_TYPE[
                                                                    invoice_data["outsource_type_id"]]
                    rs_detail = self.controlsession.query(WarehouseInOutsourcingDetail).filter(
                        WarehouseInOutsourcingDetail.invoice_id == rs_invoice.id).all()
                    detail_list = []
                    for item in rs_detail:
                        item_dict = item.to_json()
                        m_rs = m_op.get_baseinfo_by_id(item_dict["material_id"])
                        if m_rs[0] == 0:
                            item_dict["material_code"] = m_rs[1]["code"]
                            item_dict["material_name"] = m_rs[1]["name"]
                            item_dict["specification_model"] = m_rs[1]["specifications"]
                            item_dict["unit"] = m_rs[1]["measureunit"]
                        else:
                            raise CodeError(300, u"查询物料信息失败")
                        # 根据 item_dict["warehouse_id"] 获取仓库信息
                        wh_rs = wh_op.get_warehouse_name_by_id(item_dict["warehouse_id"])
                        item_dict["warehouse"] = wh_rs["warehouse_name"]
                        detail_list.append(item_dict)
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

    def save_outsourced_info(self, invoice_info):
        """
        保存委外加工入库单据信息
        :param invoice_info:
        is_commit: int				# 是否提交(1: 提交， 0：保存)
        invoice_number: str		# 单据编号
            invoice_date: str			# 单据日期
        remarks: str				# 备注
        maker_id: int				# 制单人ID
        invoice_type_id: str			# 单据类型ID
        invoice_state_id: str		# 单据状态ID
        storeman:				# 保管员
        outsource_type_id: str		# 委外类型ID
        processingUnit_id: int		# 加工单位ID
        inspector：				# 验收员
        stock_direction_id: str		# 库存方向ID
        warehouse_id: int	# 收料仓库ID
        salesman_id: int			# 业务员ID
        freight_number：			# 运货单号

        rows:[		#明细信息
        {
        material_id: int		# 物料ID
        stock_number			# 即时库存
        warehouse_id: int		# 收料仓库ID
        materiel_num: int		# 实收数量
        is_nondefective: int 	# 检验是否为良品(1:是、0:否)
        }
        ]
        }
        保存委外加工入库信息
        :return:
        """
        try:
            print "1111111111111111111111", invoice_info["stock_direction_id"],
            # 保存单据基本信息
            self.save_invoice_info(invoice_info, is_commit=True)
            # 查询单据id，然后保存详细信息
            print "2222222222222"
            rs_invoice = self.get_outsourced_info_by_number(invoice_info["invoice_number"])
            print "4444444444", type(rs_invoice), rs_invoice
            self.save_detail_info(rs_invoice["invoice_id"], invoice_info["rows"], is_commit=False)
            print "33333333333333"
            # 添加操作记录
            from data_mode.erp_supply.base_op.material_op.baseinfo_op import Baseinfo_Op
            material_base_op = Baseinfo_Op()
            material_base_op.add_operate_record(uid=session['user']['id'],
                                                detail=u"新增委外加工入库单据",
                                                id_list=rs_invoice["invoice_id"],
                                                is_commit=False,
                                                db_session=self.controlsession,
                                                tablename=WarehouseInOutsourcingInvoice.__tablename__
                                                )
            self.controlsession.commit()
            pass

        except CodeError:
            rs = self.controlsession.query(WarehouseInOutsourcingInvoice).filter(
                WarehouseInOutsourcingInvoice.invoice_number == invoice_info["invoice_number"]
            ).first()
            if rs:
                self.controlsession.delete(rs)
                self.controlsession.commit()
            self.controlsession.rollback()
            raise
        except Exception:
            rs = self.controlsession.query(WarehouseInOutsourcingInvoice).filter(
                WarehouseInOutsourcingInvoice.invoice_number == invoice_info["invoice_number"]
            ).first()
            if rs:
                self.controlsession.delete(rs)
                self.controlsession.commit()
            self.controlsession.rollback()
            raise
        return True

    def commit_outsourced_info(self, invoice_data_dict):
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

            rs = self.controlsession.query(WarehouseInOutsourcingInvoice).\
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
        rs = self.controlsession.query(WarehouseInOutsourcingInvoice).filter_by(invoice_number=invoice_number).first()
        if rs:
            invoice_id = rs.id
        else:
            CodeError(300, u"没有该单据")
        oper_op = Operate_Op()
        start = (page - 1) * per_page
        record_datas, total = oper_op.get_record(start, per_page, WarehouseInOutsourcingInvoice.__tablename__, invoice_id)
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

    def update_outsourced_info(self, invoice_info):
        """
        invoice_number: str		# 单据编号
        invoice_date: str			# 单据日期
        remarks: str				# 备注
        maker_id: int				# 制单人ID
        invoice_type_id: str			# 单据类型ID
        invoice_state_id: str		# 单据状态ID
        storeman:				# 保管员
        outsource_type_id: str		# 委外类型ID
        processingUnit_id: int		# 加工单位ID
        inspector：				# 验收员
        stock_direction_id: str		# 库存方向ID
        warehouse_id: int	# 收料仓库ID
        salesman_id: int			# 业务员ID
        freight_number：			# 运货单号

        rows:[		#明细信息
        {
        material_id: int		# 物料ID
        stock_number			# 即时库存
        warehouse_id: int		# 收料仓库ID
        materiel_num: int		# 实收数量
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
            rs_invoice = self.controlsession.query(WarehouseInOutsourcingInvoice).filter_by(
                    invoice_number=invoice_info["invoice_number"]).first()
            if not rs_invoice:
                raise CodeError(300, u"保存失败")
            elif rs_invoice.invoice_state_id != WarehouseManagementAttr.TEMPORARY_STORAGE:
                raise CodeError(300, u"只允许修改暂存状态下的单据")
            else:
                # 先把原来的绑定的物料信息删除掉
                rs_detail = self.controlsession.query(WarehouseInOutsourcingDetail).\
                    filter_by(invoice_id=rs_invoice.id).all()
                for detail_item in rs_detail:
                    self.controlsession.delete(detail_item)
                # self.controlsession.commit()
                # 更新新的单据信息 单号，制单人 类型，状态，日期，库存方向 不能修改
                rs_invoice.inspector_id = invoice_info["inspector_id"]
                rs_invoice.keeper_id = invoice_info["storeman_id"]
                rs_invoice.salesman_id = invoice_info["salesman_id"]
                rs_invoice.supplier_id = invoice_info["supplier_id"]
                rs_invoice.storage_warehouse_id = invoice_info["warehouse_id"]
                # rs_invoice.inventory_direction_id = invoice_info["stock_direction_id"]
                rs_invoice.transport_goods_number = invoice_info["freight_number"]
                rs_invoice.process_company_id = invoice_info["processing_unit_id"]
                rs_invoice.outsource_type_id = invoice_info["outsource_type_id"]
                rs_invoice.remark = invoice_info["remarks"]
                self.controlsession.add(rs_invoice)

                for item in invoice_info["rows"]:
                    item_obj = WarehouseInOutsourcingDetail( invoice_id=rs_invoice.id,
                                                             material_id=item["material_id"],
                                                             material_num=item["inventory_number"],
                                                             warehouse_id=item["warehouse_id"],
                                                             is_good_material=item["is_nondefective"])
                    self.controlsession.add(item_obj)

                # 添加操作记录
                from data_mode.erp_supply.base_op.material_op.baseinfo_op import Baseinfo_Op
                material_base_op = Baseinfo_Op()
                material_base_op.add_operate_record(uid=session['user']['id'],
                                                    detail=u"修改委外加工入库单据",
                                                    id_list=rs_invoice.id,
                                                    is_commit=False,
                                                    db_session=self.controlsession,
                                                    tablename=WarehouseInOutsourcingInvoice.__tablename__
                                                    )
            self.controlsession.commit()
            pass
        except CodeError:
            raise
        except Exception:
            raise
        return True

    def outsourced_invoice_delete(self, invoice_number):
        """
        删除委外加工入库单据
        :param invoice_number: 单据单号
        :return:
        """
        try:
            if invoice_number is None:
                raise CodeError(300, u"单据未选中")
            rs = self.controlsession.query(WarehouseInOutsourcingInvoice).filter_by(invoice_number=invoice_number).first()
            if rs:
                invoice_info = rs.to_json()
                if invoice_info["invoice_state_id"] == WarehouseManagementAttr.COMPLETED:
                    raise CodeError(300, u"该单据不能被删除")
                else:
                    self.controlsession.delete(rs)
            else:
                raise CodeError(300, u"删除失败")
            self.controlsession.commit()
        except CodeError:
            self.controlsession.rollback()
        except Exception:
            self.controlsession.rollback()
        return True

    def check_outsourced_invoice_number(self, invoice_number):
        """
        单据单号唯一性检查
        :param invoice_number:
        :return:
        """
        from redis_cache.public_cache.serial_number import check_number_exists
        return check_number_exists(self.controlsession,
                                   WarehouseInOutsourcingInvoice.__tablename__,
                                   'invoice_number',
                                   invoice_number)

    def save_invoice_info(self, invoice_info, is_commit=False):
        """
        保存外购入库单单据信息
        :param invoice_info:
        :return:
        """
        try:
            r_obj = WarehouseInOutsourcingInvoice(invoice_number=invoice_info["invoice_number"],
                                                  invoice_date=invoice_info["invoice_date"],
                                                  invoice_type_id=invoice_info["invoice_type_id"],
                                                  invoice_state_id=invoice_info["invoice_state_id"],
                                                  invoice_maker_id=invoice_info["maker_id"],
                                                  inspector_id=invoice_info["inspector_id"],
                                                  keeper_id=invoice_info["storeman_id"],
                                                  salesman_id=invoice_info["salesman_id"],
                                                  process_company_id=invoice_info["processing_unit_id"],
                                                  storage_warehouse_id=invoice_info["warehouse_id"],
                                                  outsource_type_id=invoice_info["outsource_type_id"],
                                                  inventory_direction_id=invoice_info["stock_direction_id"],
                                                  transport_goods_number=invoice_info["freight_number"],
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
                item_obj = WarehouseInOutsourcingDetail(invoice_id=invoice_id,
                                                        material_id=element["material_id"],
                                                        material_num=element["inventory_number"],
                                                        warehouse_id=element["warehouse_id"],
                                                        is_good_material=element["is_nondefective"])
                self.controlsession.add(item_obj)

            if is_commit:
                self.controlsession.commit()
        except Exception:
            raise

    def get_outsourced_info_by_number(self, invoice_number):
        """
        更具单据单号查询单据信息
        :param invoice_number:
        :return:
        """
        try:
            rs = self.controlsession.query(WarehouseInOutsourcingInvoice).filter(
                WarehouseInOutsourcingInvoice.invoice_number == invoice_number).first()
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