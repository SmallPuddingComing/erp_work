#/usr/bin/python
#-*- coding:utf-8 -*-

'''
@function : 销售模块混合op
Created on : 2016-10-10
'''

import traceback
from sqlalchemy import func, and_, or_
from operator import itemgetter
import heapq

from data_mode.hola_flagship_store.control_base.controlBase import ControlEngine
from data_mode.hola_flagship_store.base_op.sale_product_statistic import ProductSaleStatisticOp

class SaleStatisticFlag:
    #仓库类型

    CategoryType = -1           #商品直属分类(不屬於主機類（堅果投影儀類）的其它類)
    product_num = 10           #商品銷售排名前product_num的商品
    store_num = 10             #店鋪商品銷售排名前store_num的店鋪
    product_everystore = 5      #同一商品在不同店鋪銷售排名前product_everystore的店鋪
    store_everyproduct = 5              #同一個店鋪不同商品銷售排名前store_everyproduct的商品
    product_trendsale = 3       #默認統計銷售趨勢銷量排名前product_trendsale的商品
    store_trendsale = 3         #銷售趨勢統計中某商品銷量排名靠前的前store_trendsale店鋪
    IncreaseType = 1            #排名上升
    DecreaseType = 2            #排名下降
    SameType = 3                #排名不變
    NoCompareType = 0           #無比較對象



