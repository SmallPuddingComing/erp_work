#-*- coding:utf-8 –*-


import datetime
import json
import traceback
from control_center.flagship_manage.flagship_info_manage.control.flagship_op import FlagShipOp
from flask import jsonify, request
from flask.views import MethodView

from config.logistics_config.logistics import logisticsConfig
from config.service_config.returncode import ServiceCode
from control_center.flagship_manage.warehouse_manage.control.in_out_warehouse_op import InOutWarehouseOp
from control_center.flagship_manage.warehouse_manage.control.ship_in_warehouse_op import ShipInwarehouse
from data_mode.hola_flagship_store.mode.warehouse_mode.warehouse_manage import OperateType, WarehouseType
from public.function import tools

from control_center.admin import add_url
from control_center.flagship_manage import flagship_manage,flagship_manage_prefix


class CreateOutOrderForm(MethodView):
    '''
    制作入库单
    '''
    def get(self):
        return_data = {'code' : ServiceCode.service_exception}
        op = InOutWarehouseOp()
        try:
            store_id = request.values.get('flagshipid','')
            #首先生成临时订单号
            #默认操作类型为 销售出库
            operate_type = OperateType.sale_out
            rs = InOutWarehouseOp.CreateNumber(store_id,operate_type)
            number = rs['number']
            date = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')



            #获取旗舰店名字
            op_flagship =FlagShipOp()
            rs = op_flagship.get_flagship_info_by_flagship_id(store_id)
            send_site = rs['name']
            #操作类型
            out_type_list = []
            rs_operate = op.GetInOutWarehouseType()
            out_type_list.append(rs_operate[2])
            out_type_list.append(rs_operate[3])
            #物流
            logisticsType=logisticsConfig()
            logisticsList= logisticsType.logistics_get_xml()

            #仓库类型
            op_ship = ShipInwarehouse()
            rs_warehousetype_list = op_ship.GetWarehouseType()

            if rs['id']:
                id = rs['id']
                return_data = {
                    'code' : ServiceCode.success,
                    'number': number,
                    'date' : date,
                    'id' : id,
                    'send_site' :  send_site,
                    'out_type_list' : out_type_list,
                    'logistics_company_list' :logisticsList,
                    'warehousetype_list' : rs_warehousetype_list

                }
            else:
                return_data = {'code' : ServiceCode.service_exception}

        except Exception,e:
            print traceback.format_exc()
            return_data = {'code' : ServiceCode.service_exception}

        return tools.en_render_template('/storeManage/warehouse/delivery_order.html',result = json.dumps(return_data))
class QueryWhouse(MethodView):
    '''
    商品出库页面搜索接口
    '''
    def get(self):
        return_data = {'code' : ServiceCode.service_exception}
        page_num = request.values.get('page_num',1,int)
        per_page = request.values.get('per_page',10,int)
        operate_type_id = request.values.get('operate_type_id',0,int)
        start_time = request.values.get('start_time',None,str)
        end_time = request.values.get('end_time',None,str)
        flagshipid=request.values.get('flagshipid','',int)

        try:
            page = page_num - 1
            if page < 0:
                page = 0
            if per_page > 60:
                per_page = 60
            start = page *per_page
            op  = InOutWarehouseOp()

            #operate_type_id 为 0 的话表示查询全部出库类型
            if operate_type_id == 0:
                if start_time == '' and end_time == '' :
                    rs,total = op.GetOutWarehouseList_1(start,per_page,flagshipid=flagshipid)
                else:
                    rs,total = op.GetOutWarehouseList_1(start,per_page,start_time = start_time,end_time = end_time,flagshipid=flagshipid)
            else:
                if start_time =='' and end_time == '':
                    rs,total = op.GetOutWarehouseList_1(start,per_page,operate_type=operate_type_id,flagshipid=flagshipid)
                else:
                    rs,total = op.GetOutWarehouseList_1(start,per_page,operate_type=operate_type_id,start_time = start_time,end_time = end_time,flagshipid=flagshipid)


            return_data = {
                'code' : ServiceCode.success,
                'order_list' : rs,
                'total' : total
            }
            pass
        except Exception,e:
            print traceback.format_exc()
            return_data = {'code' : ServiceCode.service_exception}

        return tools.en_return_data(json.dumps(return_data))

