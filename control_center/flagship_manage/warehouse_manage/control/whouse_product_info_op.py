#/usr/bin/python
#-*- coding:utf-8 -*-
#########################################################
#    Copyright(c) 2000-2013 JmGO Company
#    All rights reserved.
#
#    文件名 :   whouse_product_info_op.py
#    作者   :   ChengQian
#  电子邮箱 :   qcheng@jmgo.com
#    日期   :   2016/09/08 20:32:27
#
#    描述   :  店铺商品详情数据模型
#

import types
from sqlalchemy import and_
import traceback
from sqlalchemy import func, distinct
from control_center.flagship_manage.warehouse_manage.control.in_out_warehouse_op import InOutWarehouseOp
from data_mode.hola_flagship_store.control_base.controlBase import ControlEngine
from data_mode.hola_flagship_store.mode.warehouse_mode.warehouse_manage import Inventory
from data_mode.hola_flagship_store.mode.warehouse_mode.warehouse_manage import ProductRelation
from data_mode.hola_flagship_store.mode.warehouse_mode.warehouse_manage import WarehouseType
from public.exception.custom_exception import CodeError

class WhouseProductInfoOp(ControlEngine):
    def __init__(self):
        ControlEngine.__init__(self)


    def get_product_count(self,store_id, product_id):
        """
        param product_id: 产品ID（或指商品ID）
        :return: 根据制定的商品ID获取对应的商品库存量
        """
        # datas = self.controlsession.query(Inventory).filter_by(good_id=product_id).first()
        # if isinstance(datas, types.NoneType):
        #     return 0
        # else:
        #     if isinstance(datas.inventory_amount, types.NoneType):
        #         return 0
        #     else:
        #         return datas.inventory_amount
        inoutwarehouseop = InOutWarehouseOp()
        datas = inoutwarehouseop.InventoryCountInfo(store_id, WarehouseType.inventory_warehouse, product_id)
        print("----"*30+"---product counts:"+"--"*30)
        print(datas)
        return datas


    # def check_serialno(self,serialno):
    #     """
    #     :param store_id:    店铺id
    #     :param serialno:    商品的序列号
    #     :return:    判断即将售卖的商品在库中的状态
    #     """
    #     try:
    #         data = self.controlsession.query(ProductRelation).filter_by(number=serialno.strip()).all()
    #         if len(data)==0:
    #             return 0                #表示库存中没有该序列号对应的商品记录
    #         elif len(data) == 1:    #表示校验成功
    #             return 1
    #     except Exception, ex:
    #         return -1

    def get_serialno_flag(self, store_id, product_id, whouse_id):
        try:
            datas = self.controlsession.query(ProductRelation).filter_by(flagship_id=store_id, good_id=product_id,warehouse_type_id=whouse_id).first()
            if isinstance(datas, types.NoneType):
                return -1       #表示商品不存在
            else:
                print("-------type(datas.number):",type(datas.number))
                if datas.number==None:
                    return 0        #表示序列号不存在
                elif len((datas.number).strip()) == 0:
                    return 0
                else:
                    return 1        #表示序列号存在
        except Exception, ex:
            raise
            
    #def get_store_product_info(self,storeId=0,productId=0,num=10,page=0):
    def get_store_product_info(self,storeId=0,productId=0):
        
        if 0 == storeId:
            return ([],0)
        
        condition = 'Inventory.store_id==%s' % storeId
           
        if productId > 0:
            condition = condition+',Inventory.good_id==%s' % productId
            condition = 'and_('+condition+')'
        
        #off = num*page
        rs = self.controlsession.query(Inventory).filter(eval(condition)).order_by(Inventory.good_id.desc()).all()#.offset(off).limit(num).all()    
        
        total = 0
        mycount = self.controlsession.query(func.count(distinct(Inventory.good_id))).filter(eval(condition)).first()

        if None == mycount or not len(mycount) or None == mycount[0]:
            total = 0
        else:
            total = mycount[0]
        
        return (rs,total)
        
    def get_store_product_detail(self,storeId=0,wareType=0,productId=0,billNumber='',serialNumber='',num=10,page=0):



        rs_list = []
        total = 0
        try:
            if storeId*wareType*productId == 0:
                return ([],0)

            condition = 'ProductRelation.flagship_id==%s,ProductRelation.warehouse_type_id==%s,ProductRelation.good_id==%s' % (storeId,wareType,productId)

            condition = condition+',ProductRelation.num>0'

            if len(billNumber):
                condition = condition+",ProductRelation.order_number=='%s'" % billNumber

            countby = condition
            if len(serialNumber):
                condition = condition+",ProductRelation.number=='%s'" % serialNumber

            condition = 'and_('+condition+')'
            countby = 'and_('+countby+')'
            off = num*page
            # print '----------condition--------------',condition
            rs = self.controlsession.query(ProductRelation).\
                filter(eval(condition)).order_by(ProductRelation.id.asc()).offset(off).limit(num).all()
            if rs:
                rs_list = [item.to_json() for item in rs]
            else:
                raise CodeError(300,u"query ProductRelation error")
            total = self.controlsession.query(func.count(ProductRelation.id)).filter(eval(countby)).scalar()

            # print '----------------------------------------',rs_list,total
        except CodeError as e:
            print traceback.format_exc()
        
        return rs_list,total

