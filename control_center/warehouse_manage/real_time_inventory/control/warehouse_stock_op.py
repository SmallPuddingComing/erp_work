#!/usr/bin/python
# -*- coding:utf-8 -*-
#    Copyright(c) 2015-2016 JmGo Company
#    All rights reserved.
#
#    文件名 : warehouse_stock_model.py
#    作者   : DengLiming
#  电子邮箱 : lmdeng@jmgo.com
#    日期   : 2017/1/11 10:25
#
#     描述  :
#
from sqlalchemy import and_, func
import traceback
from config.service_config.returncode import ServiceCode
from data_mode.erp_supply.control_base.controlBase import ControlEngine
from data_mode.erp_supply.mode.material_manage_mode.warehouse_inventory import WarehouseInventory, InventoryRecord
from public.logger.syslog import SystemLog
from control_center.supply_chain.material_warehosue.control.material_warehouse_mix_op import GetWarehouseInfo
from control_center.warehouse_manage.real_time_inventory.control.warehouse_stock_mix_op import GetWarehouseInventoryInfo


class WarehouseInventoryOp(ControlEngine):
    def get_warehouse_info(self, page_size=None, page_number=None):
        try:
            wh_op = GetWarehouseInfo()
            res = wh_op.get_warehouse_list()
            inventory_op = GetWarehouseInventoryInfo()
            inventory_list = inventory_op.get_warehouse_inventoty_info()
            warehouse_type_list = list()
            stock_list = list()
            total = 0
            if res[0]:
                for item in res[0]:
                    pass
                    # item['warehouse_type_name'] = wh_op.get_warehouse_type_id(item['pid'])['warehouse_type_name']
                warehouse_type_list = res[0]
            if inventory_list[1]:
                stock_list = inventory_list[1]
                total = inventory_list[0]
            return total, stock_list, warehouse_type_list
        except Exception:
            # SystemLog.pub_warninglog(traceback.format_exc())
            print traceback.format_exc()
            raise Exception(u'库存查询失败')

if __name__=="__main__":
    wh = WarehouseInventoryOp()
    # print wh.get_warehouse_info()