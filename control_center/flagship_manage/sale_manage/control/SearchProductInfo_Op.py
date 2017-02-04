#/usr/bin/python
#-*- coding:utf-8 -*-
#########################################################
#    Copyright(c) 2000-2013 JmGO Company
#    All rights reserved.
#
#    文件名 :   sale_order_detail.py
#  电子邮箱 :   qcheng@jmgo.com
#    日期   :   2016/09/08 14:06:17
#
#    描述   :  套餐销售订单详情数据模型
#

import datetime
import types
import traceback
from control_center.flagship_manage.flagship_info_manage.control.mixOp import FlagShipOp
from control_center.flagship_manage.warehouse_manage.control.whouse_product_info_op import WhouseProductInfoOp
from sqlalchemy import func
from sqlalchemy.exc import SQLAlchemyError

from config.service_config.returncode import ServiceCode
from data_mode.hola_flagship_store.control_base.controlBase import ControlEngine
from control_center.flagship_manage.flagship_info_manage.control.flagship_op import FlagShipOp as getFlagShipOp
from control_center.flagship_manage.warehouse_manage.control.in_out_warehouse_op import InOutWarehouseOp
from control_center.shop_manage.good_info_manage.control.mixOp import HolaWareHouse
from control_center.shop_manage.good_set_manage.control.setmealOp import SetMealOp
from data_mode.hola_flagship_store.mode.sale_mode.customer_info import CustomerInfo
from data_mode.hola_flagship_store.mode.sale_mode.sale_order import SaleOrder
from data_mode.hola_flagship_store.mode.sale_mode.sale_order_detail import SaleOrderDetail
from data_mode.hola_flagship_store.mode.sale_mode.set_product_record import SetProductRecord
from data_mode.hola_flagship_store.mode.sale_mode.set_record_info import SetRecordInfo
from data_mode.hola_flagship_store.mode.ship_model.flagship_store_info import FlagShipStoreInfo
from data_mode.hola_flagship_store.mode.warehouse_mode.warehouse_manage import WarehouseType
from data_mode.user_center.control.mixOp import MixUserCenterOp
from config.share.share_define import *


