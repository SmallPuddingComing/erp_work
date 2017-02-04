#/usr/bin/python
#-*- coding:utf-8 -*-

import json
import os
from flask import request
from flask.views import MethodView
from control_center.flagship_manage.sale_manage.control.saleProductOp import *
from control_center.flagship_manage.sale_manage.control.mixOp import FlagshipOrderInfoOp

from config.service_config.returncode import *
from control_center.admin import add_url
from control_center.flagship_manage.sale_manage.control.SearchProductInfo_Op import *
from control_center.flagship_manage import flagship_manage, flagship_manage_prefix
from public.exception.custom_exception import CodeError
from public.function import tools
from flask import make_response, send_file

#请求页面
class SaleWareHouseView(MethodView):
    def get(self):
        categoryList = HolaWareHouse().GetBaseProductCategory()
        if not categoryList:
            return 'Product Category Data Not Find!'
        account = session["user"]["username"]
        return tools.flagship_render_template('sale/sale.html', goodsTypeData=json.dumps(categoryList), account=account)

class CompleteCashier(MethodView):
    '''complete cashier to create order
    return order number
    '''
    def post(self):
        store_id = request.values.get('store_id', "")
        salesman = request.values.get('salesman', "")
        cashier = request.values.get('cashier', "")
        act_price = request.values.get('act_price', type=float)
        set_price = request.values.get('set_price', type=float)
        date_time = request.values.get('date_time', "") #NO  USER
        set_count_dict = request.values.get('set_count_dict', "")

        #新增0918
        send_tplid = request.values.get('send_tplid', "")
        pay_tplid = request.values.get('pay_tplid', "")

        product_list_info = request.values.get('product', "")
        product_list = json.loads(product_list_info)
        set_meal_list_info = request.values.get('set_product', "")
        set_meal_list = json.loads(set_meal_list_info)

        selt_date = datetime.datetime.now().strftime('%Y-%m-%d')
        selt_time = datetime.datetime.now().strftime('%H:%M:%S')

        # 选填字段
        selectDict = {}
        selectDict['consignee_name'] = request.values.get('consignee_name', "")  # 新增
        selectDict['consignee_tel'] = request.values.get('consignee_tel', "")  # 新增
        selectDict['province'] = request.values.get('province', "")
        selectDict['city'] = request.values.get('city', "")
        selectDict['addr'] = request.values.get('addr', "")

        return_data = {}
        try:
            op = FlagshipOrderInfoOp()
            data = op.getOrderNumber(store_id, salesman, cashier, set_price, act_price,
                           selt_date, selt_time, product_list, set_meal_list, set_count_dict, send_tplid, pay_tplid, kwargs=selectDict)
            if data is not None:
                data['code'] = ServiceCode.success
            else:
                return_data = {"code": ServiceCode.service_exception, "msg": "create order is fail!"}
            return_data = jsonify(data)
        except CodeError as e:
            print traceback.format_exc()
            return_data = jsonify(e.json_value())
        except Exception as e:
            print traceback.format_exc()
            return_data = jsonify({"code": ServiceCode.service_exception, "msg": u'服务器错误'})
        finally:
            return tools.en_return_data(return_data)


