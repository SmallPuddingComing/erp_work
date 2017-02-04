#/usr/bin/python
#-*- coding:utf-8 -*-
import os
from flask import session, make_response
from flask.views import MethodView
from flask import render_template, current_app, request, url_for, send_file
from flask import jsonify
from flask import json
import traceback
import time
from pprint import pprint
from public.function import tools
from control_center.shop_manage import shop_manage,shop_manage_prefix
from control_center.admin import add_url
from public.exception.custom_exception import CodeError
from config.service_config.returncode import ServiceCode
from data_mode.hola_flagship_store.base_op.sale_product_statistic import ProductSaleStatisticOp



class SalePerformanceView(MethodView):
    def get(self):
        return_data = None
        r_data = {}
        # print '****************SalePerformanceView*************************'
        # print request.values
        try:
            tm = time.localtime()
            date_time = str(tm.tm_year)+"-"+(str(tm.tm_mon)).zfill(2)

            search_dict = {
                'date_time' : date_time,
                'sale_person_name' : None,
                'flagship_id' : None,
                'per_page' : 10,
                'start' : 0,
                'sort_mode' : "sale_person_name",
                'click_num' : 1
            }
            # print '11111111111111111111111111111111111111search_dict       ',search_dict
            op = ProductSaleStatisticOp()
            data_info ,total = op.get_saleinfo_search(search_dict)


            op = ProductSaleStatisticOp()
            sale_channels = op.get_sale_channels()

            r_data = {
                'data_info':data_info,
                'total':total,
                'sale_channel' : sale_channels
            }

            # r_data = create_false_data()
            # print '数据：    ',r_data


            # 遇到业务错误
            if False:
                raise CodeError(300,u"服务器错误")
        except CodeError as e:
            # print '22222222'
            print traceback.format_exc()
            return_data = json.dumps(e.json_value())
        except Exception as e:
            # print '333333'
            print traceback.format_exc()
            return_data = json.dumps(
                {'code': ServiceCode.service_exception, 'msg': u"服务器失败",'data': r_data})
        else:
            # print '444444444',r_data,"***********"

            return_data = json.dumps(
                {'code': ServiceCode.success, 'msg': u"服务器成功",'data': r_data})
            # print '***********************',return_data
        finally:
            # print '11111111111111111111111',return_data
            return tools.en_render_template("salegoods/saleStatistics.html",return_data=return_data)

class SalePerforSearchView(MethodView):
    def post(self):
        return_data = None
        r_data = {}
        # print '****************SalePerforSearchView*************************'
        # print request.values
        try:
            date_time = request.values.get('date_time',None)
            sale_person_name = request.values.get('sale_person_name',None)
            flagship_id = request.values.get('flagship_id',None,int)
            per_page = request.values.get('per_page',10,int)
            page_num = request.values.get('page_num',1,int)
            sort_mode = request.values.get('sort_mode',None)
            click_num = request.values.get('click_num',3,int)

            page = page_num - 1
            if page < 0:
                page = 0
            if per_page > 60:
                per_page = 60
            start = page *per_page

            search_dict = {
                'date_time' : date_time,
                'sale_person_name' : sale_person_name,
                'flagship_id' : flagship_id,
                'per_page' : per_page,
                'start' : start,
                'sort_mode' : sort_mode,
                'click_num' : click_num
            }
            op = ProductSaleStatisticOp()
            data_info ,total = op.get_saleinfo_search(search_dict)
            r_data = {
                'data_info':data_info,
                'total':total
            }


            # 遇到业务错误
            if False:
                raise CodeError(300,u"服务器错误")
        except CodeError as e:
            return_data = json.dumps(e.json_value())
        except Exception as e:
            print traceback.format_exc()
            return_data = json.dumps(
                {'code': ServiceCode.service_exception, 'msg': u"服务器失败",'data': r_data})
        else:
            return_data = json.dumps(
                {'code': ServiceCode.success, 'msg': u"服务器成功",'data': r_data})
        finally:
            # print '*****************return_data*********************',return_data
            return tools.en_return_data(return_data)

class DetailProductView(MethodView):
    '''
    销售员销售单品明细
    '''
    def post(self):
        return_data = None
        r_data = {}
        # print '****************DetailProductView*************************'
        print request.values
        try:
            sale_person_id = request.values.get("sale_person_id",int)
            flagship_id = request.values.get("flagship_id",int)
            date_time = request.values.get("date_time",None)
            page_num = request.values.get("page_num",1,int)
            per_page = request.values.get("per_page",10,int)
            value_type = request.values.get("value_type","")
            value = request.values.get("value","")

            page = page_num - 1
            if page < 0:
                page = 0
            if per_page > 60:
                per_page = 60
            start = page *per_page
            user_dict = {
                "sale_person_id" : sale_person_id,
                "flagship_id" : flagship_id,
                "date_time" : date_time,
                "start" : start,
                "per_page" : per_page,
                "value_type" : value_type,
                "value" : value
            }

            op = ProductSaleStatisticOp()
            r_data = op.get_user_sale_info(user_dict)

            # 遇到业务错误
            if False:
                raise CodeError(300,u"服务器错误")
        except CodeError as e:
            return_data = json.dumps(e.json_value())
        except Exception as e:
            print traceback.format_exc()
            return_data = json.dumps(
                {'code': ServiceCode.service_exception, 'msg': u"服务器失败",'data': r_data})
        else:
            return_data = json.dumps(
                {'code': ServiceCode.success, 'msg': u"服务器成功",'data': r_data})
        finally:
            # print '*****************return_data*********************',return_data
            return tools.en_return_data(return_data)



