#/usr/bin/python
#-*- coding:utf-8 -*-

import json
import types

from flask import request
from flask.views import MethodView
from control_center.flagship_manage.sale_manage.control.saleProductOp import *
from config.service_config.returncode import ServiceCode
from control_center.admin import add_url
from control_center.flagship_manage.flagship_info_manage.control.mixOp import ClerkOp
from control_center.flagship_manage.sale_manage.control.SearchProductInfo_Op import SearchInfo_Op
from control_center.flagship_manage import flagship_manage, flagship_manage_prefix
from control_center.flagship_manage.warehouse_manage.control.ship_in_warehouse_op import ShipInwarehouse
from data_mode.user_center.control.mixOp import MixUserCenterOp
from public.function import tools


class SaleView(MethodView):
    """
    电子邮箱 :   qcheng@jmgo.com
    日期   :   2016/09/08 16:06:08
    功能描述：跳转到销售页面
    """
    def get(self):
        try:
            store_id = request.values.get('flagshipid', int)      #店铺id
            ptype = request.values.get('type', 1, int)          #1：单品   2：套餐    3：赠品
            stype = request.values.get('stype', 1, int)         #搜索类型（1：商品名称关键字 2：商品编码 3：套餐名称关键字）
            svalue = request.values.get('svalue', '', str)      #搜索内容
            curPage = request.values.get('curPage', 1, int)     #分页的当前页
            pageCounts = request.values.get('pageList', 5, int)            #当前页理论显示的记录数

            orderdetail = OrderDetail()
            payData = orderdetail.getPayType()

            #获取商品信息
            searchinfo_op = SearchInfo_Op()
            total, data = searchinfo_op.get_product_info(store_id, ptype, stype, svalue.strip(), curPage, pageCounts)
            count = len(data)

            #获取门店
            store_name = searchinfo_op.get_store_name(store_id)
            # 门店销售员信息
            clerk_op = ClerkOp()
            clerk_infos = clerk_op.get_clerks_info(store_id)
            salesman_list = []
            for clerk in clerk_infos:
                sales_dict = {}
                swork_number = clerk['work_number']
                sname = clerk['name']
                sales_dict[swork_number] = sname
                salesman_list.append(sales_dict)

            mixuser_op =  MixUserCenterOp()
            work_number = mixuser_op.get_salesmen_worknumber()
            cashier_name = session['user']['name']

            if isinstance(work_number, types.NoneType):
                work_number = ''

            return_data = {
                'code': ServiceCode.success,
                'total': total,
                'count': count,
                'product':data,
                'salesman_list':salesman_list,
                'store_name': store_name,
                'cashier':cashier_name,
                'cashierNo':work_number,
                'payType': payData
            }

            return tools.en_render_template('salegoods/salegoods.html',result=json.dumps(return_data))

        except Exception, ex:
            print(traceback.format_exc())
            data = {'code': ServiceCode.service_exception, 'msg': u'服务器错误'}
            return tools.en_render_template('salegoods/salegoods.html',result=json.dumps(data))


class SearchProductInfo(MethodView):
    """
    电子邮箱 :   qcheng@jmgo.com
    日期   :   2016/09/07 20:40:10
    功能描述：根据指定参数搜索相应的数据记录
    """
    def post(self):
        try:
            store_id = request.values.get('flagshipid', int)      #店铺id
            ptype = request.values.get('type', 1, int)          #1：单品   2：套餐    3：赠品
            stype = request.values.get('stype', 1, int)         #搜索类型（1：商品名称关键字 2：商品编码 3：套餐名称关键字）
            svalue = request.values.get('svalue', '', str)      #搜索内容
            curPage = request.values.get('curPage', 1, int)     #分页的当前页
            pageCounts = request.values.get('pageList', 5, int)            #当前页理论显示的记录数

             #获取商品信息
            searchinfo_op = SearchInfo_Op()
            total, data = searchinfo_op.get_product_info(store_id, ptype, stype, svalue.strip(), curPage, pageCounts)
            count = len(data)

            return_data = {
                'code': ServiceCode.success,
                'total': total,
                'count': count,
                'product':data,
            }

            return tools.en_return_data(json.dumps(return_data))

        except Exception, ex:
            print(traceback.format_exc())
            data = {'code': ServiceCode.service_exception, 'msg': u'服务器错误'}
            return tools.en_return_data(json.dumps(data))


