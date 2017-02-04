#-*-coding:utf-8-*-
import os
from public.exception.custom_exception import CodeError
from config.service_config.returncode import ServiceCode
from flask import session
from flask.views import MethodView
from flask import request, send_file
from flask import jsonify
from flask import json
from pprint import pprint
from public.function import tools
import traceback
from control_center.shop_manage import shop_manage,shop_manage_prefix
from control_center.admin import add_url
import time
from data_mode.hola_flagship_store.base_op.sale_product_statistic import ProductSaleStatisticOp
from data_mode.hola_flagship_store.base_op.sale_product_statistic import get_lastmonth
from control_center.shop_manage.shop_sale_statistics.control.mixOp import ShopSaleStatisticOp
from control_center.shop_manage.shop_sale_statistics.control.mixOp import SaleStatisticFlag
from control_center.shop_manage.good_info_manage.control.mixOp import Dict_Categorgory_touyingyi



class ShopSaleMgt(MethodView):

    def get(self):
        return tools.en_render_template('storeManage/warehouse/warehouse_entry.html')

class ProductRankView(MethodView):
    """
        销售统计-排名统计页面跳转接口
    """
    def get(self):
        return_data = None
        try:
            # date = request.values.get('date','', str)

            curdate = [time.localtime()[0], time.localtime()[1]]
            strcurdate = (str(curdate[0])).zfill(4) + "-" + (str(curdate[1])).zfill(2)
            strlastdate = get_lastmonth(curdate)

            shop_statistic_op = ShopSaleStatisticOp()
            #获取当前月商品销量靠前的商品信息和店铺信息
            (cur_product_list, cur_store_list) = shop_statistic_op.get_saleproduct_order(strcurdate,None,Dict_Categorgory_touyingyi['id'],SaleStatisticFlag.product_num,SaleStatisticFlag.store_num)
            #获取上月商品销量靠前的商品信息和店铺信息
            (last_product_list, last_store_list) = shop_statistic_op.get_saleproduct_order(strlastdate,None,Dict_Categorgory_touyingyi['id'],SaleStatisticFlag.product_num,SaleStatisticFlag.store_num)

            product_statistic_op = ProductSaleStatisticOp()
            #获取当前月商品销量与上月相比的排名升降比较
            product_increase_list = product_statistic_op.get_proudctrank_increase_flag(cur_product_list, last_product_list)
            #获取当前月店铺商品销量与上月相比的排名升降比较
            store_increase_list = product_statistic_op.get_storerank_increase_flag(cur_store_list, last_store_list)
            #获取查询时间内所有店铺的所有商品销量的总和
            saletotal = product_statistic_op.get_sale_product_total(strcurdate)

            allproduct = shop_statistic_op.get_saleproduct_info(cur_product_list,product_increase_list,saletotal)
            allstore = shop_statistic_op.get_salestore_info(cur_store_list, store_increase_list, saletotal)

            product = {'name':"", 'data':[]}
            store = {'name':"", 'data':[]}
            if cur_product_list:
                product = shop_statistic_op.get_productinfo_by_productid(cur_product_list[0],strcurdate,None,SaleStatisticFlag.product_everystore)
            if cur_store_list:
                store = shop_statistic_op.get_productinfo_by_storeid(cur_store_list[0],strcurdate,None,SaleStatisticFlag.store_everyproduct)
        except CodeError as e:
            return_data = jsonify(e.json_value())
        except Exception as e:
            print traceback.format_exc(e)
            return_data = jsonify(
                {'code': ServiceCode.service_exception, 'msg': u"服务器失败"})
        else:
            datas = {
                'code':ServiceCode.success,
                'date':strcurdate,
                'allproduct':allproduct,
                'product':product,
                'allstore':allstore,
                'store':store
            }
            return_data = json.dumps(datas)
        finally:
            return tools.en_render_template('salegoods/tradeRank.html', result=return_data)


