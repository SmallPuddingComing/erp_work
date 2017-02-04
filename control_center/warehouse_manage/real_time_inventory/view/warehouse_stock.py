#!/usr/bin/python
# -*- coding:utf-8 -*-
#    Copyright(c) 2015-2016 JmGo Company
#    All rights reserved.
#
#    文件名 : warehouse_stock.py
#    作者   : DengLiming
#  电子邮箱 : lmdeng@jmgo.com
#    日期   : 2017/1/4 10:25
#
#     描述  :
#
from public.function import tools
from flask.views import MethodView
from control_center.warehouse_manage import warehouse_manage, warehouse_manage_prefix
from control_center.admin import add_url
import traceback
from public.exception.custom_exception import CodeError
from public.logger.syslog import SystemLog
from flask import json, request
from control_center.warehouse_manage.real_time_inventory.control.warehouse_stock_op import WarehouseInventoryOp
from control_center.warehouse_manage.real_time_inventory.control.warehouse_stock_mix_op import GetWarehouseInventoryInfo
from config.service_config.returncode import ServiceCode


class StockQuery(MethodView):
    """
     库存查询
    """
    @staticmethod
    def get():
        return ""


class StockInfo(MethodView):
    @staticmethod
    def get():
        return_data = None
        try:
            w_op = WarehouseInventoryOp()
            res = w_op.get_warehouse_info()
            # result = {'total': res[0], 'warehouse_type_list': res[2], 'stock_list': res[1], 'msg': u'查询成功', 'code': ServiceCode.success}
            # return tools.en_render_template('warehouseManagement/inventory_search/realTimeInventory.html', result=json.dumps(result) )
        except CodeError as e:
            return_data = e.json_value()
        except Exception:
            SystemLog.pub_warninglog(traceback.format_exc())
            return_data = {'code': ServiceCode.service_exception, 'msg': u'服务器错误'}
        else:
            return_data = {
                'total': res[0],
                'warehouse_type_list': res[2],
                'stock_list': res[1],
                'msg': u'查询成功',
                'code': ServiceCode.success}

        finally:
            return tools.en_render_template('warehouseManagement/inventory_search/realTimeInventory.html',
                                            result=json.dumps(return_data) )



class SearchStockInfo(MethodView):
    @staticmethod
    def post():
        return_data = None
        try:
            page_number = request.values.get('page_number', 1, int)
            warehouse_id = request.values.get('warehouse_id', 0, int)
            materiel_name = request.values.get('materiel_name', '')
            materiel_code = request.values.get('materiel_code', '')
            page_size = request.values.get('page_size', 10, int)
            start = (page_number-1)*page_size
            w_op = GetWarehouseInventoryInfo()
            res = w_op.get_warehouse_inventoty_info(start=start,
                                                    page_size=page_size,
                                                    material_name=materiel_name,
                                                    material_code=materiel_code,
                                                    warehouse_id=warehouse_id)
            if res[1]:
                result = {'code': ServiceCode.success, 'total': res[0], 'stock_list': res[1]}
            else:
                result = {'code': ServiceCode.success, 'total': 0, 'stock_list': []}
            # return tools.en_return_data(json.dumps(result))
        except CodeError as e:
            return_data = e.json_value()
        except Exception:
            SystemLog.pub_warninglog(traceback.format_exc())
            return_data = {'code': ServiceCode.service_exception, 'msg': u'服务器错误'}
        else:
            return_data = result
        finally:
            return tools.en_return_data(json.dumps(return_data))

add_url.add_url(u'库存查询',
                'warehouse_manage.index',
                add_url.TYPE_ENTRY,
                warehouse_manage_prefix,
                warehouse_manage,
                '/stock_info/',
                'query_stock',
                StockQuery.as_view('query_stock'),
                70,
                methods=['GET'])

add_url.add_url(u'即时库存查询',
                'warehouse_manage.query_stock',
                add_url.TYPE_ENTRY,
                warehouse_manage_prefix,
                warehouse_manage,
                '/current_stock_info/',
                'StockInfo',
                StockInfo.as_view('StockInfo'),
                methods=['GET', 'POST'])

add_url.add_url(u'库存搜索',
                'warehouse_manage.StockInfo',
                add_url.TYPE_FUNC,
                warehouse_manage_prefix,
                warehouse_manage,
                '/search_stock_info/',
                'SearchStockInfo',
                SearchStockInfo.as_view('SearchStockInfo'),
                methods=['GET', 'POST'])

