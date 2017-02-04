#!/usr/bin/python
# -*- coding:utf-8 -*-
#    Copyright(c) 2015-2016 JmGo Company
#    All rights reserved.
#
#    文件名 : warehouse_stock_mix_op.py
#    作者   : DengLiming
#  电子邮箱 : lmdeng@jmgo.com
#    日期   : 2017/1/12 16:16
#
#     描述  :
#
from sqlalchemy import and_,or_,func
from data_mode.erp_supply.control_base.controlBase import ControlEngine
from data_mode.erp_supply.mode.material_manage_mode.warehouse_inventory import WarehouseInventory, InventoryRecord
from control_center.supply_chain.material_warehosue.control.material_warehouse_mix_op import GetWarehouseInfo
from data_mode.erp_supply.base_op.material_op.baseinfo_op import Baseinfo_Op
import traceback

class GetWarehouseInventoryInfo(ControlEngine):
    def get_warehouse_inventoty_info(self, start=0, page_size=10, material_name=None, material_code=None,
                                     warehouse_id=None, **kw):
        """
        :param start: 当前页码
        :param page_size:分页大小
        :param material_name:物料名称
        :param material_code:物料编码
        :param kw: 目前只支持仓库名称/仓库类型 做搜索
        :return:
        """
        try:
            data = list()
            total = 0
            wh_op = GetWarehouseInfo()
            material_op = Baseinfo_Op()
            condition = ''
            material_id_list = list()
            if material_name:
                m_res = material_op.get_base_info_by_name(m_name=material_name)
                if len(m_res[1]) == 0:
                    return total, data
                if m_res[0] and len(m_res[1]) > 0:
                    for item in m_res[1]:
                        material_id_list.append(item['id'])
                condition = "WarehouseInventory.operation_id.in_(%s)" % material_id_list
            if material_code:
                m_res = material_op.get_base_info_by_name(m_code=material_code)
                if len(m_res[1]) == 0:
                    return total, data
                if m_res[0] and len(m_res[1]) > 0:
                    for item in m_res[1]:
                        material_id_list.append(item['id'])

                condition = "WarehouseInventory.operation_id.in_(%s)" % material_id_list
            if warehouse_id:
                if condition is not '':
                    condition = condition +",WarehouseInventory.warehouse_id == %d" % warehouse_id
                else:
                    condition = "WarehouseInventory.warehouse_id == %d" % warehouse_id

            condition = "and_("+condition+")"
            res = self.controlsession.query(WarehouseInventory).filter(eval(condition)).limit(page_size).offset(start).all()
            total = self.controlsession.query(func.count(WarehouseInventory.id)).filter(eval(condition)).scalar()
            if res:
                res = [item.to_json() for item in res]
                for item in res:
                    item['warehouse_name'] = wh_op.get_warehouse_id_info(item['warehouse_id'])['warehouse_name']
                    res_warehouse_type_id = wh_op.get_warehouse_id_info(item['warehouse_id'])['warehouse_type_id']
                    item['warehouse_type'] = wh_op.get_warehouse_type_id(res_warehouse_type_id)['warehouse_type_name']
                    # material_infos = material_op.get_baseinfo_by_id(item['id'])  # 获取该仓库内的所有物料信息
                    material_infos = material_op.get_baseinfo_by_id(item['operation_id'])  # 获取该物料的信息
                    if material_infos[0] != 0:
                        raise ValueError(u'数据表erp_supply.warehouse_inventory中operation_id为%s，'
                                         u'warehouse_id为%s的记录有问题' % (item['operation_id'],
                                                                     item['warehouse_id']))
                    item['basicUnit_name'] = material_infos[1]['measureunit']
                    item['materiel_code'] = material_infos[1]['code']
                    item['materiel_name'] = material_infos[1]['name']
                    item['specification_mode'] = material_infos[1]['specifications']
                    item['stock_number'] = item['inventory_number']
                    data.append(item)
            else:
                pass
            return total, data
        except Exception:
            print traceback.format_exc()
            raise
if __name__ == "__main__":
    op = GetWarehouseInventoryInfo()
    # op.get_warehouse_inventoty_info()