class PerPageInfo(MethodView):
    """
    作者   :   ChengQian
    电子邮箱 :   qcheng@jmgo.com
    日期   :   2016/09/07 20:40:10
    功能描述：根据指定参数获取当前页的商品信息
    """
    def post(self):
        try:
            store_id = request.values.get('flagshipid', int)      #店铺id
            ptype = request.values.get('type', 1, int)          #1：单品   2：套餐    3：赠品
            stype = request.values.get('stype', 1, int)         #搜索类型（1：商品名称关键字 2：商品编码 3：套餐名称关键字）
            svalue = request.values.get('svalue', '', str)      #搜索内容
            curPage = request.values.get('curPage', 1, int)     #分页的当前页
            pageCounts = request.values.get('pageList', 5, int)            #当前页理论显示的记录数

            #获取商品信息
            searchinfo_op = SearchInfo_Op()
            total, data = searchinfo_op.get_product_info(store_id, ptype, stype, svalue.strip(), curPage, pageCounts)
            count = len(data)

            return_data = {
                'code': ServiceCode.success,
                'total': total,
                'count': count,
                'product': data
            }

            return tools.en_return_data(json.dumps(return_data))

        except Exception, ex:
            print(traceback.format_exc())
            data = {'code': ServiceCode.service_exception, 'msg': u'服务器错误'}
            return tools.en_return_data(json.dumps(data))

        #获取指定店铺指定类型（单品、套餐或赠品）当前页的记录数据


class CheckProductSerialNo(MethodView):
    """
    电子邮箱 :   qcheng@jmgo.com
    日期   :   2016/09/07 20:48:42
    功能描述：校验该商品对应的SN码(序列号)在目前库存中是否存在
    """
    def post(self):
        try:
            store_id = request.values.get('flagshipid', int)
            SerialNo = request.values.get('p_sn', str)
            product_id = request.values.get('product_id', int)

            shipinwarehouse = ShipInwarehouse()
            return_code = shipinwarehouse.GetSnCode(SerialNo.strip(), store_id, product_id)

            if isinstance(return_code, types.NoneType):
                return_code = ServiceCode.goodsSnNotExist
            return_data = {}
            return_data['code'] = return_code
            return tools.en_return_data(json.dumps(return_code))
        except Exception, ex:
            print(traceback.format_exc())
            data = {'code': ServiceCode.service_exception, 'msg': u'服务器错误'}
            return tools.en_return_data(json.dumps(data))


class DetailOfSaleOrderNo(MethodView):
    def get(self):
        try:
            #根据订单号获取订单详情
            store_id = request.values.get('flagshipid', int)
            orderNo = request.values.get('orderNo', str)
            if isinstance(orderNo, types.NoneType):
                pass
            else:
                #获取订单信息
                searchinfo_op = SearchInfo_Op()
                orderNo_info, money_info, customer_info, sendinfo, invoice_info, product_list, set_list = searchinfo_op.get_order_detail_info(orderNo)

                return_data = {
                    'code': ServiceCode.success,
                    'order':orderNo_info,
                    'money':money_info,
                    'customer':customer_info,
                    'send':sendinfo,
                    'invoice':invoice_info,
                    'product': product_list,
                    'set': set_list
                }
            return tools.en_render_template('salegoods/tradeDetail.html',result=json.dumps(return_data))

        except Exception, ex:
            print(traceback.format_exc())
            data = {'code': ServiceCode.service_exception, 'msg': u'服务器错误'}
            return tools.en_render_template('salegoods/tradeDetail.html', result=json.dumps(data))

            
class PrintReceipts(MethodView):
    """
    打印小票功能
    """
    def get(self):
        try:
            store_id = request.values.get('flagshipid', int)
            orderNo = request.values.get('orderNo', str)
            searchinfo_op = SearchInfo_Op()
            store_full_name, cashier, temp_good_list, totalPrice, setPrice, actPrice ,change,curTime= searchinfo_op.print_receipts(store_id, orderNo)
            return_data = {
                'code': ServiceCode.success,
                'full_name': store_full_name,
                'CurTime':curTime,
                'cashier':cashier,
                'totalPrice':totalPrice,
                'setPrice':setPrice,
                'actPrice':actPrice,
                'change':change,
                'product':temp_good_list
            }
            return tools.en_return_data(json.dumps(return_data))
        except Exception, ex:
            print(traceback.format_exc())
            data = {'code': ServiceCode.service_exception, 'msg': u'服务器错误'}
            return tools.en_return_data(json.dumps(data))

            