class OrderSupplement(MethodView):
    '''supplement order info
    return request code
    '''
    def post(self):
        orderNo = request.values.get('orderNo', "")

        #选填字段
        selectDict = {}
        selectDict['name'] = request.values.get('name', "")  #买家姓名
        selectDict['sex'] = request.values.get('sex', "") #买家性别
        selectDict['tel'] = request.values.get('tel', "") #买家电话

        selectDict['is_need_in'] = request.values.get('is_need_in', "") #是否需要开具发票，True需要
        selectDict['in_name'] = request.values.get('in_name', "") #发票名称
        selectDict['in_head'] = request.values.get('in_head', "")#发票抬头
        selectDict['in_comment'] = request.values.get('in_comment', "")#发票内容
        selectDict['describe'] = request.values.get('describe', "")#订单备注

        selectDict['buy_prov'] = request.values.get('buy_prov',"", str)  #买家所在省份 20160927cq新增
        selectDict['buy_city'] = request.values.get('buy_city',"", str) #买家所在城市
        selectDict['buy_addr'] = request.values.get('buy_addr', "", str) #买家所在城市内的详细地址

        return_data = {}
        try:
            op = OrderSupplementOp()
            if op.updateOrderInfo(orderNo, kwargs=selectDict): #, send_tplid,pay_tplid,
                return_data = jsonify({"code": ServiceCode.success})
            else:
                return_data = jsonify({"code": ServiceCode.service_exception, "msg": "supplement is error!"})
        except Exception as e:
            print traceback.format_exc()
            return_data = jsonify({"code": ServiceCode.service_exception, "msg":"server is error!"})
        finally:
            return tools.en_return_data(return_data)


class ShowOrderList(MethodView):
    '''order list view
    return data to view of show
    '''
    def get(self):
        return_data = {}
        flagshipid = request.values.get('flagshipid', type=int)

        try:
            op = OrderDetail()
            dataList, total, count = op.getOrderDetail(flagshipid)#, be_time, end_time, salesman,pay_type_id, orderNo, cur_page, pre_page
            payTypeDict = op.getPayType()
            salesmanDict = op.getAllSalesman(flagshipid)
            return_data['total'] = total
            return_data['count'] = count
            return_data['sales_dict'] = salesmanDict
            return_data['pay_type_dict'] = payTypeDict
            return_data['rows'] = dataList
            return_data['code'] = ServiceCode.success
            data = json.dumps(return_data)
            return tools.en_render_template('salegoods/tradeRecord.html',
                                            result=data)
        except Exception as e:
            print (traceback.format_exc(e))
            return tools.en_return_data(jsonify({"code": ServiceCode.service_exception}))


class SearchOrderList(MethodView): #按钮
    '''search the order by cashier and payType
    return data to view of search
    '''
    def post(self):
        flagshipid = request.values.get('flagshipid', type=int)
        be_time = request.values.get('be_time', "")
        end_time = request.values.get('end_time', "")
        salesman = request.values.get('salesman', "")
        pay_type_id = request.values.get('pay_type_id', type=int)
        orderNo = request.values.get('orderNo', "")
        cur_page = request.values.get('curPage', 1, type=int)
        pre_page = request.values.get('pageList',  10, type=int)

        return_data = {}
        try:
            op = OrderDetail()
            dataList, total, count = op.getOrderDetail(flagshipid, be_time, end_time, salesman,
                                                       pay_type_id, orderNo, cur_page, pre_page)
            return_data['total'] = total
            return_data['count'] = count
            return_data['rows'] = dataList
        except Exception as e:
            return_data = {"code": ServiceCode.service_exception, "msg":u'服务器'}
            print traceback.format_exc()
        finally:
            return tools.en_return_data(jsonify(return_data))

class SkipOrderListByNext(MethodView): #函数
    '''search the order by beginTime and endTime
    return data to view of search
    '''
    def post(self):
        flagshipid = request.values.get('flagshipid', type=int)
        be_time = request.values.get('be_time', "")
        end_time = request.values.get('end_time', "")
        salesman = request.values.get('salesman', "")
        pay_type_id = request.values.get('pay_type_id', type=int)
        orderNo = request.values.get('orderNo', "")
        cur_page = request.values.get('curPage', 1, type=int)
        pre_page = request.values.get('pageList', 10, type=int)

        return_data = {}
        try:
            op = OrderDetail()
            dataList, total, count = op.getOrderDetail(flagshipid, be_time, end_time, salesman,
                                                       pay_type_id, orderNo, cur_page, pre_page)

            return_data['total'] = total
            return_data['count'] = count
            return_data['rows'] = dataList
        except Exception as e:
            return_data = {"code": ServiceCode.service_exception, "msg":u'服务器'}
            print traceback.format_exc()
        finally:
            return tools.en_return_data(jsonify(return_data))

