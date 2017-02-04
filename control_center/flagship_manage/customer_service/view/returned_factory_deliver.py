#/usr/bin/python
#-*- ucoding:utf-8 -*-

from control_center.flagship_manage import flagship_manage, flagship_manage_prefix
from control_center.admin import add_url
from flask import session
from operator import itemgetter
from itertools import groupby
from flask.views import MethodView
from flask import render_template, current_app, request, url_for
from flask import jsonify
from flask import json
from pprint import pprint
from public.function import tools

import traceback
from config.service_config.returncode import ServiceCode
from public.exception.custom_exception import CodeError
from data_mode.hola_flagship_store.base_op.returned_factory_deliver_op import ReturnedFactoryDeliverOp
from control_center.flagship_manage.customer_service.control.returned_factory_op import ReturnedFactory
from control_center.flagship_manage.warehouse_manage.control.in_out_warehouse_op import InOutWarehouseOp
from data_mode.hola_flagship_store.mode.warehouse_mode.warehouse_manage import *
from config.share.share_define import FC_RECEIPTS
from control_center.flagship_manage.customer_service.control.after_sale_operate import AfterSaleOp



class ReturnedFactoryDeliver(MethodView):
    """
    售后服务返厂发货页面渲染及该页面的搜索及分页功能接口
    """
    def get(self):
        return_data = None
        datas = {}
        try:
            returned_op = ReturnedFactoryDeliverOp()

            flag = request.values.get('flag', 1, int)
            flagshipid = request.values.get('flagshipid', 0,int)
            starttime = request.values.get('starttime','', str)
            stoptime = request.values.get('stoptime','',str)
            page = request.values.get('page',1,int)
            pagenum = request.values.get('pagenum',10,int)

            datalist, total = returned_op.get_all_returnedfactory_info(flagshipid,starttime,stoptime,page,pagenum)

        except CodeError as e:
            return_data = json.dumps(e.json_value())
        except Exception as e:
            print traceback.format_exc(e)
            return_data = json.dumps(
                {'code': ServiceCode.service_exception, 'msg': u"服务器失败"})
        else:
            datas['code'] = ServiceCode.success
            datas['total'] = total
            datas['rows'] = datalist
            return_data = json.dumps(datas)
        finally:
            if flag:
                return tools.flagship_render_template("afterSales/backFactoryShip.html",result=return_data)
            else:
                return tools.en_return_data(return_data)


class DetailOfReturnedFactory(MethodView):
    """
    售后服务返厂发货页面返厂单号对应的明细功能接口
    """
    def get(self):
        return_data = None
        try:
            flag = request.values.get('flag',1,int)
            flagshipid = request.values.get('flagshipid',0, int)      #旗舰店id
            number = request.values.get('number','', str)           #返厂单号
            page = request.values.get('page',1, int)
            pagenum = request.values.get('pagenum',10, int)

            returned_op = ReturnedFactoryDeliverOp()

            datas = returned_op.get_detail_of_number(flagshipid,number,page,pagenum)

        except CodeError as e:
            return_data = json.dumps(e.json_value())
        except Exception as e:
            print traceback.format_exc(e)
            return_data = json.dumps(
                {'code': ServiceCode.service_exception, 'msg': u"服务器失败"})
        else:
            datas['code'] = ServiceCode.success
            return_data = json.dumps(datas)
        finally:
            if flag:
                return tools.flagship_render_template("afterSales/factoryDetail.html", result=return_data)
            else:
                return tools.en_return_data(return_data)



class CreateFcOrder(MethodView):
    '''
    制作返厂单
    '''
    def get(self):
        return_data = None
        r_data = {}
        try:
            flagship_id = request.values.get("flagshipid","")
            user_id = session['user']['id']

            op = ReturnedFactory()
            r_data = op.create_order_info(flagship_id,user_id)

        except CodeError as e:
            return_data = json.dumps(e.json_value())
        except Exception as e:
            print traceback.format_exc()
            return_data = json.dumps(
                {'code': ServiceCode.service_exception, 'msg': u"服务器失败",'rows': r_data})
        else:
            return_data = json.dumps(
                {'code': ServiceCode.success, 'msg': u"服务器成功",'rows': r_data})
        finally:
            return tools.en_render_template("afterSales/factoryOrder.html",result =return_data)


class QueryFcProduct(MethodView):
    '''
    选择返厂商品
    '''
    def post(self):
        return_data = None
        r_data = {}
        data_dict = {}
        try:
            data_dict['per_page'] = request.values.get("per_page","",type=int)
            data_dict['page_num'] = request.values.get("page_num",'',type=int)
            data_dict['flagship_id'] = request.values.get("flagshipid",None,type=int)
            data_dict['value_type'] = request.values.get("value_type",None,type=int)
            if data_dict["value_type"] is u"":
                data_dict["value_type"] = None
            data_dict['value'] = request.values.get("value",None)
            if data_dict["value"] is u"":
                data_dict["value"] = None
            data_dict['fc_reason'] = request.values.get("fc_reason",None,type=int)
            if data_dict["fc_reason"] is u"":
                data_dict["fc_reason"] = None

            data_dict['f_state'] = False  #表示待返厂

            op = ReturnedFactory()
            r_data = op.query_fc_product_info(data_dict)

        except CodeError as e:
            return_data = json.dumps(e.json_value())
        except Exception as e:
            print traceback.format_exc()
            return_data = json.dumps(
                {'code': ServiceCode.service_exception, 'msg': u"服务器失败",'rows': r_data})
        else:
            return_data = json.dumps(
                {'code': ServiceCode.success, 'msg': u"服务器成功",'rows': r_data})
        finally:
            return tools.en_return_data(return_data)