class EditOrderInfo(MethodView):
    """
    订单详情页面的订单备注信息编辑后保存时更新数据库中的内容
    """
    def post(self):
        try:
            return_data = {}
            store_id = request.values.get('flagshipid', int)
            orderNo = request.values.get('orderNo', str)
            orderInfo = request.values.get('orderInfo', str)

            searchinfo_op = SearchInfo_Op()
            res = searchinfo_op.update_order_note(orderNo, orderInfo)

            if res:
                return_data['code'] = ServiceCode.success
            else:
                return_data['code'] = ServiceCode.service_exception
                return_data['msg'] = u"在数据表sale_order中未查到订单号为"+ orderNo + u"的记录"

            return tools.en_return_data(json.dumps(return_data))
            #更新数据库中的内容
        except SQLAlchemyError as e:
            print(traceback.format_exc(e))
            data = {'code': ServiceCode.service_exception, 'msg': u'sale_order表中的订单备注信息更新失败'}
            return tools.en_return_data(json.dumps(data))


class SendProduct(MethodView):
    def get(self):
        try:
            store_id = request.values.get('flagshipid', int)
            orderNo = request.values.get('orderNo', str)

            searchinfo_op = SearchInfo_Op()
            good_dict, detail_addr = searchinfo_op.CreateOutOrder(str(store_id), orderNo)
            res = searchinfo_op.get_out_num(store_id, good_dict, orderNo, detail_addr)

            return_data={}
            if res==None:
                return_data = {'code': ServiceCode.service_exception, 'msg': u'服务器错误'}
            else:
                return_data = {
                    'code': ServiceCode.success,
                    'outno': res
                }

            return tools.en_return_data(json.dumps(return_data))
        except Exception, ex:
            print(traceback.format_exc())
            data = {'code': ServiceCode.service_exception, 'msg': u'服务器错误'}
            return tools.en_return_data(json.dumps(data))


add_url.flagship_add_url(u"门店销售开单", "flagship_manage.FlagshipManageView", add_url.TYPE_ENTRY, flagship_manage_prefix,
                flagship_manage, '/sale_view/', 'sale_view', SaleView.as_view('sale_view'),80, methods=['POST','GET'])

add_url.flagship_add_url(u"搜索", "flagship_manage.sale_view", add_url.TYPE_FEATURE, flagship_manage_prefix,
                         flagship_manage, '/search_info/', 'SearchProductInfo', SearchProductInfo.as_view('SearchProductInfo'), methods=['POST','GET'])

add_url.flagship_add_url(u"下一页", "flagship_manage.sale_view", add_url.TYPE_FUNC, flagship_manage_prefix, flagship_manage,
                         '/perpage_product/', 'perpage_product',PerPageInfo.as_view('perpage_product'), methods=['POST','GET'])

add_url.flagship_add_url(u"校验SN码", "flagship_manage.sale_view", add_url.TYPE_FUNC, flagship_manage_prefix, flagship_manage,
                         '/check_serialno/', 'CheckProductSerialNo', CheckProductSerialNo.as_view('CheckProductSerialNo'), methods=['POST','GET'])

add_url.flagship_add_url(u"订单详情", "flagship_manage.show_order_list", add_url.TYPE_FUNC, flagship_manage_prefix, flagship_manage,
                         '/detailoforderno/','DetailOfSaleOrderNo', DetailOfSaleOrderNo.as_view('DetailOfSaleOrderNo'), methods=['POST','GET'] )

add_url.flagship_add_url(u"确定配送出货","flagship_manage.show_order_list", add_url.TYPE_FEATURE, flagship_manage_prefix,flagship_manage,
                         '/send_product/','SendProduct', SendProduct.as_view('SendProduct'), methods=['POST','GET'])

add_url.flagship_add_url(u"打印小票","flagship_manage.show_order_list", add_url.TYPE_FEATURE, flagship_manage_prefix, flagship_manage,
                         '/print_receipts/','PrintReceipts', PrintReceipts.as_view('PrintReceipts'), methods=['POST','GET'])
                         
add_url.flagship_add_url(u"更新订单备注", "flagship_manage.show_order_list", add_url.TYPE_FEATURE, flagship_manage_prefix,flagship_manage,
                         '/update_ordernote/', 'EditOrderInfo', EditOrderInfo.as_view('EditOrderInfo'), methods=['POST','GET'])