class ShopSaleStatisticOp(ControlEngine):
    """
    s商品销量统计接口类
    """

    def __init__(self):
        ControlEngine.__init__(self)


    def get_product_name(self, product_id):
        """
        :param product_id: 商品类型id
        :return:str 商品名称
        """
        from control_center.shop_manage.good_info_manage.control.mixOp import HolaWareHouse
        hola_warehouse = HolaWareHouse()
        product_dict = hola_warehouse.get_product_info(product_id)

        product_name=None
        if product_dict:
            product_name = product_dict['product_name']
        else:
            raise ValueError(u"输入的商品id为%d的商品资料有误",product_id)

        return product_name


    def get_saleproduct_order(self,start_time, stop_time=None, category_id=None, product_num=None, store_num=None):
        statistic_op = ProductSaleStatisticOp()

        other_product_list_data = []
        # product_list_data = statistic_op.get_order_product_info(start_time, stop_time,category_id, product_num)
        product_list_data = statistic_op.get_order_product_info(start_time, stop_time,category_id)
        store_list_data = statistic_op.get_store_product_info(start_time, stop_time, None,store_num)

        if product_num is None:
            if category_id is not None:
                # other_product_list_data = statistic_op.get_order_product_info(start_time, stop_time, SaleStatisticFlag.CategoryType, product_num)
                other_product_list_data = statistic_op.get_order_product_info(start_time, stop_time, SaleStatisticFlag.CategoryType)
        else:
            if category_id is not None and len(product_list_data)<product_num:
                # other_product_list_data = statistic_op.get_order_product_info(start_time, stop_time, SaleStatisticFlag.CategoryType, product_num)
                other_product_list_data = statistic_op.get_order_product_info(start_time, stop_time, SaleStatisticFlag.CategoryType)

        total_product_datalist = product_list_data + other_product_list_data

        #2016-11-1 cq
        #将total_product_datalist中具有相同prodcut_id的数据的count进行相加，但实现并不做排序，
        # product_list_data是按主机类别降序排序的结果，other_product_list_data是按配件类别降序排序后的结果
        temp_data_list = []
        for product_dict in total_product_datalist:
            if temp_data_list:
                temp_true = [product_dict['product_id']==temp['product_id'] for temp in temp_data_list]
                if sum(temp_true) == 0:#没有重复
                    temp_data_list.append(product_dict)
                else:
                    #找出temp_data_list中哪个索引位置对应的字典重复了，并将结果进行累加
                    idx = temp_true.index(True)
                    temp_data_list[idx]['count'] += product_dict['count']
            else:
                temp_data_list.append(product_dict)

        if product_num is not None:
            if len(temp_data_list)>=product_num:
                product_list = temp_data_list[:product_num]
                sort_product_datalist = sorted(product_list, key=lambda s: s['count'], reverse=True)
            else:
                sort_product_datalist = sorted(temp_data_list, key=lambda s: s['count'], reverse=True)
        else:
            sort_product_datalist = sorted(temp_data_list, key=lambda s: s['count'], reverse=True)


         # sort_product_datalist = sorted(temp_data_list, key=lambda s: s['count'], reverse=True)
        # sort_product_datalist = sorted(total_product_datalist, key=lambda s: s['count'], reverse=True)

        sort_store_datalist = sorted(store_list_data, key=lambda s: s['count'], reverse=True)

        return (sort_product_datalist, sort_store_datalist)

    def get_saleproduct_info(self, product_count_list, product_increase_list, saletotal):
        statistic_op = ProductSaleStatisticOp()
        ratio_list = statistic_op.get_product_ratio(product_count_list, saletotal)

        all_product_list = []

        for idx, product in enumerate(product_count_list):
            temp_dict = {}
            product_name = self.get_product_name(product['product_id'])
            temp_dict['id'] = product['product_id']
            temp_dict['name'] = product_name
            temp_dict['is_increase'] = product_increase_list[idx]['is_increase']
            temp_dict['ratio'] = ratio_list[idx]['ratio']
            temp_dict['sale_volume'] = product['count']

            all_product_list.append(temp_dict)

        return all_product_list

    def get_salestore_info(self, store_count_list, store_increase_list, saletotal):
        from control_center.flagship_manage.sale_manage.control.SearchProductInfo_Op import SearchInfo_Op
        statistic_op = ProductSaleStatisticOp()
        ratio_list = statistic_op.get_store_product_ratio(store_count_list, saletotal)

        all_store_list = []
        searchinfo_op = SearchInfo_Op()

        for idx, store in enumerate(store_count_list):
            temp_dict = {}
            temp_dict['id'] = store['store_id']
            temp_dict['name'] = searchinfo_op.get_store_name(store['store_id'])
            temp_dict['is_increase'] = store_increase_list[idx]['is_increase']
            temp_dict['ratio'] = ratio_list[idx]['ratio']
            temp_dict['sale_volume'] = store['count']

            all_store_list.append(temp_dict)

        return all_store_list

    def get_productinfo_by_productid(self,product_dict, strcurdate, stop_time, pie_num):
        from control_center.flagship_manage.sale_manage.control.SearchProductInfo_Op import SearchInfo_Op
        searchinfo_op = SearchInfo_Op()

        product_statistic_op = ProductSaleStatisticOp()
        product_lists = product_statistic_op.get_store_product_info(strcurdate, stop_time, product_dict['product_id'],pie_num)
        product = {'name':"", 'data':[]}

        product['name'] = self.get_product_name(product_dict['product_id'])

        part_product_count = 0
        part_ratio_count = 0
        store_list = []
        for one_product in product_lists:
            temp_dict = {}
            temp_dict['name'] = searchinfo_op.get_store_name(one_product['store_id'])
            temp_dict['sale_num'] = one_product['count']
            temp_dict['ratio'] = str(round(100.0*one_product['count']/product_dict['count'], 1)) + '%'
            part_product_count += one_product['count']
            part_ratio_count += round(100.0*one_product['count']/product_dict['count'], 1)
            store_list.append(temp_dict)
        if part_product_count < product_dict['count']:
            temp_other={}
            temp_other['name'] = u"其它"
            temp_other['sale_num'] = product_dict['count'] - part_product_count
            temp_other['ratio'] = str(round(100.0 - part_ratio_count, 1)) + '%'
            store_list.append(temp_other)
        product['data'] = store_list

        return product

    def get_productinfo_by_storeid(self,store_dict, strcurdate, stop_time, pie_num):
        from control_center.flagship_manage.sale_manage.control.SearchProductInfo_Op import SearchInfo_Op
        searchinfo_op = SearchInfo_Op()

        product_statistic_op = ProductSaleStatisticOp()

        store_lists = product_statistic_op.get_product_instore_info(store_dict['store_id'],strcurdate,stop_time,pie_num)
        store = {'name':"", 'data':[]}
        store['name'] = searchinfo_op.get_store_name(store_dict['store_id'])
        part_product_count = 0
        part_ratio_count = 0.0
        product_list = []
        for one_store in store_lists:
            temp_dict = {}
            temp_dict['name'] = self.get_product_name(one_store['product_id'])
            temp_dict['sale_num'] = one_store['count']
            temp_dict['ratio'] = str(round(100.0*one_store['count']/store_dict['count'], 1)) + '%'
            part_product_count += one_store['count']
            part_ratio_count += round(100.0*one_store['count']/store_dict['count'], 1)
            product_list.append(temp_dict)
        if part_product_count<store_dict['count']:
            temp_other={}
            temp_other['name'] = u"其它"
            temp_other['sale_num'] = store_dict['count'] - part_product_count
            temp_other['ratio'] = str(round(100.0 - part_ratio_count, 1)) + '%'
            product_list.append(temp_other)
        store['data'] = product_list

        return store

    def get_product_sale_tend(self,product_list, start_time, stop_time, store_num):
        from control_center.flagship_manage.sale_manage.control.SearchProductInfo_Op import SearchInfo_Op
        searchinfo_op = SearchInfo_Op()
        product_statistic_op = ProductSaleStatisticOp()
        #分别获取每个商品在时间范围内没有的统计情况
        sale_info = []
        for product in product_list:
            temp_dict = {}
            temp_dict['product_id'] = product
            temp_dict['p_name'] = self.get_product_name(product)
            #获取指定product_id，在start_time至stop_time时间范围内每月的销量统计（升序排序后的结构）
            product_datas = product_statistic_op.get_product_allstore(product, start_time, stop_time)
            #获取指定product_id,指定年月该商品在销量最后的几个店铺的销量情况(按照商品销量降序排序结构)
            store_product_datas = product_statistic_op.get_product_partstore(product, start_time, store_num)
            product_data = []
            for p_data in product_datas:
                temp_data_dict ={}
                temp_data_dict['date'] = p_data['date']
                temp_data_dict['product_total'] = p_data['count']
                sale_list = []
                for store_data in store_product_datas:
                    temp_store ={}
                    temp_store['flagship_id'] = store_data['store_id']
                    temp_store['flagship_name'] = searchinfo_op.get_store_name(store_data['store_id'])
                    temp_store['flagship_num'] = store_data['count']
                    sale_list.append(temp_store)

                temp_data_dict['sale_list'] = sale_list
                product_data.append(temp_data_dict)

            temp_dict['product_data'] = product_data
            sale_info.append(temp_dict)

        return sale_info

    def get_all_saleproduct_name(self):
        from control_center.shop_manage.good_info_manage.control.mixOp import HolaWareHouse
        hola_warehouse = HolaWareHouse()
        product_id_list = hola_warehouse.get_all_product_id()
        product_info = []
        for product_id in product_id_list:
            temp_dict = {}
            temp_dict['product_id'] = product_id
            temp_dict['product_name'] = self.get_product_name(product_id)
            product_info.append(temp_dict)

        return product_info