class SearchInfo_Op(ControlEngine):
    """
    商品信息查询
    """
    def __init__(self):
        ControlEngine.__init__(self)

    def get_product_info(self, store_id, p_type, stype, svalue, curPage, pageCounts):
        """
        :param store_id:        店铺id
        :param p_type:            搜索类型（1：搜索单品信息  2：搜索套餐信息  3：搜索赠品信息
        :param stype:           搜索类型：1：商品名称关键字  2：商品编码  3：套餐名称关键字
        :param svalue:         搜索条件：商品编码关键字 or 商品编码（完全匹配）
        :param curPage:         当前页的页数
        :param pageCounts:      每页显示的记录数
        :return:                根据给定的参数搜索相应的商品信息
        """
        total = 0
        data = []
        if p_type==1:     #表示搜索单品信息
            data, total = self.get_sproduct_info(long(store_id.encode()), stype, svalue, curPage, pageCounts, False)
        elif p_type==2:   #表示搜索套餐信息
            data, total = self.get_set_product_info(long(store_id.encode()), stype, svalue, curPage, pageCounts)
        elif p_type==3:    #表示搜索赠品信息
            data, total = self.get_sproduct_info(long(store_id.encode()), stype, svalue, curPage, pageCounts, True)

        return total, data


    def get_store_name(self, store_id):
        """
        :param store_id:        店铺id
        :return:                返回店铺名称
        """
        f_op = getFlagShipOp()
        store_info = f_op.get_flagship_info_by_flagship_id(store_id)  #store_info是字典格式，flagship_store_info的to_json()转化而来
        if store_info: #表示store_info不为空字典时：
            return store_info['name']
        else:
            return ''


    def get_sproduct_info(self, store_id, stype, svalue, page, per_page, is_gift):
        """
        :param store_id: 旗舰店ID
        :param stype: 搜索类型 (1：商品名称关键字 2：商品编码（完全匹配）)
        :param svalue: 搜索内容，根据stype判断
        :param page: 分页的当前页数
        :param per_page: 每页显示的记录数
        :param is_gift: 是否为赠品（True or False (还是数字1和0)）
        :return: list(dict)
        """
        try:
            holawarehouse = HolaWareHouse()
            datas,total = holawarehouse.get_product_by_gift(store_id, stype, svalue, page, per_page, is_gift)
            #根据商品编码和店铺id搜索该商品对应的库存量
            pdata = []
            # serial_flag = False
            for data in datas:
                data['p_count'] = 0
                pdata.append(data)
                holawarehouse = HolaWareHouse()
                product_id = holawarehouse.getProIdByGoodCode(data['p_code'])
                data['product_id'] = product_id
                if product_id is not None:
                    # product_id = product_id_list[0]
                    #根据商品id获取相应的库存量
                    wh_info_op = WhouseProductInfoOp()
                    json_code = wh_info_op.get_product_count(store_id ,product_id)

                    serial_flag = wh_info_op.get_serialno_flag(store_id, product_id, WarehouseType.inventory_warehouse)
                    data['flag'] = serial_flag

                    if json_code['code'] ==ServiceCode.service_exception:
                        data['p_count'] = 0
                    elif json_code['code'] == ServiceCode.success:
                        data['p_count'] = json_code['amount']

            return pdata, total
        except Exception, ex:
            raise

    def get_set_product_info(self,store_id, stype, svalue, page, per_page):
        """
        :param store_id: 旗舰店ID
        :param stype: 搜索类型 (1：商品名称关键字 2：商品编码（完全匹配） 3:套餐名称关键字)
        :param svalue: 搜索内容，根据stype判断
        :param page: 分页的当前页数
        :param per_page: 每页显示的记录数
        :return: list(dict)
        """
        setmealop = SetMealOp()
        datas, total = setmealop.get_setmeal_for_sale(store_id, stype, svalue, page, per_page)

        pdata = []
        p_dict ={}
        for set_data in datas:
            set_contents = []
            p_dict['set_id'] = set_data['set_id']
            p_dict['name'] = set_data['name']
            p_dict['price'] = set_data['price']
            p_dict['floor_price'] = set_data['floor_price']
            set_contents = set_data['set_content']

            p_content = []
            for set_content in set_contents:
                set_content['p_count'] = 0
                p_content.append(set_content)

                holawarehouse = HolaWareHouse()
                product_id = holawarehouse.getProIdByGoodCode(set_content['p_code'])
                set_content['product_id'] = product_id

                if product_id is not None:
                #根据商品id获取相应的库存量
                    wh_info_op = WhouseProductInfoOp()
                    json_code = wh_info_op.get_product_count(store_id ,product_id)

                    serial_flag = wh_info_op.get_serialno_flag(store_id, product_id, WarehouseType.inventory_warehouse)
                    set_content['flag'] = serial_flag

                    if json_code['code'] ==ServiceCode.service_exception:
                        set_content['p_count'] = 0
                    elif json_code['code'] == ServiceCode.success:
                        set_content['p_count'] = json_code['amount']

            p_dict['set_content'] = p_content

            pdata.append(p_dict)
            p_dict = {}

        return pdata, total


    def get_order_detail_info(self, orderNo):
        """
        :param orderNo: 订单号
        :return:该订单后对应的订单信息详情
        """
        #订单表中查询基本信息
        try:
            orderNo_info = {}
            money_info = {}
            customer_info = {}
            sendinfo = {}
            invoice_info = {}
            mixusercenterop =MixUserCenterOp()

            order_datas = self.controlsession.query(SaleOrder).filter_by(orderNo=orderNo).first()
            if isinstance(order_datas, types.NoneType):
                #订单信息
                orderNo_info['storeName'] = ''
                orderNo_info['orderNo'] = '' #销售门店

                orderNo_info['salesman'] = ''
                orderNo_info['cashier'] = ''
                orderNo_info['saletime'] = '' #销售时间
                orderNo_info['desc'] = ''                             #订单备注

                if isinstance(orderNo_info['desc'], types.NoneType):
                    orderNo_info['desc'] = u"无"

                #付款信息
                money_info['payType'] = ''
                                                           #支付方式
                money_info['orderPrice'] = ''                           #订单金额
                money_info['actPrice'] = ''                         #实收金额
                money_info['setPrice'] = ''                         #应收金额
                money_info['change']=''                               #找零

                sendinfo['sendType'] = ''      #交货方式
                sendinfo['sendState'] = ''
                sendinfo['outno']= ''              #出库单号
            else:
                order_json_data = order_datas.to_json()

                #订单信息
                orderNo_info['storeName'] = self.get_store_name(order_json_data['store_id'])
                orderNo_info['orderNo'] = order_json_data['orderNo'] #销售门店
                seltDate = order_json_data['seltDate']
                seltTime = order_json_data['seltTime']
                orderNo_info['saletime'] = seltDate + u" " + seltTime[0:5]  #20160927cq新增 销售时间
                salesman_num = order_json_data['salesman']                         #促销员工号
                cashier_num = order_json_data['Rem1']                              #收银员工号
                #根据工号查询人名
                # salesName = self.get_salesmen_name(salesman_num)
                salesName = mixusercenterop.get_salesmen_name(salesman_num)         #促销员姓名
                if salesName==None:
                    salesName = ''

                cashierName = mixusercenterop.get_salesmen_name(cashier_num)                   #收营员姓名

                if cashierName==None:
                    cashierName=u'管理员'

                orderNo_info['salesman'] = salesman_num + u' ' + salesName
                orderNo_info['cashier'] = cashier_num + u' ' + cashierName

                orderNo_info['desc'] = order_json_data['describe'] if order_json_data['describe'] is not None else ""                           #订单备注

                if isinstance(orderNo_info['desc'], types.NoneType):
                    orderNo_info['desc'] = u"无"
                elif len(orderNo_info['desc'].strip())==0:
                    orderNo_info['desc'] = u"无"

                #付款信息
                payType = order_datas.newPayType
                if isinstance(payType, types.NoneType):
                    money_info['payType'] = ''
                else:
                    money_info['payType'] = payType.name
                                                           #支付方式
                money_info['orderPrice'] = order_json_data['Rem2'] /COVERT_DATA_TO_MONEY_NUMBER        #订单金额
                money_info['actPrice'] = order_json_data['actPrice'] /COVERT_DATA_TO_MONEY_NUMBER      #实收金额
                money_info['setPrice'] = order_json_data['setPrice'] /COVERT_DATA_TO_MONEY_NUMBER      #应收金额
                money_info['change']=order_json_data['change'] / COVERT_DATA_TO_MONEY_NUMBER           #找零

                sendinfo['sendType'] = order_json_data['sendType']      #交货方式
                sendinfo['sendState'] = order_json_data['sendState']
                sendinfo['outno']= order_json_data['Rem4']              #出库单号


            #顾客信息表中查询配送信息
            customer_datas = self.controlsession.query(CustomerInfo).filter_by(orderNo=orderNo).first()
            if isinstance(customer_datas, types.NoneType):
                customer_info['name'] = ''      #买家姓名
                customer_info['tel'] = ''
                customer_info['sex'] = ''
                customer_info['addr'] = ''
                customer_info['daddr'] = ''
                sendinfo['recvName'] = ''      #收货人
                sendinfo['recvtel'] = ''        #收人人手机号
                province = ''
                city = ''
                addr = ''
                sendinfo['recvaddr'] = ''.join([province, city, addr])
                invoice_info['in_head'] = ''               #发票抬头
                invoice_info['info'] = u"不需要"
                invoice_info['content'] = ''
            else:
                customer_json_data = customer_datas.to_json()
                customer_info['name'] = customer_json_data['name'] if customer_json_data['name'] is not None else ""     #买家姓名
                customer_info['tel'] = customer_json_data['tel'] if customer_json_data['tel'] is not None else ""
                customer_info['sex'] = customer_json_data['sex'] if customer_json_data['sex'] is not None else ""
                
                cus_prov = customer_json_data['buy_prov'] if customer_json_data['buy_prov'] is not None else ""
                cus_city = customer_json_data['buy_city'] if customer_json_data['buy_city'] is not None else ""
                customer_info['addr'] = ''.join([cus_prov, cus_city])
                customer_info['daddr'] = customer_json_data['buy_addr'] if customer_json_data['buy_addr'] is not None else ""

                #配送信息
                sendinfo['recvName'] = customer_json_data['Rem1'] if customer_json_data['Rem1'] is not None else ""     #收货人
                sendinfo['recvtel'] = customer_json_data['Rem2'] if customer_json_data['Rem2'] is not None else ""        #收人人手机号
                province = customer_json_data['province'] if customer_json_data['province'] is not None else ""
                city = customer_json_data['city'] if customer_json_data['city'] is not None else ""
                addr = customer_json_data['addr'] if customer_json_data['addr'] is not None else ""
                sendinfo['recvaddr'] = ''.join([province, city, addr])

                #发票信息
                in_state = order_json_data['Rem3']   #发票状态（01需要， 02不需要）
                if in_state.find(u'不') == -1:
                    invoice_info['info'] = u"需要发票"                                          #发票信息
                    invoice_info['in_head'] = customer_json_data['invoice_head'] if customer_json_data['invoice_head'] is not None else ""            #发票抬头
                    invoice_info['content'] = u"商品明细"                                       #发票内容
                else:
                    invoice_info['info'] = u"不需要"
                    invoice_info['in_head'] = ''
                    invoice_info['content'] = ''

            #获取非套餐信息
            product_list = self.get_saleproduct_by_orderno(orderNo)
            set_list = self.get_set_saleproduct_by_orderno(orderNo)

            datas = {
                'order':orderNo_info,
                'money':money_info,
                'customer':customer_info,
                'send':sendinfo,
                'invoice':invoice_info,
                'product': product_list,
                'set': set_list
            }

            return orderNo_info, money_info, customer_info, sendinfo, invoice_info, product_list, set_list
        except Exception, ex:
            raise

    def get_saleproduct_by_orderno(self, orderNo):
        """
        :param orderNo: 订单号
        :return: list(dict)  该订单号对应的非套餐商品信息
        """
        #统计该订单号中非套餐商品的信息
        good_datas = self.controlsession.query(SaleOrderDetail).filter(SaleOrderDetail.orderNo==orderNo).all()
        product_list = []

        for good_data in good_datas:
            product_dict = {}
            # product_dict['id'] = good_data.id               #标识
            product_dict['p_name'] = good_data.name         #商品名称
            product_dict['p_type'] = good_data.Rem1         #商品类别
            product_dict['p_sn'] = good_data.serialNo       #商品序列号（SN号）
            product_dict['p_code'] =good_data.pCode         #商品編碼

            product_dict['price'] = (good_data.price)/COVERT_DATA_TO_MONEY_NUMBER          #商品价格
            product_dict['saleprice'] = (good_data.salePrice)/COVERT_DATA_TO_MONEY_NUMBER  #商品售价

            product_dict['gift'] = good_data.state          #赠品标识

            count = 0
            if len(product_dict['p_sn'].strip()) != 0:
                count = 1
            else:
                count = self.controlsession.query(func.count(SaleOrderDetail.id)).filter_by(orderNo=orderNo, pCode=good_data.pCode, serialNo='').scalar()
                if count==0:
                    raise ValueError("The record of OrderNo. is wrong in sale_order_detail table")
            product_dict['p_count'] = count

            if product_list:
                temp_true = [product_dict==temp for temp in product_list]
                if sum(temp_true) == 0:
                    product_list.append(product_dict)
            else:
                product_list.append(product_dict)

        return product_list

    def get_set_saleproduct_by_orderno(self, orderNo):
        """
        :param orderNo:  訂單號
        :return:根據訂單號獲取套餐信息
        """
        # holawarehouse = HolaWareHouse()
        set_datas = self.controlsession.query(SetProductRecord).filter(SetProductRecord.orderNo==orderNo).all()
        set_dict = {}
        set_list = []

        for set_data in set_datas:
            #每种类型套餐解析
            #完善set_list中每个套餐的详细信息
            set_contents_list = []
            set_contents_dict = {}
            #根据orderNo.与set_meal_id搜索相应的set_content内容及内容
            set_product_datas = self.controlsession.query(SetRecordInfo).filter_by(orderNo=orderNo,set_meal_id=set_data.set_meal_id).order_by(SetRecordInfo.id.asc()).all()
            count = len(set_product_datas)/long((set_data.Rem2).encode())  #表示每个套餐内包含的商品数量

            for idx in range(len(set_product_datas)):
                # set_contents_dict['id'] = set_product_datas[idx].id
                set_contents_dict['p_name'] = set_product_datas[idx].name
                set_contents_dict['p_type'] = set_product_datas[idx].Rem2
                set_contents_dict['p_sn'] = set_product_datas[idx].serialNo
                set_contents_dict['price'] = (set_product_datas[idx].price)/COVERT_DATA_TO_MONEY_NUMBER
                set_contents_dict['p_code'] =set_product_datas[idx].pCode        #商品編碼
                set_contents_dict['saleprice'] = (set_product_datas[idx].price)/COVERT_DATA_TO_MONEY_NUMBER #商品售价
                set_contents_dict['gift'] = set_product_datas[idx].Rem1         #商品为赠品的标识
                #获取该套餐该商品在套餐内的数量
                ss = set_product_datas[idx].serialNo

                # set_contents_dict['p_count'] = 1

                if len(ss.strip()) != 0:
                    set_contents_dict['p_count'] = 1
                else:
                    # 序列号为空，将该商品在套餐内的数量累加
                    total_count = self.controlsession.query(SetRecordInfo.Rem3).filter_by(
                        orderNo=set_product_datas[idx].orderNo, set_meal_id=set_data.set_meal_id,
                        pCode=set_product_datas[idx].pCode).first()
                    set_contents_dict['p_count'] = int(total_count[0])

                if idx%count== 0 and idx!=0 :#表示套餐开始
                    set_dict['set_price'] = (set_data.price)/COVERT_DATA_TO_MONEY_NUMBER
                    set_dict['set_saleprice'] = (set_data.salePrice)/COVERT_DATA_TO_MONEY_NUMBER
                    set_dict['set_name'] = set_data.Rem1

                    #将set_contents_list中的数据进行去重处理
                    temp_contents_list = []
                    for product_dict in set_contents_list:
                        if temp_contents_list:
                            temp_true = [product_dict==temp for temp in temp_contents_list]
                            if sum(temp_true) == 0:
                                temp_contents_list.append(product_dict)
                        else:
                            temp_contents_list.append(product_dict)

                    set_dict['set_content'] = temp_contents_list


                    # set_dict['set_content'] = set_contents_list

                    set_list.append(set_dict)

                    set_contents_list = []
                    set_contents_list.append(set_contents_dict)
                    set_contents_dict = {}
                elif idx%count!=0 and idx==len(set_product_datas)-1:
                    set_dict['set_price'] = (set_data.price)/COVERT_DATA_TO_MONEY_NUMBER
                    set_dict['set_name'] = set_data.Rem1
                    set_dict['set_saleprice'] = (set_data.salePrice)/COVERT_DATA_TO_MONEY_NUMBER
                    set_contents_list.append(set_contents_dict)

                    #将set_contents_list中的数据进行去重处理
                    temp_contents_list = []
                    for product_dict in set_contents_list:
                        if temp_contents_list:
                            temp_true = [product_dict==temp for temp in temp_contents_list]
                            if sum(temp_true) == 0:
                                temp_contents_list.append(product_dict)
                        else:
                            temp_contents_list.append(product_dict)

                    set_dict['set_content'] = temp_contents_list

                    # set_dict['set_content'] = set_contents_list

                    set_list.append(set_dict)
                    set_contents_list = []
                    set_contents_dict = {}
                elif idx == 0 and len(set_product_datas) == 1:

                    set_contents_list.append(set_contents_dict)

                    set_dict['set_price'] = (set_data.price) / COVERT_DATA_TO_MONEY_NUMBER
                    set_dict['set_saleprice'] = (set_data.salePrice) / COVERT_DATA_TO_MONEY_NUMBER
                    set_dict['set_name'] = set_data.Rem1
                    set_dict['set_content'] = set_contents_list

                    set_list.append(set_dict)
                    set_contents_dict = {}
                else:#表示idx为0
                    set_contents_list.append(set_contents_dict)
                    set_contents_dict = {}

                set_dict = {}

        return set_list


    def print_receipts(self, store_id, orderNo):
        """
        :param store_id:    店铺id
        :param orderNo:     订单号
        :return:            打印小票信息
        """
        store_full_name = ''
        datas = self.controlsession.query(FlagShipStoreInfo).filter(FlagShipStoreInfo.id==store_id).first()
        if isinstance(datas, types.NoneType):
            store_full_name = ''
        else:
            store_name = datas.name
            store_area = datas.area
            store_addr = datas.address

            store_area_list = store_area.split(',')
            store_area_list.append(store_addr)
            store_area_list.append(store_name)
            store_temp_addr = [temp.strip() for temp in store_area_list]
            store_full_name = ''.join(store_temp_addr)


        orderDatas = self.controlsession.query(SaleOrder).filter(SaleOrder.store_id==store_id, SaleOrder.orderNo==orderNo).first()
        if isinstance(orderDatas, types.NoneType):
            raise ValueError("订单记录有错误！")
        else:
            cashier = orderDatas.Rem1
            actPrice = (orderDatas.actPrice)/COVERT_DATA_TO_MONEY_NUMBER     #实收金额
            setPrice = (orderDatas.setPrice )/COVERT_DATA_TO_MONEY_NUMBER    #应收金额
            totalPrice = (orderDatas.totalPrice)/COVERT_DATA_TO_MONEY_NUMBER #总计
            change = (orderDatas.change)/COVERT_DATA_TO_MONEY_NUMBER         #找零

            product_list = self.get_saleproduct_by_orderno(orderNo)
            set_list = self.get_set_saleproduct_by_orderno(orderNo)

            product_dict = {}
            temp_good_list = []
            for product in product_list:
                for icount in range(product['p_count']):
                    product_dict['name'] = product['p_name']
                    product_dict['serial_number'] = product['p_sn']
                    product_dict['price'] = product['price']
                    product_dict['gift'] = product['gift']

                    temp_good_list.append(product_dict)
                    product_dict = {}

            for set_item in set_list: #套餐间遍历
                for set_pro in set_item['set_content']:#套餐内遍历
                    for icount in range(set_pro['p_count']):
                        product_dict['name'] = set_pro['p_name']
                        product_dict['serial_number'] = set_pro['p_sn']
                        product_dict['price'] = set_pro['price']
                        product_dict['gift'] = set_pro['gift']

                        temp_good_list.append(product_dict)
                        product_dict = {}

            addtime = datetime.datetime.now().strftime('%Y-%m-%d %H:%M')

        return store_full_name, cashier, temp_good_list, totalPrice, setPrice, actPrice,change,addtime


    def CreateOutOrder(self, store_id, orderNo):
        """
        :param store_id: 店铺id
        :param orderNo: 订单号
        :return:生成出库单号及生成出库单
        """
        holawarehouse = HolaWareHouse()
        mixusercenterop =MixUserCenterOp()
        good_dict = {}
        datas = self.controlsession.query(SaleOrder).filter(SaleOrder.orderNo==orderNo).first()
        if isinstance(datas, types.NoneType):
            pass
        else:
            work_number = datas.Rem1        #收银员工号
            good_dict['user'] = mixusercenterop.get_salesmen_name(work_number) #收银员名称
            # good_dict['flagshipid'] = datas.store_id
            good_dict['flagshipid'] = store_id
            good_dict['remark_info'] = orderNo

            product_list = self.get_saleproduct_by_orderno(orderNo)
            set_list = self.get_set_saleproduct_by_orderno(orderNo)
            len_product = len(product_list)
            len_set = 0
            for set_item in set_list:#套餐间遍历
                for set_pro in set_item['set_content']:#套餐内遍历
                    len_set += set_pro['p_count']

            good_dict['all_amount'] = len_product + len_set

            product_dict = {}
            good_list = []
            temp_good_list = []

            for product in product_list:
                product_id = holawarehouse.getProIdByGoodCode(product['p_code'])

                product_dict['good_id'] = product_id
                product_dict['serial_number'] = product['p_sn']
                product_dict['count'] = product['p_count']

                temp_good_list.append(product_dict)
                product_dict = {}

            for set_item in set_list: #套餐间遍历
                for set_pro in set_item['set_content']:#套餐内遍历
                    product_id = holawarehouse.getProIdByGoodCode(set_pro['p_code'])
                    product_dict['good_id'] = product_id
                    product_dict['serial_number'] = set_pro['p_sn']
                    product_dict['count'] = set_pro['p_count']

                    temp_good_list.append(product_dict)
                    product_dict = {}

        #temp_good_list去重
        for temp_item in temp_good_list:
            if not good_list:
                good_list.append(temp_item)
            else:
                if temp_item['good_id'] in [temp['good_id'] for temp in good_list]:
                    if temp_item['serial_number'].strip() != '': #存在SN号
                        good_list.append(temp_item)
                    else:
                        #合并相同元素的数据
                        for item in good_list:
                            if item['good_id'] == temp_item['good_id']:
                                item['count'] += temp_item['count']
                else:
                    good_list.append(temp_item)

        good_dict['good_list'] = good_list


        datas = self.controlsession.query(CustomerInfo).filter(SaleOrder.orderNo==orderNo).first()
        if datas is not None:
            pro = datas.province
            city = datas.city
            addr = datas.addr
            detail_addr = ''.join([pro.strip(), city.strip(), addr.strip()])
        else:
            detail_addr = ''

        return good_dict, detail_addr


    def get_id_by_orderNo(self, store_id,orderNo, p_code,ptype):
        """
        :param store_id:
        :param orderNo:
        :param ptype:  1:表示搜索非套餐类型，2：表示搜索套餐类型
        :return:
        """
        holawarehouse = HolaWareHouse()
        if ptype==1:
            datas = self.controlsession.query(SaleOrderDetail).filter(SaleOrderDetail.orderNo==orderNo,SaleOrderDetail.store_id==store_id, Sa).all()
            if not datas:
                return None
            else:
                product_id = holawarehouse.getProIdByGoodCode(datas.pCode)
                return product_id
        elif ptype==2:
            datas = self.controlsession.query(SetRecordInfo).filter(SetRecordInfo.orderNo==orderNo, SetRecordInfo.store_id==store_id).all()
            if not datas:
                return None
            else:
                product_id = holawarehouse.getProIdByGoodCode(datas.pCode)
                return product_id


    def get_out_num(self, store_id, good_dict, orderNo, detail_addr):
        """
        :param store_id:店铺id
        :param good_dict:
        :param orderNo:订单号
        :param detail_addr:
        :return:生成出库单号
        """
        try:
            inoutwarehouseop = InOutWarehouseOp()

            opp = FlagShipOp()
            flagship_info = opp.get_flagship_info(store_id)
            good_dict['send_site'] = flagship_info['name']
            good_dict['recv_site'] = detail_addr
            good_dict['logistics_name'] = ""

            # good_dict['send_site'] = '深圳旗舰店'
            # good_dict['recv_site'] = ''
            # good_dict['logistics_name'] = '其它物流'
            res = inoutwarehouseop.AutoCreateOrderInfo(good_dict,False)
            if res['code'] == ServiceCode.service_exception:
                pass
            elif res['code'] == ServiceCode.success:
                outnum = res['out_number']
                #更新数据库
                result = self.controlsession.query(SaleOrder).filter(SaleOrder.orderNo==orderNo
                        ).update({SaleOrder.Rem4: outnum})
                self.controlsession.commit()
                return outnum
        except SQLAlchemyError as e:
            self.controlsession.rollback()
            return None

    def update_order_note(self, orderNo, ordernote):
        """
        :param orderNo: 订单号
        :param ordernote: 编辑保存后的订单备注信息
        :return:返回更新是否成功的标识
        """
        try:
            result = self.controlsession.query(SaleOrder).filter(SaleOrder.orderNo==orderNo).first()
            if result is None:
                return  False
            else:
                result.describe = ordernote
                self.controlsession.add(result)
                self.controlsession.commit()
        except SQLAlchemyError as e:
            self.controlsession.rollback()
            print (traceback.format_exc(e))
            raise
        return True

    # def ReCheckSerialNo(self,orderNo):
    #     product_list = self.get_saleproduct_by_orderno(orderNo)
    #     set_list = self.get_set_saleproduct_by_orderno(orderNo)
    # 
    #     #从product_list与set_list中筛选出需要重现验证序列号的商品信息
    #     goods = []
    #     for product in product_list:
    #         product_dict = {}
    #         product_dict['id'] = product['id']
    #         product_dict['p_name'] = product['p_name']
    #         product_dict['p_code'] = product['p_code']
    #         goods.append(product_dict)
    # 
    #     set = []
    #     for set_item in set_list: #套餐间遍历
    #         for set_pro in set_item['set_content']:#套餐内遍历
    #             product_dict = {}
    #             product_dict['id'] = set_pro['id']
    #             product_dict['p_name'] = set_pro['p_name']
    #             product_dict['p_code'] = set_pro['p_sn']
    #             set.append(product_dict)
    # 
    #     return goods, set

    def get_saleproduct_info(self, order_number, barcode):
        """
        :param order_number: 销售订单号
        :param barcode:     商品条形码
        :return: 根据商品销售订单号和商品条形码获取商品的信息
        """


        rs_singel = self.controlsession.query(SaleOrderDetail).filter(SaleOrderDetail.orderNo==order_number,
                                                                      SaleOrderDetail.barCode==barcode).first()

        if rs_singel:
            setprice = rs_singel.price  #商品门店价
            saleprice = rs_singel.salePrice #商品售价
        else:
            rs_set = self.controlsession.query(SetRecordInfo).filter(SetRecordInfo.orderNo==order_number,
                                                                     SetRecordInfo.barCode==barcode).first()
            if rs_set:
                setprice = rs_set.price
                saleprice = rs_set.price
            else:
                print(order_number)
                print(barcode)
                raise ValueError(u"销售订单号为%s的记录中没有关于商品条形码为%s的信息" % order_number,barcode)

        return setprice, saleprice
















