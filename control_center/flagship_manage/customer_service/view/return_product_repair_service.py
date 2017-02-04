#/usr/bin/python
#-*- coding:utf-8 -*-
from control_center.flagship_manage import flagship_manage, flagship_manage_prefix
from control_center.admin import add_url
from flask import session
import types

from flask.views import MethodView
from flask import render_template, current_app, request, url_for
from flask import jsonify
from flask import json
from pprint import pprint
from public.function import tools

import traceback
from config.service_config.returncode import ServiceCode
from public.exception.custom_exception import CodeError
import datetime

from control_center.flagship_manage.customer_service.control.mixOP import QueryReturnFactoryInfoOp
from config.share.share_define import DEAL_WITH_TYPE, translate_dict_to_list, WX_VALUE_RANGE, ORDER_PROGRESS,\
    TREATMENT_KEEP
from data_mode.hola_flagship_store.base_op.product_repair_service import AfterSaleRepariOp

class ReturnedProductRepair(MethodView):
    def get(self):
        return_data = None
        datas = {}
        try:
            repari_op = QueryReturnFactoryInfoOp()

            flag = request.values.get('flag', 1, int)
            flagshipid = request.values.get('flagshipid', 0,int)
            searchtype = request.values.get('type',1, int)
            searchvalue = request.values.get('value',"", str)
            starttime = request.values.get('starttime','', str)
            stoptime = request.values.get('stoptime','',str)
            dealtype = request.values.get('dealtype',None,int)
            page = request.values.get('page',1,int)
            pagenum = request.values.get('pagenum',10,int)
            product_info_list,total = repari_op.get_number_of_repair(flagshipid,starttime,stoptime,searchtype,searchvalue,page,pagenum,dealtype)


            # 遇到业务错误
            #raise CodeError(ServiceCode.service_exception, 'Service Error')
        except CodeError as e:
            return_data = json.dumps(e.json_value())
        except Exception as e:
            print traceback.format_exc(e)
            return_data = json.dumps(
                {'code': ServiceCode.service_exception, 'msg': u"服务器失败"})
        else:
            datas['code'] = ServiceCode.success
            datas['total'] = total
            datas['dealtype'] = translate_dict_to_list(DEAL_WITH_TYPE, WX_VALUE_RANGE)
            datas['rows'] = product_info_list
            return_data = json.dumps(datas)

        finally:
            if flag:
                return tools.flagship_render_template("afterSales/repairList.html",result=return_data)
            else:
                return tools.en_return_data(return_data)

class NewRepariService(MethodView):
    def get(self):
        from control_center.flagship_manage.sale_manage.control.SearchProductInfo_Op import SearchInfo_Op
        from control_center.flagship_manage.flagship_info_manage.control.mixOp import ClerkOp
        from control_center.shop_manage.good_info_manage.control.mixOp import HolaWareHouse
        from data_mode.hola_flagship_store.mode.warehouse_mode.warehouse_manage import OperateType
        from public.sale_share.share_function import ShareFunctionOp
        holahouse_op = HolaWareHouse()
        return_data = None
        datas = {}
        try:
            flagshipid = request.values.get('flagshipid', 0,int)

            #生成返修单号
            shareFunc_op = ShareFunctionOp()
            number_dict = shareFunc_op.create_numberNo(flagshipid, OperateType.wx_service)
            if number_dict['code'] != 100:
                raise ValueError(u"创建维修单号失败")

            number = number_dict['number']


            #订单处理进度列表
            progress = translate_dict_to_list(ORDER_PROGRESS)

            #商品类别列表
            producttype = []
            category_info = holahouse_op.show_all_category()
            for item in category_info:
                temp_dict = {}
                temp_dict['id'] = item['id']
                temp_dict['name'] = item['name']
                producttype.append(temp_dict)

            #保内/保外列表
            guarantee = translate_dict_to_list(TREATMENT_KEEP)

            #处理方式列表
            dealtype = translate_dict_to_list(DEAL_WITH_TYPE, WX_VALUE_RANGE)

            #获取门店
            search_op = SearchInfo_Op()
            store_name = search_op.get_store_name(flagshipid)
            # 门店销售员信息
            clerk_op = ClerkOp()
            clerk_infos = clerk_op.get_clerks_info(flagshipid)
            salesman_list = []
            for clerk in clerk_infos:
                sales_dict = {}
                sales_dict['workerno'] = clerk['work_number']
                sales_dict['name'] = clerk['name']
                salesman_list.append(sales_dict)


            # 遇到业务错误
            #raise CodeError(ServiceCode.service_exception, 'Service Error')
        except CodeError as e:
            return_data = json.dumps(e.json_value())
        except Exception as e:
            print traceback.format_exc(e)
            return_data = json.dumps(
                {'code': ServiceCode.service_exception, 'msg': u"服务器失败"})
        else:
            datas['code'] = ServiceCode.success
            datas['number'] = number
            datas['store'] = store_name
            datas['progress'] = progress
            datas['producttype'] = producttype
            datas['guarantee'] = guarantee
            datas['worker'] = salesman_list
            datas['dealtype'] = dealtype
            datas['datetime'] = (datetime.datetime.now()).strftime("%Y-%m-%d %H:%M:%S")

            return_data = json.dumps(datas)

        finally:
            return tools.flagship_render_template("afterSales/repairAdd.html",result=return_data)



