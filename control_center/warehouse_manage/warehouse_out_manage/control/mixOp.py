#!/usr/bin/python
# -*- coding:utf-8 -*-
#    Copyright(c) 2015-2016 JmGo Company
#    All rights reserved.
#
#    文件名 : mixOp.py
#    作者   : ChengQian
#  电子邮箱 : qcheng@jmgo.com
#    日期   : 2017/1/12 15:18
#
#     描述  :
#
from sqlalchemy import cast, LargeBinary
from public.logger.syslog import SystemLog
import traceback
from public.function.tools import check_type
from data_mode.erp_supply.mode.material_repertory_model.warehouseout_other_invoice import WarehouseOutOtherInvoice
from data_mode.erp_supply.mode.material_repertory_model.warehouseout_other_detail import WarehouseOutOtherDetail
from data_mode.erp_supply.mode.material_repertory_model.warehouseout_outsourcing_invoice import WarehouseOutOutsourcingInvoice
from data_mode.erp_supply.mode.material_repertory_model.warehouseout_outsourcing_detail import WarehouseOutOutsourcingDetail
from data_mode.erp_supply.mode.material_repertory_model.warehouse_out_sell_invoice import WarehouseOutSellInvoice
from data_mode.erp_supply.mode.material_repertory_model.warehouse_out_sell_detail import WarehouseOutSellDetail

def select_material():
    from data_mode.erp_supply.base_op.material_op.baseinfo_op import Baseinfo_Op
    baseinfo_op = Baseinfo_Op()
    total, full_material_datas = baseinfo_op.get_all_material_info()
    material_list = []
    for data in full_material_datas:
        temp_dict = {}
        temp_dict['material_id'] = data.get("material_id")
        temp_dict['material_code'] = data.get("material_code")
        temp_dict['material_name'] = data.get("material_name")
        temp_dict['specification_model'] = data.get("specification_model")
        temp_dict['unit'] = data.get("unit")
        temp_dict['base_attr'] = data.get("base_attr")
        temp_dict['base_attr_type'] = data.get("base_attr_type")
        material_list.append(temp_dict)
    return total, material_list

def select_customer():
    from control_center.supply_chain.customer_manage.control.customer_mix_op import QueryCustomerInfo
    customer_op = QueryCustomerInfo()
    total, customer_datas = customer_op.get_customer_info_all()
    customer_datas_list = []
    for data in customer_datas:
        temp_dict = {}
        temp_dict['customer_id'] = data.get("id")
        temp_dict['customer_name'] = data.get("customer_name")
        temp_dict['prov'] = data.get("province")
        temp_dict['city'] = data.get("city")
        temp_dict['region'] = data.get("county")
        temp_dict['contacts'] = data.get("contacts")
        temp_dict['contact_information'] = data.get("telephone")
        customer_datas_list.append(temp_dict)
    return total, customer_datas_list

def select_supplier():
    from control_center.supply_chain.supplier_manage.control.supplier_baseinfo_op import SupplierBaseInfoOp
    supplier_op = SupplierBaseInfoOp()
    total, supplier_datas = supplier_op.get_all_supplier_baseinfo()
    supplier_datas_list = []
    for data in supplier_datas:
        temp_dict = {}
        contact_info = supplier_op.get_supplier_contact_info(data.get("supplier_id"))
        temp_dict['supplier_id'] = data.get("supplier_id")
        temp_dict['supplier_code'] = data.get("supplier_code")
        temp_dict['supplier_name'] = data.get("supplier_name")
        contacts = contact_info.get("contacts")
        contacts_info = contact_info.get("contact_information")
        temp_dict['contacts'] = contacts if contacts is not None else ""
        temp_dict['contact_information'] = contacts_info if contacts_info is not None else ""
        supplier_datas_list.append(temp_dict)
    return total, supplier_datas_list

