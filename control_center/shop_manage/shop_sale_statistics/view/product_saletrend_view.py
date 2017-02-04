#-*-coding:utf-8-*-
from public.exception.custom_exception import CodeError
from config.service_config.returncode import ServiceCode
from flask import session
from flask.views import MethodView
from flask import render_template, current_app, request, url_for
from flask import jsonify
from flask import json
from pprint import pprint
from public.function import tools
from control_center.shop_manage import shop_manage,shop_manage_prefix
from control_center.admin import add_url
import traceback
import time
from data_mode.hola_flagship_store.base_op.sale_product_statistic import ProductSaleStatisticOp
from data_mode.hola_flagship_store.base_op.sale_product_statistic import get_lastmonth
from control_center.shop_manage.shop_sale_statistics.control.mixOp import ShopSaleStatisticOp
from control_center.shop_manage.shop_sale_statistics.control.mixOp import SaleStatisticFlag

class ProductTrendView(MethodView):
    """
    销售统计-销售趋势页面跳转接口
    """
    def get(self):
        return_data = None
        try:
            # start_time = request.values.get('start_time', int)
            # stop_time = request.values.get('stop_time','', str)

            curdate = [time.localtime()[0], time.localtime()[1]]
            strcurdate = (str(curdate[0])).zfill(4) + "-" + (str(curdate[1])).zfill(2)
            strlastdate = get_lastmonth(curdate)

            product_statistic_op = ProductSaleStatisticOp()
            #获取当前月排名前三的商品
            product_list = product_statistic_op.get_order_product_info(strcurdate,None,None,SaleStatisticFlag.product_trendsale)
            #分别获取每个商品在时间范围内没有的统计情况
            product_id_list=[product['product_id'] for product in product_list]
            shop_statistic_op = ShopSaleStatisticOp()
            product_datas = shop_statistic_op.get_product_sale_tend(product_id_list,strlastdate,strcurdate,SaleStatisticFlag.store_trendsale)
            product_info = shop_statistic_op.get_all_saleproduct_name()
            # 遇到业务错误
            #raise CodeError(ServiceCode.service_exception, 'Service Error')
        except CodeError as e:
            return_data = jsonify(e.json_value())
        except Exception as e:
            print traceback.format_exc(e)
            return_data = jsonify(
                {'code': ServiceCode.service_exception, 'msg': u"服务器失败"})
        else:
            datas = {
                'code': ServiceCode.success,
                'msg': "success",
                'curdate':strcurdate,
                'predate':strlastdate,
                'sale_info': product_datas,
                'product_info':product_info
            }
            return_data = json.dumps(datas)
        finally:
            return tools.en_render_template('salegoods/saleTrend.html', result=return_data)

class ProductTrendSearch(MethodView):
    """
    销售统计-销售趋势页面时间搜索接口
    """
    def post(self):
        return_data = None
        try:
            start_time = request.values.get('start_time', str)
            stop_time = request.values.get('stop_time','', str)
            product_id_list = request.values.get('product_id_list')
            print("=="*20+"product_id_list" + "=="*20)

            shop_statistic_op = ShopSaleStatisticOp()
            product_datas = shop_statistic_op.get_product_sale_tend(json.loads(product_id_list),start_time,stop_time,3)
            # 遇到业务错误
            #raise CodeError(ServiceCode.service_exception, 'Service Error')
        except CodeError as e:
            return_data = jsonify(e.json_value())
        except Exception as e:
            print traceback.format_exc(e)
            return_data = jsonify(
                {'code': ServiceCode.service_exception, 'msg': u"服务器失败"})
        else:
            datas = {
                'code': ServiceCode.success,
                'msg': "success",
                'sale_info': product_datas
            }
            return_data = json.dumps(datas)
        finally:
            return tools.en_return_data(return_data)


add_url.add_url(u'销售趋势','shop_manage.ShopSaleMgt',add_url.TYPE_ENTRY,shop_manage_prefix,shop_manage,
                '/product_trend/','product_trend',ProductTrendView.as_view('product_trend'), 60, methods=['GET'])

add_url.add_url(u'趋势搜索', 'shop_manage.product_trend', add_url.TYPE_FEATURE, shop_manage_prefix,shop_manage,
                '/producttrend_search/','producttrend_search',ProductTrendSearch.as_view('producttrend_search'), methods=['POST'])