class PrintRepairServiceBill(MethodView):
    def post(self):
        from control_center.flagship_manage.flagship_info_manage.control.flagship_op import FlagShipOp
        return_data = None
        datas = {}
        try:
            flagshipid = request.values.get('flagshipid', 0,int)
            repair_number = request.values.get('number',str)

            if repair_number is None:
                raise ValueError("返修订单号number传入失败")

            #获取门店信息
            flagship_op = FlagShipOp()
            store_info = flagship_op.get_flagship_info_by_flagship_id(flagshipid)
            store_name = store_info['name']     #服务门店
            tel = store_info['telephone']       #门店电话

            repair_service_op = AfterSaleRepariOp()
            #获取客户信息
            customer_dict = repair_service_op.get_customer_info_by_reparinumber(repair_number)
            customerinfo = {}
            customerinfo['customer'] = customer_dict['name']
            customerinfo['tel'] = customer_dict['tel']
            customerinfo['email'] = customer_dict['email']
            customerinfo['prov'] = customer_dict['buy_prov']
            customerinfo['city'] = customer_dict['buy_city']
            customerinfo['addr'] = customer_dict['buy_addr']
            #获取其它维修信息
            others = repair_service_op.get_all_product_by_repairnumber(repair_number)
            purchase_date = others['productinfo']['date']       #购机日期
            invoiceno = others['productinfo']['invoiceno']      #发票号

            service_dict = {}
            service_dict['type'] = others['dealinfo']['dealtype_id']            #服务类型id
            service_dict['name'] = others['dealinfo']['dealtype']             #服务类型
            service_dict['datetime'] = others['takeinfo']['datetime']            #服务开始日期及时间
            service_dict['worker']  = others['takeinfo']['worker']            #服务人

            is_charge = others['repairinfo']['is_charge']                        #服务标准（收费、免费）

            product_dict = {}
            product_dict['model'] = others['productinfo']['name']                #产品型号
            product_dict['color'] =''               #暂时没有颜色信息
            product_dict['searialno'] = others['productinfo']['searialno']            #产品序列号
            product_dict['problem'] = others['dealinfo']['problem']              #产品故障描述
            product_dict['product'] = others['productinfo']['product']      #随机配件

            quote = others['repairinfo']['quote']                        #服务费金额（报价金额）


            # 遇到业务错误
            #raise CodeError(ServiceCode.service_exception, 'Service Error')
        except CodeError as e:
            return_data = json.dumps(e.json_value())
        except Exception as e:
            print traceback.format_exc(e)
            return_data = json.dumps(
                {'code': ServiceCode.service_exception, 'msg': u"服务器失败"})
        else:
            datas['code'] = ServiceCode.success
            datas['number'] = repair_number
            datas['customerinfo'] = customerinfo
            datas['purchase_date'] = purchase_date
            datas['store'] = store_name
            datas['store_tel'] = tel
            datas['invoiceno'] = invoiceno
            datas['service'] = service_dict
            datas['is_charge'] = is_charge
            datas['productinfo'] = product_dict
            datas['quote'] = quote
            return_data = json.dumps(datas)
        finally:
           return tools.en_return_data(return_data)