class ProductRankSearchView(MethodView):
    """
    销售统计-排名统计时间搜索接口
    """
    def post(self):
        return_data = None
        try:
            strcurdate = request.values.get('date','', str)
            strlastdate = request.values.get('predate','', str)

            shop_statistic_op = ShopSaleStatisticOp()
            #获取当前月商品销量靠前的商品信息和店铺信息
            (cur_product_list, cur_store_list) = shop_statistic_op.get_saleproduct_order(strcurdate,None,Dict_Categorgory_touyingyi['id'],SaleStatisticFlag.product_num,SaleStatisticFlag.store_num)
            #获取上月商品销量靠前的商品信息和店铺信息
            (last_product_list, last_store_list) = shop_statistic_op.get_saleproduct_order(strlastdate,None,Dict_Categorgory_touyingyi['id'],SaleStatisticFlag.product_num,SaleStatisticFlag.store_num)

            product_statistic_op = ProductSaleStatisticOp()
            #获取当前月商品销量与上月相比的排名升降比较
            if strcurdate:
                product_increase_list = product_statistic_op.get_proudctrank_increase_flag(cur_product_list, last_product_list)
                #获取当前月店铺商品销量与上月相比的排名升降比较
                store_increase_list = product_statistic_op.get_storerank_increase_flag(cur_store_list, last_store_list)
            else:
                product_increase_list=[]
                store_increase_list = []

                for temp_pro in cur_product_list:
                    temp_dict={}
                    temp_dict['product_id'] = temp_pro['product_id']
                    temp_dict['is_increase'] = SaleStatisticFlag.NoCompareType
                    product_increase_list.append(temp_dict)

                for temp_store in cur_store_list:
                    temp_dict = {}
                    temp_dict['store_id'] = temp_store['store_id']
                    temp_dict['is_increase'] = SaleStatisticFlag.NoCompareType
                    store_increase_list.append(temp_dict)

            #获取查询时间内所有店铺的所有商品销量的总和
            saletotal = product_statistic_op.get_sale_product_total(strcurdate)

            allproduct = shop_statistic_op.get_saleproduct_info(cur_product_list,product_increase_list,saletotal)
            allstore = shop_statistic_op.get_salestore_info(cur_store_list, store_increase_list, saletotal)


            product = {'name':"", 'data':[]}
            store = {'name':"", 'data':[]}
            if cur_product_list:
                product = shop_statistic_op.get_productinfo_by_productid(cur_product_list[0],strcurdate,None,SaleStatisticFlag.product_everystore)
            if cur_store_list:
                store = shop_statistic_op.get_productinfo_by_storeid(cur_store_list[0],strcurdate,None,SaleStatisticFlag.store_everyproduct)
        except CodeError as e:
            return_data = jsonify(e.json_value())
        except Exception as e:
            print traceback.format_exc(e)
            return_data = jsonify(
                {'code': ServiceCode.service_exception, 'msg': u"服务器失败"})
        else:
            datas = {
                'code':ServiceCode.success,
                'date':strcurdate,
                'allproduct':allproduct,
                'product':product,
                'allstore':allstore,
                'store':store
            }
            return_data = json.dumps(datas)
        finally:
            return tools.en_return_data(return_data)

class PerProductRankView(MethodView):
    """
    销售统计-排名统计根据任意商品id查询在各店铺销售情况接口
    """
    def post(self):
        return_data = None
        try:
            p_id = request.values.get('id', int)
            date = request.values.get('date','', str)

            product_statistic_op = ProductSaleStatisticOp()
            shop_statistic_op = ShopSaleStatisticOp()

            product_dict = product_statistic_op.get_salecount_by_productid(p_id,date,None)

            datas = shop_statistic_op.get_productinfo_by_productid(product_dict,date, None, SaleStatisticFlag.product_everystore)
        except CodeError as e:
            return_data = jsonify(e.json_value())
        except Exception as e:
            print traceback.format_exc(e)
            return_data = jsonify(
                {'code': ServiceCode.service_exception, 'msg': u"服务器失败"})
        else:
            datas['code'] = ServiceCode.success
            datas['date'] = date
            return_data = json.dumps(datas)
        finally:
            return tools.en_return_data(return_data)

class ProductRankStoreView(MethodView):
    """
    销售统计-排名统计根据任意店铺id统计店铺内个商品销量情况
    """
    def post(self):
        return_data = None
        try:
            store_id = request.values.get('id',int)
            date = request.values.get('date','', str)

            product_statistic_op = ProductSaleStatisticOp()
            shop_statistic_op = ShopSaleStatisticOp()

            store_dict = product_statistic_op.get_salecount_by_storeid(store_id,date,None)
            datas = shop_statistic_op.get_productinfo_by_storeid(store_dict,date,None,SaleStatisticFlag.store_everyproduct)
        except CodeError as e:
            return_data = jsonify(e.json_value())
        except Exception as e:
            print traceback.format_exc(e)
            return_data = jsonify(
                {'code': ServiceCode.service_exception, 'msg': u"服务器失败"})
        else:
            datas['code'] = ServiceCode.success
            datas['date'] = date
            return_data = json.dumps(datas)
        finally:
            return tools.en_return_data(return_data)