class ExportData(MethodView):
    '''export data from sale detail 表格
    '''
    def get(self):
        flagshipid = request.values.get("flagshipid", "")

        be_time = request.values.get('be_time', "")
        end_time = request.values.get('end_time', "")
        salesman = request.values.get('salesman', "")
        pay_type_id = request.values.get('pay_type_id', type=int)
        orderNo = request.values.get('orderNo', "")

        # print "################export data#############"
        return_data = {}
        response = None
        try:
            date_bgn_time = datetime.datetime.strptime(be_time, '%Y-%m-%d')
            date_end_time = datetime.datetime.strptime(end_time, '%Y-%m-%d')
            if (date_end_time-date_bgn_time).days > 100:
                raise CodeError(ServiceCode.params_error, u'导出的时间跨度不能超过100天')
            op = OrderDetail()
            filename_path = op.getDataFromExportExp(flagshipid, be_time, end_time, salesman,
                                                   pay_type_id, orderNo)


            response = make_response(send_file(filename_path))
            response.headers['Content-Type'] = 'application/vnd.ms-excel'
            response.headers['Content-Disposition'] = 'attachment;filename=%s' % (
                os.path.basename(filename_path).encode('utf-8'))

        except CodeError as e:
            print traceback.format_exc()
            return_data = e.json_value()
            return tools.en_return_data(jsonify(return_data))
        except Exception as e:
            print traceback.format_exc()
            return_data = {"code": ServiceCode.service_exception, "msg":u'服务器'}
            return tools.en_return_data(jsonify(return_data))
        else:
            return response

add_url.flagship_add_url(u"门店销售管理", 'flagship_manage.FlagshipManageView', add_url.TYPE_ENTRY, flagship_manage_prefix,
                flagship_manage, '/salewarehouse/', 'salewarehouse', SaleWareHouseView.as_view('salewarehouse'),70, methods=['GET'])

add_url.flagship_add_url(u"完成购物车结算", "flagship_manage.sale_view", add_url.TYPE_FEATURE, flagship_manage_prefix,
                flagship_manage, '/complete_cashier/', 'complete_cashier', CompleteCashier.as_view('complete_cashier'), methods=['GET', 'POST'])

add_url.flagship_add_url(u"补充订单", "flagship_manage.sale_view", add_url.TYPE_FEATURE, flagship_manage_prefix,
                flagship_manage, '/order_supplement/', 'order_supplement', OrderSupplement.as_view('order_supplement'), methods=['GET', 'POST'])

add_url.flagship_add_url(u"销售记录", "flagship_manage.salewarehouse", add_url.TYPE_ENTRY, flagship_manage_prefix,
                flagship_manage, '/show_order_list/', 'show_order_list', ShowOrderList.as_view('show_order_list'), methods=['GET', 'POST'])

add_url.flagship_add_url(u"查询订单页面", "flagship_manage.show_order_list", add_url.TYPE_FEATURE, flagship_manage_prefix,
                flagship_manage, '/search_order_list/', 'search_order_list', SearchOrderList.as_view('search_order_list'), methods=['GET', 'POST'])

add_url.flagship_add_url(u"页面跳转查询", "flagship_manage.show_order_list", add_url.TYPE_FUNC, flagship_manage_prefix,
                flagship_manage, '/skip_page_search/', 'skip_page_search', SkipOrderListByNext.as_view('skip_page_search'), methods=['GET', 'POST'])

add_url.flagship_add_url(u"销售记录导出数据", "flagship_manage.show_order_list", add_url.TYPE_FUNC, flagship_manage_prefix,
                flagship_manage, '/export_data/', 'export_data', ExportData.as_view('export_data'), methods=['GET', 'POST'])