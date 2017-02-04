#/usr/bin/python
#-*- coding:utf-8 -*-

import time
import traceback
from public.exception.custom_exception import CodeError
from data_mode.hola_flagship_store.control_base.controlBase import ControlEngine
from data_mode.hola_flagship_store.mode.statistic_model.flagship_sale_daily import GlobalDailySale
from data_mode.hola_flagship_store.mode.statistic_model.flagship_sale_yearMonth import GlobalMonthSale
from data_mode.hola_flagship_store.mode.statistic_model.flagship_sale_clerk_daily import ClerkDailySale
from data_mode.hola_flagship_store.mode.statistic_model.flagship_sale_clerk_yearMonth import ClerkMonthSale
from data_mode.hola_flagship_store.mode.statistic_model.flagship_sale_set_clerk_daily import ClerkDailySaleSet
from data_mode.hola_flagship_store.mode.statistic_model.flagship_sale_set_clerk_yearMonth import ClerkMonthSaleSet

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

class testMixOp(ControlEngine):
    '''
    FUNCTION : 批量导入已经销售的数据进统计表中
    '''
    def __init__(self):
        ControlEngine.__init__(self)

    def add_flagship_sale(self, uid, productId, flagShipId, mySaleMoney, myPercentageMoney, myCategoryId,
                          myday=None, ym=None, proType=1):
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

            g_ds = gdsquery.filter_by(productTypeId=productId, dayTime=myday, shipId=flagShipId).scalar()
            g_ms = gmsquery.filter_by(productTypeId=productId, yearMonth=ym, shipId=flagShipId).scalar()
            c_ds = cdsquery.filter_by(userId=uid, dayTime=myday, productTypeId=productId, shipId=flagShipId).scalar()
            c_ms = cmsquery.filter_by(userId=uid, yearMonth=ym, productTypeId=productId, shipId=flagShipId).scalar()

            if not g_ds:
                g_ds = GlobalDailySale(productTypeId=productId, categoryId=myCategoryId, dayTime=myday, shipId=flagShipId,
                                       saleCount=1, saleMoney=mySaleMoney, proType=proType)  # 修改统计记录商品的直接分类
            else:
                g_ds.saleCount = g_ds.saleCount + 1
                g_ds.saleMoney = g_ds.saleMoney + mySaleMoney

            if not g_ms:
                g_ms = GlobalMonthSale(productTypeId=productId, categoryId=myCategoryId, yearMonth=ym, shipId=flagShipId,
                                       saleCount=1, saleMoney=mySaleMoney, proType=proType)  # 修改统计记录商品的直接分类
            else:
                g_ms.saleCount = g_ms.saleCount + 1
                g_ms.saleMoney = g_ms.saleMoney + mySaleMoney

            if not c_ds:
                c_ds = ClerkDailySale(userId=uid, productTypeId=productId, shipId=flagShipId, dayTime=myday, orderCount=1,
                                      saleMoney=mySaleMoney, percentageMoney=myPercentageMoney)
            else:
                c_ds.orderCount = c_ds.orderCount + 1
                c_ds.saleMoney = c_ds.saleMoney + mySaleMoney
                c_ds.percentageMoney = c_ds.percentageMoney + myPercentageMoney

            if not c_ms:
                c_ms = ClerkMonthSale(userId=uid, productTypeId=productId, shipId=flagShipId, yearMonth=ym, orderCount=1,
                                      saleMoney=mySaleMoney, percentageMoney=myPercentageMoney)
            else:
                c_ms.orderCount = c_ms.orderCount + 1
                c_ms.saleMoney = c_ms.saleMoney + mySaleMoney
                c_ms.percentageMoney = c_ms.percentageMoney + myPercentageMoney

            self.controlsession.add(g_ds)
            self.controlsession.add(g_ms)
            self.controlsession.add(c_ds)
            self.controlsession.add(c_ms)
            self.controlsession.commit()
        except CodeError as e:
            self.controlsession.rollback()
            raise
        except Exception, e:
            print traceback.format_exc()
            self.controlsession.rollback()


    def add_flagship_sale_set_detail(self, productId, flagShipId, mySaleMoney, myCategoryId,
                                     myday=None, ym=None, proType=1):
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

            g_ds = gdsquery.filter_by(productTypeId=productId, dayTime=myday, shipId=flagShipId).scalar()
            g_ms = gmsquery.filter_by(productTypeId=productId, yearMonth=ym, shipId=flagShipId).scalar()

            if not g_ds:
                g_ds = GlobalDailySale(productTypeId=productId, categoryId=myCategoryId, dayTime=myday, shipId=flagShipId,
                                       saleCount=1, saleMoney=mySaleMoney, proType=proType)  # 修改统计记录商品的直接分类
            else:
                g_ds.saleCount = g_ds.saleCount + 1
                g_ds.saleMoney = g_ds.saleMoney + mySaleMoney

            if not g_ms:
                g_ms = GlobalMonthSale(productTypeId=productId, categoryId=myCategoryId, yearMonth=ym, shipId=flagShipId,
                                       saleCount=1, saleMoney=mySaleMoney, proType=proType)  # 修改统计记录商品的直接分类
            else:
                g_ms.saleCount = g_ms.saleCount + 1
                g_ms.saleMoney = g_ms.saleMoney + mySaleMoney

            self.controlsession.add(g_ds)
            self.controlsession.add(g_ms)
            self.controlsession.commit()
        except CodeError as e:
            self.controlsession.rollback()
            raise
        except Exception, e:
            print traceback.format_exc()
            self.controlsession.rollback()


    def add_flagship_sale_set(self, uid, setId, flagShipId, mySaleMoney, myPercentageMoney, myday=None, ym=None):
        '''
        Function : 统计旗舰店的套餐销售
        :return:
        '''
        try:
            cdssquery = self.controlsession.query(ClerkDailySaleSet)
            cmssquery = self.controlsession.query(ClerkMonthSaleSet)

            c_dss = cdssquery.filter_by(userId=uid, dayTime=myday, setTypeId=setId, shipId=flagShipId).scalar()
            c_mss = cmssquery.filter_by(userId=uid, yearMonth=ym, setTypeId=setId, shipId=flagShipId).scalar()

            if not c_dss:
                c_dss = ClerkDailySaleSet(userId=uid, setTypeId=setId, shipId=flagShipId, dayTime=myday, orderCount=1,
                                          saleMoney=mySaleMoney, percentageMoney=myPercentageMoney)
            else:
                c_dss.orderCount = c_dss.orderCount + 1
                c_dss.saleMoney = c_dss.saleMoney + mySaleMoney
                c_dss.percentageMoney = c_dss.percentageMoney + myPercentageMoney

            if not c_mss:
                c_mss = ClerkMonthSaleSet(userId=uid, setTypeId=setId, shipId=flagShipId, yearMonth=ym, orderCount=1,
                                          saleMoney=mySaleMoney, percentageMoney=myPercentageMoney)
            else:
                c_mss.orderCount = c_mss.orderCount + 1
                c_mss.saleMoney = c_mss.saleMoney + mySaleMoney
                c_mss.percentageMoney = c_mss.percentageMoney + myPercentageMoney

            self.controlsession.add(c_dss)
            self.controlsession.add(c_mss)
            self.controlsession.commit()
        except CodeError as e:
            self.controlsession.rollback()
            raise
        except Exception, e:
            print traceback.format_exc()
            self.controlsession.rollback()