class ProductRankExportData(MethodView):
    def get(self):
        from control_center.shop_manage.shop_sale_statistics.control.statement import StatictisStatementOp
        from data_mode.hola_flagship_store.base_op.sale_product_rangedate_statistic import ProductSaleRangeDateStatisticOp
        from data_mode.hola_warehouse.control_base.controlBase import ControlEngine
        from data_mode.hola_flagship_store.mode.ship_model.flagship_store_info import FlagShipStoreInfo
        from data_mode.hola_warehouse.model.base_product_unit import BaseProductUnit
        import re
        import xlwt
        try:
            # 获取请求参数
            date_time = request.values.get('datetime', None)
            if date_time is None or date_time == u'':
                raise CodeError(ServiceCode.params_error, u'请选择时间！')

            cle = re.compile(r'^\d{4}-\d{2}$')
            if not re.match(cle, date_time):
                raise CodeError(ServiceCode.params_error, u'上送的时间格式不正确')

            # 创建报表
            workbook = xlwt.Workbook()
            sheet2 = workbook.add_sheet(u'坚果旗舰店设备销量排名')
            sheet1 = workbook.add_sheet(u'坚果旗舰店销量排名')

            # 第一个工作簿--坚果旗舰店销量排名
            pro_sale_range = ProductSaleRangeDateStatisticOp()
            data = pro_sale_range.get_store_datas(date_time)
            sheet1.write(0, 0, u'坚果旗舰店销量排名')
            field_list = [u'名次', u'销售渠道', u'占总销量', u'总销量']
            control_engien = ControlEngine()
            products = control_engien.controlsession.query(BaseProductUnit.id,
                                                           BaseProductUnit.name).order_by(BaseProductUnit.id).all()
            if len(products):
                field_list += [x[1] for x in products]

            for content in data:
                StatictisStatementOp.sale_rank(sheet1,
                                               content['start_date'],
                                               content['stop_date'],
                                               u'坚果旗舰店设备销量排名',
                                               field_list,
                                               content['data'])

            # 第二个工作簿--坚果旗舰店销量排名
            data = pro_sale_range.get_product_datas(date_time)
            sheet2.write(0, 0, u'坚果旗舰店设备销量排名')
            field_list = [u'名次', u'商品名称', u'占总销量', u'总销量']
            flagships = pro_sale_range.controlsession.query(FlagShipStoreInfo.name).order_by(FlagShipStoreInfo.id).all()
            if len(flagships):
                field_list += [x[0] for x in flagships]

            print("field_list:", field_list)
            for content in data:
                StatictisStatementOp.sale_rank(sheet2,
                                               content['start_date'],
                                               content['stop_date'],
                                               u'坚果旗舰店销量排名',
                                               field_list,
                                               content['data'])

            from config.upload_config.upload_config import UploadConfig
            path = UploadConfig.SERVER_ERP_FIle + date_time + ".xls"
            # path = u'F:/test.xls'
            workbook.save(path)
            result = send_file(path)
            os.remove(path)
            filename = u'旗舰店排名统计.xls'
        except CodeError as e:
            result = e.json_value()
            return  tools.en_return_data(json.dumps(result))
        except Exception as e:
            print traceback.format_exc()
            result = {'code': ServiceCode.exception_op, 'msg': u'服务器错误'}
            return tools.en_return_data(json.dumps(result))
        else:
            return tools.en_return_execl(result, filename)



add_url.add_url(u"数据统计", "shop_manage.ShopManageView", add_url.TYPE_ENTRY, shop_manage_prefix,
                shop_manage, '/shopsale_mgt/', 'ShopSaleMgt', ShopSaleMgt.as_view('ShopSaleMgt'), 60,methods=['GET','POST'])

add_url.add_url(u'排名统计','shop_manage.ShopSaleMgt',add_url.TYPE_ENTRY,shop_manage_prefix,shop_manage,
                '/product_rank/','product_rank',ProductRankView.as_view('product_rank'), 70, methods=['GET'])

add_url.add_url(u'排名搜索', 'shop_manage.product_rank', add_url.TYPE_FEATURE, shop_manage_prefix,shop_manage,
                '/productrank_search/','productrank_search',ProductRankSearchView.as_view('productrank_search'), methods=['POST'])

add_url.add_url(u"商品在店铺排名", 'shop_manage.ShopManageView',add_url.TYPE_FEATURE,shop_manage_prefix,shop_manage,
                '/product_store_rank/', 'product_store_rank',PerProductRankView.as_view('product_store_rank'), methods=['POST'] )

add_url.add_url(u"店铺内商品排名", 'shop_manage.product_rank',add_url.TYPE_FEATURE,shop_manage_prefix,shop_manage,
                '/store_product_rank/', 'store_product_rank',ProductRankStoreView.as_view('store_product_rank'), methods=['POST'] )

add_url.add_url(u"排名统计报表下载", 'shop_manage.product_rank', add_url.TYPE_FEATURE, shop_manage_prefix, shop_manage,
                '/product_rank_export_data/', 'product_rank_export_data',
                ProductRankExportData.as_view('product_rank_export_data'),
                methods=['GET'])