class OutWhouse(MethodView):
    '''
    进入商品出库页面
    '''
    def get(self):
        return_data = {'code' : ServiceCode.service_exception}
        page_num = request.values.get('page_num',1,int)
        per_page = request.values.get('per_page',10,int)
        flagshipid = request.values.get('flagshipid','',int)
        try:
            page = page_num - 1
            if page < 0:
                page = 0
            if per_page > 60:
                per_page = 60
            start = page *per_page
            op  = InOutWarehouseOp()
            rs,total = op.GetOutWarehouseList_1(start,per_page,flagshipid=flagshipid)
            rs_warehousetype = op.GetInOutWarehouseType()
            operate_list = []
            operate_list.append(rs_warehousetype[2])
            operate_list.append(rs_warehousetype[3])
            return_data = {
                'code' : ServiceCode.success,
                'order_list' : rs,
                'total' : total,
                'operate_list' : operate_list
            }
            pass
        except Exception,e:
            print traceback.format_exc()
            return_data = {'code' : ServiceCode.service_exception}

        return tools.en_render_template('/storeManage/warehouse/warehouse_delivery.html',result = json.dumps(return_data))

class QueryGoodinfo(MethodView):
    '''
    点击选择商品
    查询商品库存信息
    '''
    def get(self):
        return_data = {'code':ServiceCode.service_exception}
        try:
            page_num = request.values.get('page_num', 0, type=int)
            per_page = request.values.get('per_page', 0, type=int)
            name = request.values.get('name', None, type=str)
            code = request.values.get('code', None, type=str)
            bar_code = request.values.get('bar_code', None, type=str)
            warehouse_type_id = request.values.get('warehouse_type_id',WarehouseType.inventory_warehouse,int)
            flagshipid = request.values.get('flagshipid','')

            if name is '':
                name = None
            if code is '':
                code = None
            if bar_code is '':
                bar_code = None
            page = page_num - 1
            if page < 0:
                page = 0
            if per_page > 60:
                per_page = 60
            start = page *per_page


            op  = InOutWarehouseOp()
            rs = op.QueryInventory(start,per_page,warehouse_type_id,flagshipid,name,code,bar_code)
            return_data = rs

        except Exception,e:
            print traceback.format_exc()
            return_data = {'code':ServiceCode.service_exception}

        return tools.en_return_data( json.dumps(return_data))

class Inventory_count(MethodView):
    '''
    查询库存量
    '''
    def get(self):
        return_data = {'code' : ServiceCode.service_exception}
        try:

            store_id = request.values.get('flagshipid','')
            good_id = request.values.get('good_id','')
            warehouse_type_id = request.values.get('warehouse_type_id',WarehouseType.inventory_warehouse,int)

            #获取库存量
            op = InOutWarehouseOp()
            rs = op.InventoryCountInfo(store_id,warehouse_type_id,good_id)
            rs_is_serial_number = op.CheckIsSerialNumber(good_id,warehouse_type_id,store_id)
            return_data = {
                'code' : ServiceCode.success,
                'inventory_count': rs,
                'is_serialnumber' : rs_is_serial_number
            }


        except Exception,e:
            print traceback.format_exc()
            return_data = {'code' : ServiceCode.service_exception}

        return tools.en_return_data(json.dumps(return_data))

import re
class SaveOutOrder(MethodView):
    '''
    提交数据接口
    '''
    def post(self):

        return_data = {'code':ServiceCode.service_exception}
        op = InOutWarehouseOp()
        try:
            start_time = datetime.datetime.now()
            info_dict = {}
            info_dict['number'] = request.values.get('number','')
            info_dict['user'] = request.values.get('user','')
            info_dict['date'] = request.values.get('date','')
            info_dict['operate_type'] = request.values.get('operate_type',OperateType.sale_out,int)
            info_dict['warehouse_type_id'] = request.values.get('warehouse_type_id',WarehouseType.inventory_warehouse,int)

            info_dict['send_site'] = request.values.get('send_site','')
            info_dict['recv_site'] = request.values.get('recv_site','')
            info_dict['remark_info'] = request.values.get('remark_info','')
            info_dict['flagshipid'] = request.values.get('flagship_id','')
            info_dict['logistics_name'] = request.values.get('logistics_name','')
            info_dict['all_amount'] = request.values.get('in_out_number',0,int)
            info_dict['product_id'] = request.values.get('product_id','')
            code_list = request.values.get('code_list','')
            code_list = json.loads(code_list)
            info_dict['code_list'] = code_list
            # rs = op.SaveDataInfo(info_dict)

            #2016-10-25  修改
            good_list = []
            for item in code_list:
                good_dict = {}
                good_dict["good_id"] = info_dict['product_id']
                good_dict["serial_number"] = item
                good_dict["count"] = 1
                good_list.append(good_dict)
            info_dict["good_list"] = good_list
            info_dict["to_warehouse_type_id"] = WarehouseType.out_warehouse

            print '-------------------SaveOutOrder---------------------------',code_list

            rs = op.create_number(info_dict)
            return_data = rs



        except Exception,e:
            print traceback.format_exc()
            return_data = {'code':ServiceCode.service_exception}

        end_time = datetime.datetime.now()
        rs = end_time - start_time
        ra = rs.seconds*1000 + rs.microseconds/1000
        print '------------运行时间----------------',ra
        return tools.en_return_data(jsonify(return_data))