class DetailSetmealView(MethodView):
    '''
    销售员销售套餐明细
    '''
    def post(self):
        return_data = None
        r_data = {}
        # print '****************DetailSetmealView*************************'
        # print request.values
        try:
            sale_person_id = request.values.get("sale_person_id",int)
            flagship_id = request.values.get("flagship_id",int)
            date_time = request.values.get("date_time",None)
            page_num = request.values.get("page_num",1,int)
            per_page = request.values.get("per_page",10,int)
            value_type = request.values.get("value_type","")
            value = request.values.get("value","")

            page = page_num - 1
            if page < 0:
                page = 0
            if per_page > 60:
                per_page = 60
            start = page *per_page

            user_dict = {
                "sale_person_id" : sale_person_id,
                "flagship_id" : flagship_id,
                "date_time" : date_time,
                "start" : start,
                "per_page" : per_page,
                "value_type" : value_type,
                "value" : value
            }

            # print "***********************user_dict**********************",user_dict
            op = ProductSaleStatisticOp()
            r_data = op.get_user_setmeal_info(user_dict)

            # 遇到业务错误
            if False:
                raise CodeError(300,u"服务器错误")
        except CodeError as e:
            return_data = json.dumps(e.json_value())
        except Exception as e:
            print traceback.format_exc()
            return_data = json.dumps(
                {'code': ServiceCode.service_exception, 'msg': u"服务器失败",'data': r_data})
        else:
            return_data = json.dumps(
                {'code': ServiceCode.success, 'msg': u"服务器成功",'data': r_data})
        finally:
            # print '*****************return_data*********************',return_data
            return tools.en_return_data(return_data)


class SalePerformance_Statement(MethodView):
    """
    业绩统计报表
    """
    def get(self):
        from control_center.shop_manage.shop_sale_statistics.control.statement import StatictisStatementOp
        from data_mode.hola_warehouse.control_base.controlBase import ControlEngine
        from data_mode.hola_warehouse.model.base_product_unit import BaseProductUnit
        import re
        try:
            # 获取请求参数
            date_time = request.values.get('datetime', None)
            if date_time is None or date_time == u'':
                raise CodeError(ServiceCode.params_error, u'请选择时间！')

            cle = re.compile(r'^\d{4}-\d{2}$')
            if not re.match(cle, date_time):
                raise CodeError(ServiceCode.params_error, u'上送的时间格式不正确')

            # 设置标题栏
            title = [u'促销员', u'销售渠道', u'成交单数', u'成交环比', u'销售额', u'销售环比']

            # 获取商品
            control_engien = ControlEngine()
            products = control_engien.controlsession.query(BaseProductUnit.id,
                                                           BaseProductUnit.name).order_by(BaseProductUnit.id).all()
            if len(products):
                title += [x[1] for x in products]

            # 获取内容
            prd_sale = ProductSaleStatisticOp()
            data = prd_sale.export_data(date_time)

            # 重组内容
            content = []
            for result in data:
                temp = [result['sale_person_name'],
                        result['flagship_name'],
                        result['sale_order_num'],
                        result['sale_order_chain'],
                        result['sale_money'],
                        result['sale_money_chain']
                        ]
                product_sale_num = result['p_dict']
                temp += [product_sale_num.get(x[0], 0) for x in products]
                content.append(temp)

            from config.upload_config.upload_config import UploadConfig
            path = UploadConfig.SERVER_ERP_FIle + date_time + ".xls"
            new_date_time = date_time.replace(u'-', u'年') + u'月'
            StatictisStatementOp.business_statictis(title, content, new_date_time, filename=path)
            result = send_file(path)
            os.remove(path)
            filename = u'旗舰店业绩统计.xls'
        except CodeError as e:
            result = e.json_value()
            return  tools.en_return_data(json.dumps(result))
        except Exception as e:
            print traceback.format_exc()
            result = {'code': ServiceCode.exception_op, 'msg': u'服务器错误'}
            return tools.en_return_data(json.dumps(result))
        else:
            return tools.en_return_execl(result, filename)


add_url.add_url(u"业绩统计", "shop_manage.ShopSaleMgt", add_url.TYPE_ENTRY, shop_manage_prefix,
                shop_manage, '/sale_performance/', 'SalePerformance', SalePerformanceView.as_view('SalePerformance'), 50, methods=['GET'])

add_url.add_url(u"业绩统计搜索", "shop_manage.SalePerformance", add_url.TYPE_FEATURE, shop_manage_prefix,
                shop_manage, '/sale_perfor_search/', 'SalePerforSearch', SalePerforSearchView.as_view('SalePerforSearch'), methods=['POST'])

add_url.add_url(u"明细单品", "shop_manage.SalePerformance", add_url.TYPE_FEATURE, shop_manage_prefix,
                shop_manage, '/detail_product/', 'DetailProduct', DetailProductView.as_view('DetailProduct'), methods=['POST'])

add_url.add_url(u"明细套餐", "shop_manage.SalePerformance", add_url.TYPE_FEATURE, shop_manage_prefix,
                shop_manage, '/detail_Setmeal/', 'DetailSetmeal', DetailSetmealView.as_view('DetailSetmeal'), methods=['POST'])

add_url.add_url(u'业绩统计报表', "shop_manage.SalePerformance", add_url.TYPE_FEATURE, shop_manage_prefix,
                shop_manage, '/sale_performance/statement/', 'SalePerformance_Statement',
                SalePerformance_Statement.as_view('SalePerformance_Statement'), methods=['GET'])


