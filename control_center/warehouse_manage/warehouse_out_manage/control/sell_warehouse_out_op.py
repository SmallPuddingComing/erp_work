#!/usr/bin/python
# -*- coding:utf-8 -*-
#    Copyright(c) 2015-2016 JmGo Company
#    All rights reserved.
#
#    文件名 : sell_warehouse_out_op.py
#    作者   : ChengQian
#  电子邮箱 : qcheng@jmgo.com
#    日期   : 2017/1/13 13:54
#
#     描述  :
#
import os
import traceback
from flask import session
from datetime import datetime
from sqlalchemy import and_, func
from sqlalchemy import cast, LargeBinary
from public.logger.syslog import SystemLog
from public.exception.custom_exception import CodeError
from public.function.tools import check_type
from config.service_config.returncode import ServiceCode
from config.share.share_define import get_key_by_value
from config.share.share_define import WarehouseManagementAttr
from data_mode.erp_supply.control_base.controlBase import ControlEngine
from data_mode.erp_supply.base_op.warehouse_manage_op.inventory_op import pub_batch_in_warehouse
from data_mode.erp_supply.base_op.warehouse_manage_op.inventory_op import pub_batch_out_warehouse
from data_mode.erp_supply.base_op.warehouse_manage_op.inventory_op import pub_get_inventory
from redis_cache.public_cache.serial_number import create_number
from data_mode.erp_supply.mode.material_repertory_model.warehouse_out_sell_invoice import WarehouseOutSellInvoice
from data_mode.erp_supply.mode.material_repertory_model.warehouse_out_sell_detail import WarehouseOutSellDetail
from config.share.share_define import is_None
from control_center.supply_chain.material_warehosue.control.material_warehose_info_op import MaterialWarehouseInfoOp


