#/usr/bin/python
#-*- coding:utf-8 -*-

'''
Created on : 2016-10-10
@author : Yuan Rong
@function : 销售订单信息的混合OP
'''

import time
import datetime
import traceback
from flask import session
from data_mode.hola_flagship_store.control_base.controlBase import ControlEngine
from control_center.shop_manage.good_info_manage.control.mixOp import HolaWareHouse
from control_center.flagship_manage.flagship_info_manage.control.mixOp import FlagShipOp
from control_center.flagship_manage.warehouse_manage.control.in_out_warehouse_op import InOutWarehouseOp
from data_mode.hola_warehouse.control.base_op import ProductBaseInfoOp

from control_center.flagship_manage.sale_manage.control.saleProductOp import SaleOrderOp
from control_center.flagship_manage.sale_manage.control.saleProductOp import OrderSupplementOp
from control_center.flagship_manage.sale_manage.control.saleProductOp import OrderDetail

from data_mode.hola_flagship_store.mode.sale_mode.customer_info import CustomerInfo
from data_mode.hola_flagship_store.mode.sale_mode.sale_order import SaleOrder
from data_mode.hola_flagship_store.mode.sale_mode.sale_order_detail import SaleOrderDetail
from data_mode.hola_flagship_store.mode.sale_mode.set_product_record import SetProductRecord
from data_mode.hola_flagship_store.mode.sale_mode.set_record_info import SetRecordInfo
from data_mode.hola_flagship_store.mode.warehouse_mode.warehouse_manage import *
from data_mode.hola_flagship_store.mode.warehouse_mode.warehouse_manage import ProductRelation, Inventory
from data_mode.hola_flagship_store.mode.statistic_model.flagship_sale_daily import GlobalDailySale
from data_mode.hola_flagship_store.mode.statistic_model.flagship_sale_yearMonth import GlobalMonthSale
from data_mode.hola_flagship_store.mode.statistic_model.flagship_sale_clerk_daily import ClerkDailySale
from data_mode.hola_flagship_store.mode.statistic_model.flagship_sale_clerk_yearMonth import ClerkMonthSale
from data_mode.hola_flagship_store.mode.statistic_model.flagship_sale_set_clerk_daily import ClerkDailySaleSet
from data_mode.hola_flagship_store.mode.statistic_model.flagship_sale_set_clerk_yearMonth import ClerkMonthSaleSet
from data_mode.user_center.control.mixOp import MixUserCenterOp


from config.service_config.returncode import ServiceCode
from public.exception.custom_exception import CodeError
from config.share.share_define import *

from public.sale_share.share_function import *


def get_current_month():
    '''
    FUNCTION : 获得当前年月
    :return: int <201610>
    '''
    current = time.localtime()
    return current.tm_year * 100 + current.tm_mon

def get_current_date():
    '''
    FUNCTION : 获得当前年月日
    :return: int <20160901>
    '''
    current = time.localtime()
    return current.tm_year * 10000 + current.tm_mon * 100 + current.tm_mday

