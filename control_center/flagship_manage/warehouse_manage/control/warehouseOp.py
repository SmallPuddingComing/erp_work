#-*- coding:utf-8 –*-

import json
from sqlalchemy import func
import time
import traceback
from sqlalchemy.sql import text
from sqlalchemy import func, distinct,and_
from data_mode.hola_flagship_store.control_base.controlBase import ControlEngine
from data_mode.hola_flagship_store.mode.warehouse_mode.warehouse_manage import WarehouseType, Inventory, ProductRelation
from control_center.shop_manage.good_info_manage.control.mixOp import HolaWareHouse


class WarehouseOp(ControlEngine):
    def __init__(self):
        ControlEngine.__init__(self)

    def get_WH_total_info(self, store_id):
        # 需要考虑分页
        iw = InWarehouseOp()
        prdt_list = iw.get_productlist_by_store_id(store_id)

        wt = WarehouseTypeOp()
        w_types = wt.get_all_warehouse_type()
        info_list = []
        for product_id in prdt_list:
            # 根据商品id 获取商品信息
            base = HolaWareHouse()
            info = {}
            info["product_id"] = product_id
            info["product_details"] = base.get_product_info(product_id)

            # 根据商品id 和 库存信息获取商品库存数
            info["warehouse"] = []
            for type in w_types:
                dct = {}
                # tmp = self.controlsession.query(WareHouse).filter_by(store_id = store_id, product_id = product_id, warehouse_id = type.get("id")).first()
                tmp = self.controlsession.query(Inventory).filter(Inventory.store_id == store_id, Inventory.good_id == product_id, Inventory.warehouse_type_id == type.get("id")).first()
                dct["id"] = type.get('id')
                dct["name"] = type.get('name')
                dct["num"] = tmp.to_json().get("num") if tmp else 0
                info["warehouse"].append(dct)
            # 获取商品今日入库数
            # iwh = InWarehouseOp()
            # info["today_in_nums"] = iwh.get_todays_in_nums(store_id, product_id)
            # 获取商品今日出库数
            # info["today_out_nums"] = iwh.get_todays_out_nums(store_id, product_id)
            info["today_in_nums"] = ""
            info["today_out_nums"] = ""
            info_list.append(info)

        return json.dumps(info_list)

            
class WarehouseTypeOp(ControlEngine):
    def __init__(self):
        ControlEngine.__init__(self)

    def get_all_warehouse_type(self):
        rs = self.controlsession.query(WarehouseType).all()
        rs = [item.to_json()for item in rs]
        return rs

class InWarehouseOp(ControlEngine):
    def __init__(self):
        ControlEngine.__init__(self)

    def get_productlist_by_store_id(self, store_id):
        rs = self.controlsession.query(distinct(ProductRelation.good_id)).all()
        rs = [int(item[0]) for item in rs]
        return rs