class SellWarehousOutOp(ControlEngine):
    def __init__(self):
        ControlEngine.__init__(self)

    def check_invoice_number(self, invoice_number):
        from redis_cache.public_cache.serial_number import check_number_exists
        return check_number_exists(self.controlsession,
                                   WarehouseOutSellInvoice.__tablename__,
                                   'invoice_number',
                                   invoice_number)

    def create_sell_warehouse_number(self, is_red_invoice_flag=None):
        """
        :param is_red_invoice_flag: 红蓝单据的标识，1：表示红字单据，0：表示蓝字单据
        :return: # 创建其他出库单据单号
        """
        if is_red_invoice_flag is None:
            raise ValueError("parameter is_red_invoice_flag must be a value in [0, 1]")
        if is_red_invoice_flag not in [0, 1]:
            raise ValueError("parameter is_red_invoice_flag must be a value in [0, 1]")
        if is_red_invoice_flag:
            invoice_number = create_number('SROU{DATE}{SERIAL_NUMBER_4}',
                    self.controlsession,
                    WarehouseOutSellInvoice.__tablename__,
                    'invoice_number',
                    is_auto_create=True)
        else:
            invoice_number = create_number('SBOU{DATE}{SERIAL_NUMBER_4}',
                    self.controlsession,
                    WarehouseOutSellInvoice.__tablename__,
                    'invoice_number',
                    is_auto_create=True)
        return invoice_number

    def get_order_baseinfo(self, **kwargs):
        from control_center.supply_chain.customer_manage.control.customer_info_op import CustomerInfoOp
        customer_op = CustomerInfoOp()
        invoice_number = kwargs.get("invoice_number") # 单据单号
        start_time = kwargs.get("start_time") # 开始时间
        stop_time = kwargs.get("stop_time") # 结束时间
        invoice_type_id = kwargs.get("invoice_type") # 单据类型ID（红蓝单据）
        invoice_state_id = kwargs.get("invoice_state") # 单据状态ID
        purchase_unit = kwargs.get("purchase_unit") # 销售出库购货单位（即客户信息）
        page = kwargs.get("page") # 需要分页时的当前分页页数
        pagecount = kwargs.get("pagecount") # 需要分页时每页最多显示的记录数

        if (start_time is not None and stop_time is None) or (start_time is None and stop_time is not None):
            raise ValueError("start_time and stop_time both must be None or not None ")
        elif start_time is not None and stop_time is not None:
            if start_time > stop_time:
                raise ValueError("start_time must be not more than stop_time")
        if (page is not None and pagecount is None) or (page is None and pagecount is not None):
            raise ValueError("page and pagecount both must be positive whole number or None")
        elif page is not None and pagecount is not None:
            if page <= 0 or pagecount <= 0:
                raise ValueError("page and pagecount both must be positive whole number or None")

        # para_list中元素所代表的含义与下属rule中添加的数据库搜索条件息息相关，谨慎修改
        para_list = [invoice_number, start_time, stop_time, invoice_type_id, invoice_state_id, purchase_unit]
        para_map_dict = {}
        for k in range(0, len(para_list)): # 将参数通过索引映射
            para_map_dict[str(k)] = para_list[k]

        None_list = list(filter(is_None, para_list))
        if not None_list: # 表示未传入任何参数，搜索所有的数据
            total, invoice_data_list = self.get_all_invoice_baseinfo(page, pagecount)
        else:
            invoice_data_list = []
            rule = and_()
            useful_para_list = []
            for idx, search_para in enumerate(para_list):
                if search_para is not None:
                    para_idx = para_list.index(search_para, idx)
                    useful_para_list.append(para_idx)

            for idx in useful_para_list:
                if idx == 0: # 单据单号搜索条件
                    rule.append(WarehouseOutSellInvoice.invoice_number.cast(LargeBinary)==invoice_number)
                elif idx == 1: # 表示开始时间存在
                    s_date = datetime.strptime(start_time, "%Y-%m-%d").date()
                    rule.append(func.date_format(WarehouseOutSellInvoice.invoice_date, '%Y-%m-%d') >= s_date)
                elif idx == 2: # 表示结束时间存在 （开始和结束时间必须同时存在）
                    e_date = datetime.strptime(stop_time, "%Y-%m-%d").date()
                    rule.append(func.date_format(WarehouseOutSellInvoice.invoice_date, '%Y-%m-%d') <= e_date)
                elif idx == 3: # 表示单据类型（红蓝单据，对应了库存方向）
                    rule.append(WarehouseOutSellInvoice.inventory_direction_id.cast(LargeBinary)==invoice_type_id)
                elif idx == 4: # 表示单据状态
                    rule.append(WarehouseOutSellInvoice.invoice_state_id.cast(LargeBinary)==invoice_state_id)
                elif idx == 5: # 表示销售出库购货单位
                    #  查询客户信息表中的customer_name字段为purchase_unit的客户ID列表
                    customer_id_list = customer_op.get_customer_id_by_name(purchase_unit)
                    if customer_id_list:
                        rule.append(WarehouseOutSellInvoice.customer_id.in_(customer_id_list))
                    else: # 表示该购货单位对应的单据不存在
                        total = 0
                        return total, invoice_data_list
            total = self.controlsession.query(func.count(WarehouseOutSellInvoice.id)).filter(rule).scalar()

            if page is None: # 表示不需要分页
                invoice_datas = self.controlsession.query(WarehouseOutSellInvoice).filter(rule).order_by(
                    WarehouseOutSellInvoice.id).all()
            else:
                start = (page - 1) * pagecount
                invoice_datas = self.controlsession.query(WarehouseOutSellInvoice).filter(rule).order_by(
                    WarehouseOutSellInvoice.id).limit(pagecount).offset(start)
            if invoice_datas:
                for data in invoice_datas:
                    invoice_dict = self.paras_invoice_fields(data)
                    invoice_data_list.append(invoice_dict)
        return total, invoice_data_list

    def get_all_invoice_baseinfo(self, page=None, pagecount = None):
        """
        :param page: 分页功能中当前分页的页数
        :param pagecount: 分页功能中每页最多显示的记录数
        :return: 返回记录总数及需要显示的记录列表
        """
        if page is None and pagecount is None:
            order_datas = self.controlsession.query(WarehouseOutSellInvoice).order_by(WarehouseOutSellInvoice.id).all()
        elif (page is None and pagecount is not None) or (page is not None and pagecount is None):
            raise ValueError("page and pagecount both must be None or both positive integer")
        else:
            if page <= 0 or pagecount <= 0:
                raise ValueError("page and pagecount both must be None or both positive integer")
            start = (page - 1) * pagecount
            order_datas = self.controlsession.query(WarehouseOutSellInvoice).order_by(WarehouseOutSellInvoice.id
                                                                          ).limit(pagecount).offset(start)

        total = 0
        order_datas_list = []
        if order_datas:
            total = self.controlsession.query(func.count(WarehouseOutSellInvoice.id)).scalar() # 记录总数
            for data in order_datas:
                invoice_dict = self.paras_invoice_fields(data)
                order_datas_list.append(invoice_dict)
            return  total, order_datas_list
        else:
            return total, order_datas_list

    def paras_invoice_fields(self, data_object):
        """
        :param data_object: 其他出库单据表对象
        :return:
        """
        from control_center.supply_chain.customer_manage.control.customer_mix_op import QueryCustomerInfo
        from data_mode.user_center.control.mixOp import MixUserCenterOp
        from control_center.supply_chain.material_warehosue.control.material_warehouse_mix_op import GetWarehouseInfo
        customer_op = QueryCustomerInfo()
        user_op = MixUserCenterOp()
        warehouse_op = GetWarehouseInfo()
        if isinstance(data_object, WarehouseOutSellInvoice):
            data = data_object.to_json()
            if data['stock_direction_id'] == WarehouseManagementAttr.BLUE_ORDER_DIRECTION:

                data['invoice_type_direction'] = u"蓝字单据" # 单据类型（红字单据或蓝字单据）
            elif data['stock_direction_id'] == WarehouseManagementAttr.RED_ORDER_DIRECTION:

                data['invoice_type_direction'] = u"红字单据" # 单据类型（红字单据或蓝字单据）
            data['invoice_type'] = WarehouseManagementAttr.INVOICE_TYPE.get(data['invoice_type_id']) # 单据类型
            data['invoice_state'] = WarehouseManagementAttr.INVOICE_STATE.get(data['invoice_state_id']) # 单据状态
            maker_info = user_op.get_user_info(data['maker_id'])
            data['maker'] = maker_info.get("name") # 制作人

            deliver_info = user_op.get_user_info(data['deliver_handler_id'])
            data['deliver_handler'] = deliver_info.get('name') # 发货员

            material_info = user_op.get_user_info(data['storeman_id'])
            data['storeman'] = material_info.get('name') # 保管员

            if data.get('salesman_id') is None or not data.get('salesman_id'):
                data['salesman'] = ""
            else:
                salesman_info = user_op.get_user_info(data['salesman_id'])
                data['salesman'] = salesman_info.get('name') # 业务员

            data['outgoing_type'] = WarehouseManagementAttr.SELL_OUTWAREHOUSE_TYPE.get(data['outgoingType_id']) # 其他出库出库类型
            customer_info = customer_op.get_customer_id_info(data['purchaseUnit_id'])
            data['purchase_unit'] = customer_info.get("customer_name") if customer_info else "" # 客户

            if data.get('warehouse_id') is None or not data.get('warehouse_id'):
                data['deliver_warehouse'] = ""
            else:
                warehouse_info = warehouse_op.get_warehouse_id_info(data['warehouse_id'])
                data['deliver_warehouse'] = warehouse_info.get("warehouse_name") if warehouse_info else "" # 发货仓库

            data['stock_direction'] = WarehouseManagementAttr.REPERTORY_DIRECTION_TYPE.get(data['stock_direction_id']) # 库存方向

            if data.get('department_id') is None or not data.get('department_id'):
                data['department_organization'] = ""
            else:
                department_info = user_op.get_department_name_byID(data['department_id'])
                data['department_organization'] = department_info # 部门组织
            return data
        else:
            raise TypeError("data_object must be an instance of the WarehouseOutOtherInvoice class")

    def get_invoice_baseinfo_by_invoice_number(self, invoice_number=None):
        """
        :param invoice_number:  单据单号
        :return: 返回该单据单号对应的单据基本信息
        """
        if invoice_number is None:
            order_data = self.controlsession.query(WarehouseOutSellInvoice).all()
        else:
            order_data = self.controlsession.query(WarehouseOutSellInvoice).filter(
                WarehouseOutSellInvoice.invoice_number.cast(LargeBinary)==invoice_number).first()
        if order_data is None or not order_data:
            return []
        else:
            order_data_list = self.paras_invoice_fields(order_data)
            return order_data_list

    def get_invoice_materialinfo_by_invoice_id(self, invoice_id=None):
        """
        :param invoice_id:  单据单号的ID
        :return: 根据单据单号ID返回该单据对应的物料明细信息
        """
        from control_center.supply_chain.material_warehosue.control.material_warehouse_mix_op import GetWarehouseInfo
        from data_mode.erp_supply.base_op.material_op.baseinfo_op import Baseinfo_Op
        from control_center.warehouse_manage.warehouse_out_manage.control.other_warehouse_out_op import OtherWarehousOutOp
        warehouse_op = GetWarehouseInfo()
        baseinfo_op = Baseinfo_Op()
        other_op = OtherWarehousOutOp()
        if invoice_id is None:
            raise ValueError("invoice_id should be inputed")
        material_datas = self.controlsession.query(WarehouseOutSellDetail).filter(
            WarehouseOutSellDetail.invoice_id==invoice_id).all()
        if not material_datas:
            raise ValueError("when the invoice_id is %s, the record does not exist" % invoice_id)
        else:
            data_list = []
            material_data_list = [data.to_json() for data in material_datas]
            for data in material_data_list:
                # 根据物料ID获取物料的所有信息
                search_flag, baseinfo_datas = baseinfo_op.get_baseinfo_by_id_ex(data['material_id'])
                if search_flag != 0:
                    raise ValueError(baseinfo_datas)
                baseinfo_dict = baseinfo_op.change_material_baseinfo_key(baseinfo_datas)
                baseinfo_dict['stock_number'] = pub_get_inventory(data.get('warehouse_id'), data.get('material_id')) # 即时库存
                baseinfo_dict['warehouse_id'] = data.get('warehouse_id')
                warehouse_info = warehouse_op.get_warehouse_id_info(data['warehouse_id'])
                baseinfo_dict['deliver_warehouse'] = warehouse_info.get("warehouse_name") if warehouse_info else "" # 发货仓库
                baseinfo_dict['inventory_number'] = data.get('inventory_number')
                baseinfo_dict['is_nondefective'] = data.get('is_nondefective')

                select_data = other_op.select_invoice_associated_material(baseinfo_dict)
                data_list.append(select_data)
                # data_list.append(baseinfo_dict)
            return data_list

    def get_red_or_blue_invoice_baseinfo(self, red_blue_flag=None):
        """
        :param red_blue_flag:  红蓝单据类型
        :return: 返回红单据类型或蓝单据类型或全部单据基本信息
        """
        blue_flag = WarehouseManagementAttr.BLUE_ORDER_DIRECTION # 蓝字单据对应库存方向为“正常”
        red_flag = WarehouseManagementAttr.RED_ORDER_DIRECTION # 红色单据对应库存方向为“退回”

        if red_blue_flag is None:
            total, invoice_data_list = self.get_all_invoice_info()
            return invoice_data_list
        elif red_blue_flag == blue_flag: # 蓝字单据
            invoice_datas = self.controlsession.query(WarehouseOutSellInvoice).filter(
                WarehouseOutSellInvoice.inventory_direction_id.cast(LargeBinary)==blue_flag).order_by(
                WarehouseOutSellInvoice.id).all()
        elif red_blue_flag == red_flag: # 红字单据
            invoice_datas = self.controlsession.query(WarehouseOutSellInvoice).filter(
                WarehouseOutSellInvoice.inventory_direction_id.cast(LargeBinary)==red_flag).order_by(
                WarehouseOutSellInvoice.id).all()
        else:
            raise ValueError("red_blue_flag must be a value in %s" %
                             WarehouseManagementAttr.REPERTORY_DIRECTION_TYPE.keys())

        invoice_data_list = []
        for data in invoice_datas:
            invoice_dict = self.paras_invoice_fields(data)
            invoice_data_list.append(invoice_dict)
        return invoice_data_list

    def get_invoice_baseinfo_by_state(self, invoice_state_type=None):
        """
        :param invoice_state_type: 单据状态类型ID
        :return: 返回指定单据类型的单据记录基本信息
        """
        state_keys = WarehouseManagementAttr.INVOICE_STATE.keys()
        if invoice_state_type is None: # 表示查询所有单据状态的单据记录
            invoice_datas = self.controlsession.query(WarehouseOutSellInvoice).order_by(
                WarehouseOutSellInvoice.id).all()
        else:
            if invoice_state_type not in (state_keys):
                raise ValueError("invoice_state_type must be a value in %s" % state_keys)
            else:
                invoice_datas = self.controlsession.query(WarehouseOutSellInvoice).filter(
                    WarehouseOutSellInvoice.invoice_state_id.cast(LargeBinary)==invoice_state_type).order_by(
                    WarehouseOutSellInvoice.id).all()
        invoice_data_list = []
        for data in invoice_datas:
            invoice_dict = self.paras_invoice_fields(data)
            invoice_data_list.append(invoice_dict)
        return invoice_data_list

    def get_invoice_baseinfo_by_outtype(self, warehouse_out_type=None):
        """
        :param warehouse_out_type: 其他出库出库类型
        :return: 返回指定出库类型的单据记录信息
        """
        warehouse_out_keys = WarehouseManagementAttr.SELL_OUTWAREHOUSE_TYPE.keys()
        if warehouse_out_type is None: # 查询所有出库类型的单据记录信息
            invoice_datas = self.controlsession.query(WarehouseOutSellInvoice).order_by(
                WarehouseOutSellInvoice.id).all()
        else:
            if warehouse_out_type not in warehouse_out_keys:
                raise ValueError("warehouse_out_type must be a value in %s" % warehouse_out_keys)
            else:
                invoice_datas = self.controlsession.query(WarehouseOutSellInvoice).filter(
                    WarehouseOutSellInvoice.outwarehouse_type_id.cast(LargeBinary)==warehouse_out_type).order_by(
                    WarehouseOutSellInvoice.id).all()
        invoice_data_list = []
        for data in invoice_datas:
            invoice_dict = self.paras_invoice_fields(data)
            invoice_data_list.append(invoice_dict)
        return invoice_data_list

    def get_invoice_baseinfo_by_date(self, start_date=None, stop_date=None):
        """
        :param start_date:  查询开始时间
        :param stop_date:  查询结束时间
        :return: 返回指定时间范围内的单据记录信息
        """
        try:
            if start_date is None and stop_date is None:
                invoice_datas = self.controlsession.query(WarehouseOutSellInvoice).order_by(
                    WarehouseOutSellInvoice.id).all()
            elif start_date is not None and stop_date is not None: # 表示搜索时间单内的数据
                s_date = datetime.strptime(start_date, "%Y-%m-%d").date()
                e_date = datetime.strptime(stop_date, "%Y-%m-%d").date()
                invoice_datas = self.controlsession.query(WarehouseOutSellInvoice).filter(
                    func.date_format(WarehouseOutSellInvoice.invoice_date, '%Y-%m-%d') >= s_date,
                    func.date_format(WarehouseOutSellInvoice.invoice_date , '%Y-%m-%d')<= e_date).\
                    order_by(WarehouseOutSellInvoice.id).all()
            else:
                s_date = datetime.strptime(start_date, "%Y-%m-%d").date()
                invoice_datas = self.controlsession.query(WarehouseOutSellInvoice).filter(
                    func.date_format(WarehouseOutSellInvoice.invoice_date, '%Y-%m-%d') == s_date).\
                    order_by(WarehouseOutSellInvoice.id).all()
            invoice_data_list = []
            for data in invoice_datas:
                invoice_dict = self.paras_invoice_fields(data)
                invoice_data_list.append(invoice_dict)
            return invoice_data_list

        except ValueError:
            raise ValueError("the date format is incorrect, the correct date format must be year-month-day")

    def get_invoice_state(self, invoice_number=None):
        """
        :param invoice_number: 单据单号
        :return: 返回该单据单号的状态
        """
        if invoice_number is None:
            raise ValueError("invoice_number can not be None")
        if not isinstance(invoice_number, str):
            raise TypeError("unsupported operand type(s) for function's parameter")

        invoice_state_id = self.controlsession.query(WarehouseOutSellInvoice.invoice_state_id).filter(
            WarehouseOutSellInvoice.invoice_number.cast(LargeBinary)==invoice_number).first()

        if invoice_state_id is None:
            raise ValueError("%s does not exist in the table %s's invoice_number field" %
                             (invoice_number, WarehouseOutSellInvoice.__tablename__))
        else:
            return invoice_state_id[0]

    def get_invoice_id(self, invoice_number):
        """
        :param invoice_number: 单据单号
        :return: 返回该单据单号的ID
        """
        if invoice_number is None:
            raise ValueError("invoice_number can not be None")
        if not isinstance(invoice_number, str):
            raise TypeError("unsupported operand type(s) for function's parameter")

        invoice_id = self.controlsession.query(WarehouseOutSellInvoice.id).filter(
            WarehouseOutSellInvoice.invoice_number.cast(LargeBinary)==invoice_number).first()

        if invoice_id is None:
            raise ValueError("%s does not exist in the table %s's invoice_number field" %
                             (invoice_number, WarehouseOutSellInvoice.__tablename__))
        else:
            return invoice_id[0]

    def get_customer_id(self, invoice_number):
        """
        :param invoice_number:  单据单号
        :return: 返回其他出库类型中单据单号对应的客户ID
        """
        if invoice_number is None:
            raise ValueError("invoice_number can not be None")
        if not isinstance(invoice_number, str):
            raise TypeError("unsupported operand type(s) for function's parameter")

        customer_id = self.controlsession.query(WarehouseOutSellInvoice.customer_id).filter(
            WarehouseOutSellInvoice.invoice_number.cast(LargeBinary)==invoice_number).first()

        if customer_id is None:
            raise ValueError("%s does not exist in the table %s's invoice_number field" %
                             (invoice_number, WarehouseOutSellInvoice.__tablename__))
        else:
            return customer_id[0]

    def get_invoice_operate_record(self, invoice_number, page=1, per_page=5):
        """
        :param invoice_number:
        :param page:
        :param per_page:
        :return: 获取单据单号对应的操作记录
        """
        if invoice_number is None:
            raise ValueError("invoice_number can not be None")
        if not isinstance(invoice_number, str):
            raise TypeError("unsupported operand type(s) for function's parameter")

        from data_mode.erp_supply.base_op.operate_op import Operate_Op
        invoice_id = self.get_invoice_id(invoice_number)
        oper_op = Operate_Op()
        start = (page - 1) * per_page
        record_datas, total = oper_op.get_record(start, per_page, WarehouseOutSellInvoice.__tablename__, invoice_id)
        record_list = []
        if record_datas is None or not record_datas:
            return total, record_list
        else:
            for data in record_datas:
                temp_dict = {}
                temp_dict['operate_name'] = data.get('operator_name')
                temp_dict['operate_time'] = data.get('operate_time')
                temp_dict['operate_content'] = data.get('detail')
                record_list.append(temp_dict)
        return total, record_list

    def save_invoice_data(self, invoice_data_dict, is_commit=0):
        from data_mode.erp_supply.base_op.material_op.baseinfo_op import Baseinfo_Op
        from control_center.supply_chain.customer_manage.control.customer_mix_op import QueryCustomerInfo
        customer_op = QueryCustomerInfo()
        if is_commit is None:
            raise ValueError("is_commit must be a value in [0, 1]")
        if is_commit not in [0, 1]:
            raise ValueError("is_commit must be a value in [0, 1]")
        check_type(invoice_data_dict, (dict,), 'invoice_data_dict')
        # 保存之前检测该单据号是否存在
        assert not self.check_invoice_number(invoice_data_dict['invoice_number']), \
            "number exist. %s" % invoice_data_dict['invoice_number']
        assert invoice_data_dict.get('invoice_state_id')==WarehouseManagementAttr.TEMPORARY_STORAGE, \
            "invoice state should be %s" % WarehouseManagementAttr.TEMPORARY_STORAGE
        base_commit_flag = False
        commit_flag = False
        try:
            # 保存单据的基本信息
            base_commit_flag = self.save_invoice_basedata(invoice_data_dict)
            if base_commit_flag:
                # 批量保存单据的明细信息
                invoice_id = self.get_invoice_id(invoice_data_dict.get('invoice_number'))
                self.patch_save_invoice_detail_data(invoice_id=invoice_id, m_list=invoice_data_dict['rows'])
                material_base_op = Baseinfo_Op()
                material_base_op.add_operate_record(uid=session['user']['id'],
                                                    detail=u"新增销售出库单据",
                                                    id_list=invoice_id,
                                                    is_commit=False,
                                                    db_session=self.controlsession,
                                                    tablename=WarehouseOutSellInvoice.__tablename__
                                                    )
                # 修改客户操作记录
                commit_flag = customer_op.add_customer_links([invoice_data_dict.get("purchaseUnit_id")],
                                                WarehouseOutSellInvoice.__tablename__)
                if not commit_flag:
                    raise CodeError(ServiceCode.service_exception, msg=u"客户操作记录提交失败")
                self.controlsession.commit()
        except Exception:
            self.controlsession.rollback()
            if commit_flag:
                customer_op.del_customer_links([invoice_data_dict.get("purchaseUnit_id")],
                                                WarehouseOutSellInvoice.__tablename__)
            if base_commit_flag:
                self.del_invoice_basedata(invoice_data_dict.get("invoice_number"), is_commit=True)
            raise

    def save_invoice_basedata(self, basedata_dict, is_commit=True):
        try:
            # 先检测要保存的数据是否有效
            self.__save_check_basedata(basedata_dict)
            obj = WarehouseOutSellInvoice(
                invoice_number = basedata_dict.get("invoice_number"),
                invoice_date = basedata_dict.get("invoice_date"),
                invoice_type_id = basedata_dict.get("invoice_type_id"),
                invoice_state_id = basedata_dict.get("invoice_state_id"),
                invoice_maker_id = basedata_dict.get("maker_id"),
                consignor_id = basedata_dict.get("deliver_handler_id"), #发货员
                keeper_id = basedata_dict.get("storeman_id"), # 保管员
                salesman_id = basedata_dict.get("salesman_id"),
                outwarehouse_type_id = basedata_dict.get("outgoingType_id"),
                customer_id = basedata_dict.get("purchaseUnit_id"),
                deliver_warehouse_id = basedata_dict.get("warehouse_id"),
                inventory_direction_id = basedata_dict.get("stock_direction_id"),
                online_store = basedata_dict.get("online_shop"),
                department_id = basedata_dict.get("department_id"),
                remark = basedata_dict.get("remarks")
            )
            self.controlsession.add(obj)
            if is_commit:
                self.controlsession.commit()
                return True
        except Exception:
            self.controlsession.rollback()
            raise

    def patch_save_invoice_detail_data(self, invoice_id, m_list):
        from control_center.warehouse_manage.warehouse_allocation_manage.control.allocation_op import \
            add_warehouse_id_to_link
        check_type(m_list, (list,), 'm_list')
        op = MaterialWarehouseInfoOp()

        # 存储数据前先检查数据的有效性
        self.__save_check_detail(m_list)

        material_dict = {}
        link_dict = {}
        for element in m_list:
            key = str(invoice_id) + str(element['warehouse_id']) + "_" + str(element['material_id'])
            if key in material_dict:
                material_dict[key]['inventory_number'] += element['inventory_number']
            else:
                material_dict[key] = element
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
            self.save_invoice_detail_data(invoice_id,
                                     int(element['material_id']),
                                     int(element['warehouse_id']),
                                     int(element['inventory_number']),
                                     int(element['is_nondefective']))
        return link_dict

    def save_invoice_detail_data(self, invoice_id, material_id, warehouse_id, material_number, is_non_defective):
        check_type(invoice_id, (int, long), 'invoice_id')
        check_type(material_id, (int, long), 'material_id')
        check_type(warehouse_id, (int, long), 'warehouse_id')
        check_type(material_number, (int, long), 'material_number')
        check_type(is_non_defective, (bool,int), 'is_non_defective')

        non_defective = int(is_non_defective)

        obj = WarehouseOutSellDetail(
            invoice_id=invoice_id,
            material_id = material_id,
            material_num=material_number,
            warehouse_id=warehouse_id,
            is_good_material=non_defective
        )
        self.controlsession.add(obj)

    def update_invoice_data(self, invoice_data_dict, is_commit=0):
        from data_mode.erp_supply.base_op.material_op.baseinfo_op import Baseinfo_Op
        assert self.check_invoice_number(invoice_data_dict['invoice_number']), \
            "number isn't existed. %s" % invoice_data_dict['invoice_number']
        assert invoice_data_dict.get('invoice_state_id')==WarehouseManagementAttr.TEMPORARY_STORAGE, \
            "invoice state should be %s" % WarehouseManagementAttr.TEMPORARY_STORAGE
        if is_commit is None:
            raise ValueError("is_commit must be a value in [0, 1]")
        if is_commit not in [0, 1]:
            raise ValueError("is_commit must be a value in [0, 1]")
        check_type(invoice_data_dict, (dict,), 'invoice_data_dict')
        invoice_id = self.get_invoice_id(invoice_data_dict.get("invoice_number"))
        invoice = self.get_invoice_baseinfo_by_invoice_number(invoice_data_dict.get("invoice_number"))
        invoice_data_dict['invoice_number'] = invoice['invoice_number']
        invoice_data_dict['invoice_date'] = invoice['invoice_date']
        invoice_data_dict['maker_id'] = invoice['maker_id']
        invoice_data_dict['invoice_type_id'] = invoice['invoice_type_id']
        invoice_data_dict['invoice_state_id'] = invoice['invoice_state_id']
        invoice_data_dict['stock_direction_id'] = invoice['stock_direction_id']

        # 更新单据的基本信息
        self.update_invoice_basedata(invoice_data_dict)
        # 批量删除单据原有的明细信息
        add_link = self.del_invoice_detail_data(invoice_id)
        # 批量更新单据的明细信息
        del_link = self.patch_update_invoice_detail_data(invoice_id=invoice_id, m_list=invoice_data_dict['rows'])
        material_base_op = Baseinfo_Op()
        op = MaterialWarehouseInfoOp()
        try:
            # 添加单据操作记录
            material_base_op.add_operate_record(uid=session['user']['id'],
                                                    detail=u"修改销售出库单据",
                                                    id_list=invoice_id,
                                                    is_commit=False,
                                                    db_session=self.controlsession,
                                                    tablename=WarehouseOutSellInvoice.__tablename__)
            self.controlsession.commit()
        except Exception:
            self.controlsession.rollback()
            for key, value in add_link.items():
                for i in range(0, value):
                    op.warehouse_link_status(key)
            for key, value in del_link.items():
                for i in range(0, value):
                    op.delete_warehouse_link(key)
            raise

    def update_invoice_basedata(self, basedata_dict):
        try:
            # 先检测要保存的数据是否是有效的
            self.__save_check_basedata(basedata_dict)
            obj = self.controlsession.query(WarehouseOutSellInvoice).filter(
                WarehouseOutSellInvoice.invoice_number.cast(LargeBinary)==basedata_dict.get("invoice_number")).first()
            obj.invoice_number = basedata_dict.get("invoice_number")
            obj.invoice_date = basedata_dict.get("invoice_date")
            obj.invoice_type_id = basedata_dict.get("invoice_type_id")
            obj.invoice_state_id = basedata_dict.get("invoice_state_id")
            obj.invoice_maker_id = basedata_dict.get("maker_id")
            obj.consignor_id = basedata_dict.get("deliver_handler_id") #发货员
            obj.keeper_id = basedata_dict.get("storeman_id") # 保管员
            obj.salesman_id = basedata_dict.get("salesman_id")
            obj.outwarehouse_type_id = basedata_dict.get("outgoingType_id")
            obj.customer_id = basedata_dict.get("purchaseUnit_id")
            obj.deliver_warehouse_id = basedata_dict.get("warehouse_id")
            obj.inventory_direction_id = basedata_dict.get("stock_direction_id")
            obj.online_store = basedata_dict.get("online_shop")
            obj.department_id = basedata_dict.get("department_id")
            obj.remark = basedata_dict.get("remarks")
            self.controlsession.add(obj)
        except Exception:
            self.controlsession.rollback()
            raise

    def patch_update_invoice_detail_data(self, invoice_id, m_list):
        from control_center.warehouse_manage.warehouse_allocation_manage.control.allocation_op import \
            add_warehouse_id_to_link
        check_type(m_list, (list,), 'm_list')
        op = MaterialWarehouseInfoOp()
        link_dict = {}
        material_dict = {}
        for element in m_list:
            key = str(invoice_id) + str(element['warehouse_id']) + "_" + str(element['material_id'])
            if key in material_dict:
                material_dict[key]['inventory_number'] += element['inventory_number']
            else:
                material_dict[key] = element
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
            self.save_invoice_detail_data(invoice_id,
                                     int(element['material_id']),
                                     int(element['warehouse_id']),
                                     int(element['inventory_number']),
                                    int(element['is_nondefective']))
        return link_dict

    def update_invoice_detail_data(self, invoice_id, material_id, warehouse_id, material_number, is_non_defective):
        check_type(invoice_id, (int, long), 'invoice_id')
        check_type(material_id, (int, long), 'material_id')
        check_type(warehouse_id, (int, long), 'warehouse_id')
        check_type(material_number, (int, long), 'material_number')
        check_type(is_non_defective, (bool,int), 'is_non_defective')

        non_defective = int(is_non_defective)

        obj = WarehouseOutSellDetail(
            invoice_id=invoice_id,
            material_id = material_id,
            material_num=material_number,
            warehouse_id=warehouse_id,
            is_good_material=non_defective
        )
        self.controlsession.add(obj)

    def del_invoice_info_by_invoice_number(self, invoice_number):
        """
        :param invoice_number:  单据单号
        :return: 删除指定单据单号对应的记录
        """
        from control_center.supply_chain.customer_manage.control.customer_mix_op import QueryCustomerInfo
        customer_op = QueryCustomerInfo()
        op = MaterialWarehouseInfoOp()
        commit_flag = False
        assert self.check_invoice_number(invoice_number), \
            "number isn't existed. %s" % invoice_number

        if invoice_number is None:
            raise ValueError("invoice_number can not be None")
        if not isinstance(invoice_number, str):
            raise TypeError("unsupported operand type(s) for function's parameter")
        # 根据单据单号获取该单据单号的ID
        invoice_id = self.get_invoice_id(invoice_number)
        # 根据单据单号获取对应的客户ID
        customer_id = self.get_customer_id(invoice_number)
        # 先删除由外键关联的单据中的物料信息
        add_link = self.del_invoice_detail_data(invoice_id)
        # 然后删除该单据单号对应的基本信息
        self.del_invoice_basedata(invoice_number)
        commit_flag = customer_op.del_customer_links([customer_id], WarehouseOutSellInvoice.__tablename__)
        if not commit_flag:
            raise CodeError(ServiceCode.service_exception, msg=u"客户操作记录提交失败")
        try:
            self.controlsession.commit()
        except Exception:
            self.controlsession.rollback()
            for key, value in add_link.items():
                for i in range(0, value):
                    op.warehouse_link_status(key)
            if commit_flag:
                customer_op.add_customer_links([customer_id], WarehouseOutSellInvoice.__tablename__)


    def del_invoice_basedata(self, invoice_number, is_commit=False):
        """
        :param db_session: 该表对应的数据库session
        :param invoice_number: 其他出库单据单号
        :return:
        """
        try:
            obj = self.controlsession.query(WarehouseOutSellInvoice).filter(
                WarehouseOutSellInvoice.invoice_number.cast(LargeBinary)==invoice_number).first()
            self.controlsession.delete(obj)
            if is_commit:
                self.controlsession.commit()
        except Exception:
            self.controlsession.rollback()
            raise

    def del_invoice_detail_data(self, invoice_id):
        """
        :param db_session: 该表对应的数据库session
        :param invoice_id: 其他出库单据单号ID
        :return:
        """
        from control_center.warehouse_manage.warehouse_allocation_manage.control.allocation_op import \
            add_warehouse_id_to_link
        op = MaterialWarehouseInfoOp()
        objs = self.controlsession.query(WarehouseOutSellDetail).filter(
            WarehouseOutSellDetail.invoice_id==invoice_id).all()
        link_dict = {}
        for obj in objs:
            try:
                op.delete_warehouse_link(obj.warehouse_id)
                link_dict = add_warehouse_id_to_link(obj.warehouse_id, link_dict)
            except Exception:
                for key, value in link_dict.items():
                    for i in range(0, value):
                      op.warehouse_link_status(key)
                raise
            self.controlsession.delete(obj)
        return link_dict

    def commit_invoice_data(self, invoice_number):
        try:
            blue_flag = WarehouseManagementAttr.BLUE_ORDER_DIRECTION
            red_flag = WarehouseManagementAttr.RED_ORDER_DIRECTION
            submit_invoice_state = WarehouseManagementAttr.COMPLETED
            temp_invoice_state = WarehouseManagementAttr.TEMPORARY_STORAGE
            invoice = self.controlsession.query(WarehouseOutSellInvoice).filter_by(invoice_number=invoice_number).first()
            if invoice.invoice_state_id != temp_invoice_state:
                raise CodeError(ServiceCode.service_exception, u'单据状态为已完成的单据不能重复提交')

            invoice.invoice_state_id = submit_invoice_state
            try:
                self.controlsession.add(invoice)
                self.controlsession.commit()
            except Exception:
                self.controlsession.rollback()
                raise

            material_datas = self.get_invoice_materialinfo_by_invoice_id(invoice.id)

            try:
                if invoice.inventory_direction_id == blue_flag:
                    # 出库
                    pub_batch_out_warehouse(invoice_number, material_datas)
                elif invoice.inventory_direction_id == red_flag:
                    # 入库
                    pub_batch_in_warehouse(invoice_number, material_datas)
                else:
                    raise ValueError("invoice_data['stock_direction_id'] must be a value in %s" %
                                     WarehouseManagementAttr.REPERTORY_DIRECTION_TYPE.keys())
            except Exception:
                invoice.invoice_state_id = temp_invoice_state
                self.controlsession.add(invoice)
                self.controlsession.commit()
                raise
        except Exception:
            from public.logger.syslog import SystemLog
            raise
        return True

    def __save_check_basedata(self, m_dict):
        from data_mode.erp_supply.base_op.warehouse_manage_op.warehouse_op import WarehouseManageBaseOp
        base_op = WarehouseManageBaseOp()

        all_user_list = [
            m_dict.get('maker_id'),
            m_dict.get('salesman_id'),
            m_dict.get('storeman_id'),
            m_dict.get('deliver_handler_id')]
        useful_user_list = list(filter(is_None, all_user_list))

        all_department_id = [m_dict.get('department_id')]
        useful_department_list = list(filter(is_None, all_department_id))

        all_warehouse_id = [m_dict.get('warehouse_id')]
        useful_warehouse_list = list(filter(is_None, all_warehouse_id))

        all_customer_id = [m_dict.get('purchaseUnit_id')]
        useful_customer_list = list(filter(is_None, all_customer_id))

        assert base_op.check_user_exist(useful_user_list), "person error:%s not exist" % useful_user_list
        assert base_op.check_department_exist(useful_department_list), \
            "department error:%s not exist" % useful_department_list
        assert base_op.check_warehouse_id(useful_warehouse_list), \
            "warehouse error:%s not exist" % useful_warehouse_list
        assert base_op.check_customer_id(useful_customer_list), "customer error:%s not exist" % useful_customer_list
        assert base_op.check_sell_invoice_type(m_dict.get('invoice_type_id')), \
            "invoice type error: %s is wrong for the invoice" % m_dict.get('invoice_type_id')
        assert base_op.check_sell_out_type(m_dict.get('outgoingType_id')), \
            "warehouse out type error: %s does not exist in the %s" % (m_dict.get('outgoingType_id'),
                                                                       WarehouseManagementAttr.SELL_OUTWAREHOUSE_TYPE.keys())
        assert base_op.check_invoice_state(m_dict.get('invoice_state_id')), \
            "invoice state error: %s does not exist in the %s" % (m_dict.get('invoice_state_id'),
                                                                  WarehouseManagementAttr.INVOICE_STATE.keys())
        assert base_op.check_red_bule_flag_exist(m_dict.get('stock_direction_id')), \
            "stock direction error: %s does not exist in the %s" % (m_dict.get('stock_direction_id'),
                                                                    WarehouseManagementAttr.REPERTORY_DIRECTION_TYPE.keys())

    def __save_check_detail(self, material_list):
        from data_mode.erp_supply.base_op.warehouse_manage_op.warehouse_op import WarehouseManageBaseOp
        base_op = WarehouseManageBaseOp()

        check_type(material_list, list, 'material_list')
        material_id_list =[]
        for element in material_list:
            material_id_list.append(int(element.get('material_id')))

        assert base_op.check_material_id(material_id_list), "material error: %s not exist" % material_id_list