class FlagshipOrderInfoOp(ControlEngine):
    '''旗舰店销售订单信息混合控制模块
    '''

    def __init__(self):
        ControlEngine.__init__(self)

    def createOrderNo(self, store_id, selt_date, selt_time):
        '''
        @function : 根据<店铺id-日期-时间-流水号>规则生成订单号
        :param store_id:
        :param selt_date:
        :param selt_time:
        :return: str
        '''
        try:
            orderNo = None
            rs = self.controlsession.query(SaleOrder).order_by(
                SaleOrder.id.desc()).first()
            selt_date = selt_date[2:]
            date = selt_date.replace('-', '')
            selt_time = selt_time.split(':')
            time = selt_time[0] + selt_time[1]
            now_count = rs.id + 1 if rs is not None else 1
            orderNo = "S%.3d%6.6s%4.4s%.4d" % (int(store_id), date, time, now_count)
            return orderNo

        except Exception as e:
            print(traceback.format_exc(e))
            raise

    def getGoodDict(self, p_code, p_sn, p_count=1):
        '''
        @function : 生成商品字典，组装数据给库存模块
        :param p_code:
        :param p_sn:
        :param p_count:
        :return:
        '''
        try:
            temp = {}
            hola_op = HolaWareHouse()
            temp['good_id'] = hola_op.getProIdByGoodCode(p_code)
            temp['serial_number'] = p_sn
            temp['count'] = p_count
            if temp is not None:
                print "-----------------temp,type, pcode-------------",temp, type(temp), p_code
                return temp
            else:
                raise NameError("value is null!")
        except Exception as e:
            print traceback.format_exc(e)
            raise

    def getIsGift(self, state):
        '''
        @function : 根据状态获得商品是否为赠品
        :param state:
        :return:
        '''
        result = "gift" if state else "goods"
        return result

    def floatToIntger(self, f_num):
        '''
        @function : float number change to intger
        :param f_num:
        :return: int
        '''
        if f_num is not None:
            if isinstance(f_num, float):
                return int(f_num * COVERT_MONEY_TYPE_NUMBER)
            elif isinstance(f_num, (str, unicode)):
                return int(float(f_num) * COVERT_MONEY_TYPE_NUMBER)
            elif isinstance(f_num, int):
                return f_num
        raise ValueError(u'类型错误!')

    def getOrderNumber(self, store_id, salesman, cashier, set_price, act_price,
                       selt_date, selt_time, product_list, set_meal_list, set_count_dict, send_tplid, pay_tplid, **kwargs):
        '''
        @function : 根据结算数据生成订单信息和储存数据库数据
        :param store_id: 店铺id
        :param salesman: 促销员名字
        :param cashier: 收营员账号名字
        :param set_price: 应付
        :param act_price: 实付
        :param selt_date: 结算日期
        :param selt_time: 结算时间
        :param product_list: 商品信息列表
        :param set_meal_list: 套餐信息列表
        :param set_count_dict: 购物车内套餐数量字典信息
        :param send_tplid: 商品配送方式
        :param pay_tplid: 支付方式
        :param kwargs: 缺省参数
        :return: {'code':
                ' orderNo':str
                'set_price': float,	#订单金额}
        '''
        try:
            set_price = self.floatToIntger(set_price)
            act_price = self.floatToIntger(act_price)
            # print("set_price:%d  act_price:%d" % (set_price, act_price))
            if set_price == 0 or act_price == 0:
                raise CodeError(ServiceCode.PriceLessThenBasePrice, u'物品销售价格不能为0')

            orderNo = self.createOrderNo(store_id, selt_date, selt_time)
            if orderNo is None:
                raise CodeError(ServiceCode.service_exception, u'创建订单号失败')

            sale_op = SaleOrderOp()
            supp_op = OrderSupplementOp()
            pro_base_op = ProductBaseInfoOp()
            user_op = MixUserCenterOp()
            uid = user_op.get_salesmen_uid(salesman)

            rs = self.controlsession.query(
                SaleOrder).filter_by(orderNo=orderNo).first()
            if rs is not None:  # 判断新生成的订单号是否已经存在订单表中，已存在返回错误码
                raise CodeError(ServiceCode.service_exception, u'订单号已存在')

            p_total_original_price = 0  # 商品原价
            p_total_sale_price = 0  # 商品的售价

            good_dict = {} #返回信息给库存模块
            for pro_info in product_list:
                # 将商品信息存进商品详情表中
                pSaleDetail = SaleOrderDetail(
                    store_id=store_id,
                    orderNo=orderNo,
                    name=pro_info['name'],
                    serialNo=pro_info['p_sn'],
                    barCode=pro_info['p_barCode'],
                    pCode=pro_info['p_code'],
                    price=self.floatToIntger(pro_info['price']),
                    salePrice=self.floatToIntger(pro_info['sale_price']),
                    Rem1=pro_info['p_category_name'],
                    state=self.getIsGift(pro_info['is_gift']))
                self.controlsession.add(pSaleDetail)
                p_total_original_price += self.floatToIntger(pro_info['price'])
                p_total_sale_price += self.floatToIntger(pro_info['sale_price'])

                #组合商品数据
                temp = self.getGoodDict(pro_info['p_code'], pro_info['p_sn'])
                # print "set pro info: ", temp
                if good_dict.get('good_list', ""):
                    good_dict['good_list'].append(temp)
                else:
                    good_dict['good_list'] = []
                    good_dict['good_list'].append(temp)

                #商品销售数据统计
                pro_base_info = pro_base_op.getGoodInfoByproCode(pro_info['p_code'])
                self.add_flagship_sale(uid, pro_base_info.get('id', ""), store_id,
                                       self.floatToIntger(pro_info['sale_price']), 0,
                                       pro_base_info['category']['id'])

            s_total_original_price = 0  # 套餐的原价
            s_total_sale_price = 0  # 套餐的售价
            tempSet = []
            for set_info in set_meal_list:
                set_content_list = set_info['set_content']
                for p_info in set_content_list:
                    # 将套餐内含的商品信息记录到商品内容记录表中
                    setRecordDetail = SetRecordInfo(
                        store_id=store_id,
                        orderNo=orderNo,
                        set_meal_id=set_info['set_id'],
                        name=p_info['name'],
                        serialNo=p_info['p_sn'],
                        barCode=p_info['p_barCode'],
                        pCode=p_info['p_code'],
                        price=self.floatToIntger(p_info['price']),
                        Rem2=p_info['p_category_name'],
                        Rem1=self.getIsGift(p_info['is_gift']),
                        Rem3=p_info['p_count']
                    )
                    self.controlsession.add(setRecordDetail)

                    # 组合商品数据
                    temp = self.getGoodDict(p_info['p_code'], p_info['p_sn'], p_info['p_count'])
                    # print "set pro info: ",temp
                    if good_dict.get('good_list', ""):
                        good_dict['good_list'].append(temp)
                    else:
                        good_dict['good_list'] = []
                        good_dict['good_list'].append(temp)

                    # 套餐中商品销售数据统计
                    pro_base_info = pro_base_op.getGoodInfoByproCode(p_info['p_code'])
                    for i in xrange(int(p_info['p_count'])):
                        print "pro_base_info.get('id', "")", int(pro_base_info.get('id', ""))
                        self.add_flagship_sale_set_detail(int(pro_base_info.get('id', "")), int(store_id),
                                             0, int(pro_base_info['category']['id']), 2)

                s_total_sale_price += self.floatToIntger(set_info['sale_price'])
                s_total_original_price += self.floatToIntger(set_info['original_price'])

                # 将套餐信息存进套餐商品记录表中
                setCountDict = eval(set_count_dict.encode())
                if set_info['set_id'] not in tempSet:
                    tempSet.append(set_info['set_id'])
                else:
                    continue
                sSaleRecord = SetProductRecord(
                    store_id=store_id,
                    orderNo=orderNo,
                    set_meal_id=set_info['set_id'],
                    Rem1=set_info['name'],
                    salePrice=self.floatToIntger(set_info['sale_price']),
                    price=self.floatToIntger(s_total_original_price),
                    Rem2=setCountDict.get(str(set_info['set_id']), ""))
                self.controlsession.add(sSaleRecord)

                #套餐销售统计
                for i in xrange(int(setCountDict.get(str(set_info['set_id']), ""))):
                    self.add_flagship_sale_set(uid, int(set_info['set_id']), int(store_id),
                                             self.floatToIntger(set_info['sale_price']), 0)

            # 扣钱成功，通知库存模块，进行相对应sn码的商品进行删除，也就是库存量减一,制作出库单
            detail_op = OrderDetail()
            print "################cashier##########",
            uid = session['user']['id']
            cashier_name = user_op.get_user_simple_info(uid)
            good_dict['user'] = cashier_name['name']
            good_dict['flagshipid'] = store_id
            good_dict['remark_info'] = orderNo
            good_dict['all_amount'] = len(good_dict['good_list'])

            tempList = []
            for info in good_dict['good_list']:
                if tempList:
                    tempList.append(info)
                else:
                    if info['good_id'] in [t['good_id'] for t in tempList]:
                        if info['serial_number'] != u'':
                            tempList.append(info)
                        else:
                            for item in tempList:
                                if item['good_id'] == info['good_id']:
                                    item['count'] += info['count']
                    else:
                        tempList.append(info)

            # 添加收货单位和发送单位
            opp = FlagShipOp()
            flagship_info = opp.get_flagship_info(store_id)
            good_dict['send_site'] = flagship_info['name']
            good_dict['recv_site'] = kwargs['kwargs']['province'] + kwargs['kwargs']['city'] + kwargs['kwargs']['addr']
            good_dict['logistics_name'] = None
            good_dict['good_list'] = tempList
            good_dict['warehouse_type_id'] = WarehouseType.inventory_warehouse
            good_dict['to_warehouse_type_id'] = WarehouseType.out_warehouse
            good_dict['operate_type'] = OperateType.sale_out
            good_dict['flagshipid'] = store_id
            good_dict['date'] = datetime.datetime.now()
            op = ShareFunctionOp()
            good_dict['number'] = op.create_numberNo(store_id, good_dict['operate_type'])['number']

            if send_tplid == '1':
                # print "good_dict : ", good_dict
                # number = self.AutoCreateOrderInfo(good_dict, False)
                number = AutoCreateOrderInfoExp(good_dict, self.controlsession)
                if number['code'] == ServiceCode.success:
                    number = number['out_number']
                elif number['code'] == ServiceCode.service_exception:
                    raise CodeError(ServiceCode.out_inventory_error, u'出库失败')
            else:
                number = ""

            total_original_price = self.floatToIntger(p_total_original_price) + self.floatToIntger(s_total_original_price)
            total_sale_price = self.floatToIntger(p_total_sale_price) + self.floatToIntger(s_total_sale_price)
            if self.checkTotalMoney(total_sale_price, set_price):
                # print "#################act_price, set_price################",self.floatToIntger(act_price), type(act_price), self.floatToIntger(set_price), type(set_price)
                change = self.floatToIntger(act_price) - self.floatToIntger(set_price)  # 找零
                # print "#################change################",self.floatToIntger(change), type(change)
                if change >= 0.0001:
                    saleOrder = SaleOrder(
                        store_id=store_id,
                        orderNo=orderNo,
                        seltDate=selt_date,
                        seltTime=selt_time,
                        salesman=salesman,
                        Rem1=cashier,
                        setPrice=self.floatToIntger(set_price),
                        actPrice=self.floatToIntger(act_price),
                        change=change,
                        totalPrice=self.floatToIntger(total_original_price),
                        discount=0,
                        newPayType_id=pay_tplid,
                        describe="",
                        sendType=supp_op.getSendType(send_tplid),
                        sendState=sale_op.getSendStateBySendType(send_tplid),
                        Rem2=self.floatToIntger(set_price),
                        Rem3="不需要",
                        Rem4=number
                    )
                    self.controlsession.add(saleOrder)
                else:
                    saleOrder = SaleOrder(
                        store_id=store_id,
                        orderNo=orderNo,
                        seltDate=selt_date,
                        seltTime=selt_time,
                        salesman=salesman,
                        Rem1=cashier,
                        setPrice=self.floatToIntger(set_price),
                        actPrice=self.floatToIntger(act_price),
                        change=change,
                        totalPrice=self.floatToIntger(total_original_price),
                        discount=0,
                        newPayType_id=pay_tplid,
                        describe="",
                        sendType=supp_op.getSendType(send_tplid),
                        sendState=sale_op.getSendStateBySendType(send_tplid),
                        Rem2=self.floatToIntger(act_price),
                        Rem3="不需要",
                        Rem4=number
                    )
                    self.controlsession.add(saleOrder)

            rs_c = self.controlsession.query(CustomerInfo).filter_by(orderNo=orderNo).first()
            if rs_c is None:
                #插入联系人订单信息
                customer = CustomerInfo(
                    store_id=store_id,
                    orderNo=orderNo,
                    name="",
                    tel="",
                    province=kwargs['kwargs']['province'],
                    city=kwargs['kwargs']['city'],
                    addr=kwargs['kwargs']['addr'],
                    invoice_name="",
                    invoice_head="",
                    invoice_comment="",
                    Rem1=kwargs['kwargs']['consignee_name'],
                    Rem2=kwargs['kwargs']['consignee_tel'],
                    sex="")
                self.controlsession.add(customer)
            self.controlsession.commit()
            return {"orderNo": orderNo, "set_price": self.floatToIntger(set_price)/COVERT_DATA_TO_MONEY_NUMBER}
        except CodeError as e:
            print e
            self.controlsession.rollback()
            raise
        except Exception as e:
            self.controlsession.rollback()
            print (traceback.format_exc(e))
            raise

    def checkTotalMoney(self, calc_price, get_price):
        '''
        FUNCTION : 核查客户端传来的实收金额
        :param calc_price: 服务端计算后的金额
        :param get_price: 客户端传过来的金额
        :return: 布尔值True or False
        '''
        try:
            # print "*"*40
            # print "calc_price, get_price", calc_price, get_price
            if calc_price == get_price:
                return True
            else:
                raise ValueError("calc_price is not equal to get_price!")
        except Exception as e:
            print (traceback.format_exc(e))
            raise

    def add_flagship_sale(self, uid, productId, flagShipId, mySaleMoney, myPercentageMoney, myCategoryId, proType=1):
        '''
        FUNCTION : 添加旗舰店销售统计记录
        :param uid:
        :param productId:
        :param flagShipId:
        :param mySaleMoney:
        :param myPercentageMoney:
        :param myCategoryId:
        :return:
        '''
        try:
            gdsquery = self.controlsession.query(GlobalDailySale)
            gmsquery = self.controlsession.query(GlobalMonthSale)
            cdsquery = self.controlsession.query(ClerkDailySale)
            cmsquery = self.controlsession.query(ClerkMonthSale)
            hwop = HolaWareHouse()
            # ancestorId = hwop.get_category_ancestor(myCategoryId)


            myday = get_current_date()
            ym = get_current_month()
            g_ds = gdsquery.filter_by(productTypeId=productId, dayTime=myday, shipId=flagShipId).scalar()
            g_ms = gmsquery.filter_by(productTypeId=productId, yearMonth=ym, shipId=flagShipId).scalar()
            c_ds = cdsquery.filter_by(userId=uid, dayTime=myday, productTypeId=productId, shipId=flagShipId).scalar()
            c_ms = cmsquery.filter_by(userId=uid, yearMonth=ym, productTypeId=productId, shipId=flagShipId).scalar()

            if not g_ds:
                g_ds = GlobalDailySale(productTypeId=productId, categoryId=myCategoryId, dayTime=myday, shipId=flagShipId,
                                       saleCount=1, saleMoney=mySaleMoney, proType=proType)  #修改统计记录商品的直接分类
            else:
                g_ds.saleCount = g_ds.saleCount+1
                g_ds.saleMoney = g_ds.saleMoney+mySaleMoney

            if not g_ms:
                g_ms = GlobalMonthSale(productTypeId=productId, categoryId=myCategoryId, yearMonth=ym, shipId=flagShipId,
                                       saleCount=1, saleMoney=mySaleMoney, proType=proType) #修改统计记录商品的直接分类
            else:
                g_ms.saleCount = g_ms.saleCount+1
                g_ms.saleMoney = g_ms.saleMoney+mySaleMoney

            if not c_ds:
                c_ds = ClerkDailySale(userId=uid, productTypeId=productId, shipId=flagShipId, dayTime=myday, orderCount=1,
                                      saleMoney=mySaleMoney, percentageMoney=myPercentageMoney)
            else:
                c_ds.orderCount = c_ds.orderCount+1
                c_ds.saleMoney = c_ds.saleMoney+mySaleMoney
                c_ds.percentageMoney = c_ds.percentageMoney+myPercentageMoney

            if not c_ms:
                c_ms = ClerkMonthSale(userId=uid, productTypeId=productId, shipId=flagShipId, yearMonth=ym, orderCount=1,
                                      saleMoney=mySaleMoney, percentageMoney=myPercentageMoney)
            else:
                c_ms.orderCount = c_ms.orderCount+1
                c_ms.saleMoney = c_ms.saleMoney+mySaleMoney
                c_ms.percentageMoney = c_ms.percentageMoney+myPercentageMoney

            self.controlsession.add(g_ds)
            self.controlsession.add(g_ms)
            self.controlsession.add(c_ds)
            self.controlsession.add(c_ms)
        except CodeError as e:
            self.controlsession.rollback()
            raise
        except Exception, e:
            print traceback.format_exc()
            self.controlsession.rollback()

    def add_flagship_sale_set_detail(self, productId, flagShipId, mySaleMoney, myCategoryId, proType=1):
        '''
        FUNCTION : 统计套餐中商品的数据
        :param uid:
        :param productId:
        :param flagShipId:
        :param mySaleMoney:
        :param myPercentageMoney:
        :param myCategoryId:
        :return:
        '''
        try:
            gdsquery = self.controlsession.query(GlobalDailySale)
            gmsquery = self.controlsession.query(GlobalMonthSale)
            hwop = HolaWareHouse()
            # ancestorId = hwop.get_category_ancestor(myCategoryId)

            myday = get_current_date()
            ym = get_current_month()
            g_ds = gdsquery.filter_by(productTypeId=productId, dayTime=myday, shipId=flagShipId).scalar()
            g_ms = gmsquery.filter_by(productTypeId=productId, yearMonth=ym, shipId=flagShipId).scalar()

            if not g_ds:
                g_ds = GlobalDailySale(productTypeId=productId, categoryId=myCategoryId, dayTime=myday, shipId=flagShipId,
                                       saleCount=1, saleMoney=mySaleMoney, proType=proType) #修改统计记录商品的直接分类
            else:
                g_ds.saleCount = g_ds.saleCount + 1
                g_ds.saleMoney = g_ds.saleMoney + mySaleMoney

            if not g_ms:
                g_ms = GlobalMonthSale(productTypeId=productId, categoryId=myCategoryId, yearMonth=ym, shipId=flagShipId,
                                       saleCount=1, saleMoney=mySaleMoney, proType=proType) #修改统计记录商品的直接分类
            else:
                g_ms.saleCount = g_ms.saleCount + 1
                g_ms.saleMoney = g_ms.saleMoney + mySaleMoney

            self.controlsession.add(g_ds)
            self.controlsession.add(g_ms)
        except CodeError as e:
            self.controlsession.rollback()
            raise
        except Exception, e:
            print traceback.format_exc()
            self.controlsession.rollback()

    def add_flagship_sale_set(self, uid, setId, flagShipId, mySaleMoney, myPercentageMoney):
        '''
        Function : 统计旗舰店的套餐销售
        :return:
        '''
        try:
            cdssquery = self.controlsession.query(ClerkDailySaleSet)
            cmssquery = self.controlsession.query(ClerkMonthSaleSet)

            myday = get_current_date()
            ym = get_current_month()

            c_dss = cdssquery.filter_by(userId=uid, dayTime=myday, setTypeId=setId, shipId=flagShipId).scalar()
            c_mss = cmssquery.filter_by(userId=uid, yearMonth=ym, setTypeId=setId, shipId=flagShipId).scalar()

            if not c_dss:
                c_dss = ClerkDailySaleSet(userId=uid, setTypeId=setId, shipId=flagShipId, dayTime=myday, orderCount=1, saleMoney=mySaleMoney, percentageMoney=myPercentageMoney)
            else:
                c_dss.orderCount = c_dss.orderCount+1
                c_dss.saleMoney = c_dss.saleMoney+mySaleMoney
                c_dss.percentageMoney = c_dss.percentageMoney+myPercentageMoney

            if not c_mss:
                c_mss = ClerkMonthSaleSet(userId=uid, setTypeId=setId, shipId=flagShipId, yearMonth=ym, orderCount=1, saleMoney=mySaleMoney, percentageMoney=myPercentageMoney)
            else:
                c_mss.orderCount = c_mss.orderCount+1
                c_mss.saleMoney = c_mss.saleMoney+mySaleMoney
                c_mss.percentageMoney = c_mss.percentageMoney+myPercentageMoney

            self.controlsession.add(c_dss)
            self.controlsession.add(c_mss)
        except CodeError as e:
            self.controlsession.rollback()
            raise
        except Exception, e:
            print traceback.format_exc()
            self.controlsession.rollback()