class QueryOutOrderInfo(MethodView):
    def get(self):
        '''
        查询出库明细
        :return:
        '''
        return_data = {'code' : ServiceCode.service_exception}
        try:
            out_number = request.values.get('number','')
            flagship_id = request.values.get('flagshipid','')
            op = ShipInwarehouse()
            rs = op.GetWarehouseDetailed(out_number,flagship_id)

            return_data = rs
        except Exception,e:
            print traceback.format_exc()
            return_data = {'code' : ServiceCode.service_exception}

        return tools.flagship_render_template('storeManage/warehouse/transfer_detail.html',result = json.dumps(return_data))


class OutCheckSerialNumber(MethodView):
    def get(self):
        return_data = {'code' : ServiceCode.service_exception}
        try:
            flagship_id = request.values.get('flagshipid','')
            warehousetype_id = request.values.get('warehousetype_id',WarehouseType.inventory_warehouse,int)
            good_id = request.values.get('good_id','')
            serial_number = request.values.get('serial_number','')
            op_ship = ShipInwarehouse()

            rs_ship = op_ship.CheckSpace(serial_number)
            if not rs_ship:
                return_data = {
                    'code' : ServiceCode.service_exception,
                    'msg' : '序列号不匹配'
                }

            op = InOutWarehouseOp()
            rs = op.CheckSerialNumber(serial_number,flagship_id,good_id,warehousetype_id)
            return_data = rs


        except Exception,e:
            print traceback.format_exc()
            return_data = {'code' : ServiceCode.service_exception}
        return tools.en_return_data(json.dumps(return_data))



add_url.flagship_add_url(u"商品出库", "flagship_manage.WarehouseMgt", add_url.TYPE_ENTRY, flagship_manage_prefix,
                flagship_manage, '/warehouse/outwhouse/', 'OutWhouse', OutWhouse.as_view('OutWhouse'), 90,methods=['GET'])

add_url.flagship_add_url(u"制作出库单", "flagship_manage.OutWhouse", add_url.TYPE_FEATURE, flagship_manage_prefix,
                flagship_manage, '/warehouse/createoutform/', 'CreateOutOrderForm', CreateOutOrderForm.as_view('CreateOutOrderForm'), methods=['GET'])


add_url.flagship_add_url(u"选择商品", "flagship_manage.CreateOutOrderForm", add_url.TYPE_FEATURE, flagship_manage_prefix,
                flagship_manage, '/warehouse/select_good/', 'QueryGoodinfo', QueryGoodinfo.as_view('QueryGoodinfo'), methods=['GET'])

add_url.flagship_add_url(u"获取库存量", "flagship_manage.QueryGoodinfo", add_url.TYPE_FEATURE, flagship_manage_prefix,
                flagship_manage, '/warehouse/inventory_count/', 'Inventory_count', Inventory_count.as_view('Inventory_count'), methods=['GET'])

add_url.flagship_add_url(u"保存出库信息", "flagship_manage.CreateOutOrderForm", add_url.TYPE_FEATURE, flagship_manage_prefix,
                flagship_manage, '/warehouse/SaveOutOrder/', 'SaveOutOrder', SaveOutOrder.as_view('SaveOutOrder'), methods=['POST','GET'])

add_url.flagship_add_url(u"商品出库页面搜索", "flagship_manage.OutWhouse", add_url.TYPE_FEATURE, flagship_manage_prefix,
                flagship_manage, '/warehouse/QueryWhouse/', 'QueryWhouse', QueryWhouse.as_view('CreateOutOrderForm'), methods=['GET'])

add_url.flagship_add_url(u"商品出库明细", "flagship_manage.OutWhouse", add_url.TYPE_FEATURE, flagship_manage_prefix,
                flagship_manage, '/warehouse/QueryOutOrderInfo/', 'QueryOutOrderInfo', QueryOutOrderInfo.as_view('QueryOutOrderInfo'), methods=['GET'])
add_url.flagship_add_url(u"检查序列号", "flagship_manage.CreateOutOrderForm", add_url.TYPE_FEATURE, flagship_manage_prefix,
                flagship_manage, '/warehouse/OutCheckSerialNumber/', 'OutCheckSerialNumber', OutCheckSerialNumber.as_view('OutCheckSerialNumber'), methods=['GET'])