class DetailOfRepariNum(MethodView):
    def get(self):
        from control_center.flagship_manage.sale_manage.control.SearchProductInfo_Op import SearchInfo_Op
        return_data = None
        datas = {}
        try:
            flagshipid = request.values.get('flagshipid', 0,int)
            repair_number = request.values.get('number', str)

            if repair_number is None:
                raise ValueError("返修订单号number传入失败")

            #获取受理网点
            search_op = SearchInfo_Op()
            store_name = search_op.get_store_name(flagshipid)
            #获取受理进度
            repair_service_op = AfterSaleRepariOp()
            progress = repair_service_op.get_repairprogress_by_reparinumber(repair_number)
            #获取客户信息
            customer_dict = repair_service_op.get_customer_info_by_reparinumber(repair_number)
            customerinfo = {}
            customerinfo['customer'] = customer_dict['name']
            customerinfo['tel'] = customer_dict['tel']
            customerinfo['email'] = customer_dict['email']
            customerinfo['prov'] = customer_dict['buy_prov']
            customerinfo['city'] = customer_dict['buy_city']
            customerinfo['addr'] = customer_dict['buy_addr']
            #获取其它维修信息
            others = repair_service_op.get_all_product_by_repairnumber(repair_number, flagshipid)

        except CodeError as e:
            return_data = json.dumps(e.json_value())
        except Exception as e:
            print traceback.format_exc(e)
            return_data = json.dumps(
                {'code': ServiceCode.service_exception, 'msg': u"服务器失败"})
        else:
            datas['code'] = ServiceCode.success
            datas['number'] = repair_number
            datas['store'] = store_name
            datas['progress'] = progress
            datas['customerinfo'] = customerinfo
            datas['productinfo'] = others['productinfo']
            datas['dealinfo'] = others['dealinfo']
            datas['repairinfo'] = others['repairinfo']
            datas['takeinfo'] = others['takeinfo']
            return_data = json.dumps(datas)
        finally:
            return tools.flagship_render_template("afterSales/repairDetail.html",result=return_data)

class SaveRepailBill(MethodView):
    def get(self):
        datas = {}
        return_data = {}
        try:
            code = request.values.get('code', int)
            if isinstance(code, types.NoneType):
                raise ValueError(u"未传输响应码code")
        except CodeError as e:
            return_data = json.dumps(e.json_value())
        except Exception as e:
            print traceback.format_exc(e)
            return_data = json.dumps(
                {'code': ServiceCode.service_exception, 'msg': u"服务器失败"})
        else:
            datas['code'] = code
            return_data = json.dumps(datas)
        finally:
            return tools.flagship_render_template("afterSales/saveRepairBill.html",result=return_data)




add_url.flagship_add_url(u"售后维修","flagship_manage.AfterSale",add_url.TYPE_ENTRY, flagship_manage_prefix,
                         flagship_manage,'/returned_repair/','repairlist',
                         ReturnedProductRepair.as_view('repairlist'), 90, methods=['GET'])

add_url.flagship_add_url(u"新建维修服务","flagship_manage.repairlist", add_url.TYPE_FEATURE,flagship_manage_prefix,
                         flagship_manage, '/new_repair_service/', 'newrepairbill',
                         NewRepariService.as_view('newrepairbill'), methods=['GET'])

add_url.flagship_add_url(u"打印服务单","flagship_manage.repairlist",add_url.TYPE_FEATURE,flagship_manage_prefix,
                         flagship_manage, 'print_repari_servicebill','printservicebill',
                         PrintRepairServiceBill.as_view('printservicebill'), methods=['POST'])

add_url.flagship_add_url(u"返修单明细","flagship_manage.repairlist", add_url.TYPE_FEATURE,flagship_manage_prefix,
                         flagship_manage,'/detail_repair_number/','detailofrepair',
                         DetailOfRepariNum.as_view('detailofrepair'), methods=['GET'])

add_url.flagship_add_url(u"维修单保存","flagship_manage.newrepairbill", add_url.TYPE_FEATURE,flagship_manage_prefix,
                         flagship_manage,'/save_repair_number/','saverepailnumber',
                         SaveRepailBill.as_view('saverepailnumber'), methods=['GET'])