class SaveFcInfo(MethodView):
    '''
    保存返厂单信息
    '''
    def post(self):
        return_data = None
        r_data = {}
        fc_info_dict = {}
        try:
            #返厂单号
            fc_info_dict["number"] = request.values.get("number","")
            #制单人
            fc_info_dict["user"] = request.values.get("user","")
            #日期
            fc_info_dict["date"] = request.values.get("date","")
            #出库类型
            # fc_info_dict["operate_type"] = request.values.get("operate_type","")
            fc_info_dict["operate_type"] = request.values.get("operate_type_id","")
            #发送单位
            fc_info_dict["send_site"] = request.values.get("send_site","")
            #接收单位
            fc_info_dict["recv_site"] = request.values.get("recv_site","")
            #备注信息
            fc_info_dict["remark_info"] = request.values.get("remark_info","")
            #店铺id
            fc_info_dict["flagshipid"] = request.values.get("flagshipid","",type=int)
            #物流信息
            fc_info_dict["logistics_name"] = request.values.get("logistics_name","")

            product_list = request.values.get("product_list","")
            product_list = json.loads(product_list)
            fc_info_dict["all_amount"] = len(product_list)
            good_list = []
            for item in product_list:
                item_dict = {}
                item_dict["good_id"] = item["a_p_id"]
                item_dict["serial_number"] = item["searialno"]
                item_dict["count"] = 1
                item_dict["customer_id"] = item["a_c_id"]
                item_dict["deal_with_information_id"] = item["a_t_id"]
                item_dict["bill_num"] = item["number"]
                good_list.append(item_dict)
            fc_info_dict["good_list"] = good_list
            fc_info_dict["user_id"] = session['user']['id']
            fc_info_dict["warehouse_type_id"] = WarehouseType.back_factory_warehouse
            fc_info_dict["to_warehouse_type_id"] = WarehouseType.out_warehouse
            #2016-10-31 tjx  单据类型为 FC_RECEIPTS
            fc_info_dict["number_type"] = FC_RECEIPTS

            op = ReturnedFactory()
            rs = op.save_fc_info(fc_info_dict)
            if not rs :
                raise CodeError(300,u"服务器失败")
        except CodeError as e:
            return_data = json.dumps(e.json_value())
        except Exception as e:
            print traceback.format_exc()
            return_data = json.dumps(
                {'code': ServiceCode.service_exception, 'msg': u"服务器失败",'rows': r_data})
        else:
            return_data = json.dumps(
                {'code': ServiceCode.success, 'msg': u"服务器成功",'rows': r_data})
        finally:
            return tools.en_return_data(return_data)

class AfterSale(MethodView):
    def get(self):
        return ""

        
add_url.flagship_add_url(u"门店售后服务", "flagship_manage.FlagshipManageView", add_url.TYPE_ENTRY, flagship_manage_prefix,
                         flagship_manage, '/after_sale/', 'AfterSale', AfterSale.as_view('AfterSale'), 60,methods=['GET','POST'])

add_url.flagship_add_url(u"返厂发货","flagship_manage.AfterSale",add_url.TYPE_ENTRY, flagship_manage_prefix,
                         flagship_manage,'/returned_factory/','returnedfactory',
                         ReturnedFactoryDeliver.as_view('returnedfactory'), 70, methods=['GET'])

add_url.flagship_add_url(u"返厂明细","flagship_manage.returnedfactory", add_url.TYPE_FEATURE,flagship_manage_prefix,
                         flagship_manage,'/detatil_returnedfactory/', 'detailofreturnedfactory',
                         DetailOfReturnedFactory.as_view('detailofreturnedfactory'),methods=['GET'])


add_url.flagship_add_url(u"制作返厂单", "flagship_manage.returnedfactory", add_url.TYPE_FEATURE, flagship_manage_prefix,
                flagship_manage, '/create_fc_order/', 'CreateFcOrder', CreateFcOrder.as_view('CreateFcOrder'),methods=['GET'])

add_url.flagship_add_url(u"选择返厂产品", "flagship_manage.CreateFcOrder", add_url.TYPE_FEATURE, flagship_manage_prefix,
                flagship_manage, '/query_fc_product/', 'QueryFcProduct', QueryFcProduct.as_view('QueryFcProduct'),methods=['POST'])


add_url.flagship_add_url(u"保存返厂单信息", "flagship_manage.CreateFcOrder", add_url.TYPE_FEATURE, flagship_manage_prefix,
                flagship_manage, '/save_fc_info/', 'SaveFcInfo', SaveFcInfo.as_view('SaveFcInfo'),methods=['POST'])
