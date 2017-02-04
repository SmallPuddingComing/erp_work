#-*- coding:utf-8 -*-

import json

from control_center.shop_manage.good_info_manage.control.mixOp import HolaWareHouse
from data_mode.hola_flagship_store.control_base.controlBase import ControlEngine
from data_mode.hola_flagship_store.mode.ship_model.flagship_clerk_info import Clerk
from data_mode.hola_flagship_store.mode.ship_model.flagship_store_info import FlagShipStoreInfo
from data_mode.user_center.control.mixOp import MixUserCenterOp


class FlagShipOp(ControlEngine):
    def __init__(self):
        ControlEngine.__init__(self)

    def get_flagship_info(self, fs_id):
        '''
        返回某个旗舰店的信息
        :param fs_id: 旗舰店id
        :return: dict
        '''
        rs = self.controlsession.query(FlagShipStoreInfo).get(fs_id)
        print rs
        if rs:
            rs = rs.to_json()
            mc = MixUserCenterOp()
            leader_id = rs.get('leader')
            name = ""
            gander = 0
            telephone = ""
            if leader_id != 0:
                user_info = mc.get_user_info(leader_id)
                gander = user_info.get("gander")
                name = user_info.get("name")
                telephone = user_info.get("telephone")
            rs["leader_name"] = name
            rs["gander"] = gander
            rs["leader_telephone"] = telephone
            rs.pop('leader')
            return rs
        else:
            return {}


    def save_flagship_info(self, fs_id, telephone, leader_telephone):
        '''
        保存旗舰店信息
        :param fs_id: 旗舰店id
        :param telephone: 服务电话
        :param leader_telephone: 店长电话
        :return: bool
        '''
        try:
            rs = self.controlsession.query(FlagShipStoreInfo).filter_by(id = fs_id).first()
            if rs:
                rs.telephone = telephone
                mc = MixUserCenterOp()
                mc.up_user_telephone(rs.id, leader_telephone)
                self.controlsession.commit()
                return json.dumps({"code": 100})
        except Exception,e:
            print e
            return json.dumps({"code": 300})

    # def add_flagship_info(self, flag_obj):
    #     self.controlsession.add(flag_obj)
    #     self.controlsession.commit()

    def get_clerk_info(self, fs_id):
        '''

        :param fs_id:
        :return:
        '''
        rs = self.controlsession.query(FlagShipStoreInfo).get(fs_id)
        t = rs.id.clerk_info
        print t

    def getFlagshipNameById(self, flagshipid):
        '''
        @function : 根据销旗舰店id获得旗舰店名字
        :param flagshipid: 旗舰店id
        :return:
        '''
        try:
            dict = self.get_flagship_info(flagshipid)
            if dict is not None:
                return dict['name']
            else:
                ValueError('flagship is not exist!')
        except Exception as e:
            print e
            raise


class ClerkOp(ControlEngine):
    def __init__(self):
        ControlEngine.__init__(self)

    def add_clerk(self,clerk_obj):
        self.controlsession.add(clerk_obj)
        self.controlsession.commit()

    def add_one_clerk(self, user_id, product_id, floor_price, commission_amount):
        clerk = Clerk(user_id=user_id, product_id=product_id, floor_price=floor_price, commission_amount=commission_amount )
        self.controlsession.add(clerk)
        self.controlsession.commit()


    def get_clerk_info(self, fg_id):
        '''
        获取旗舰店下所有店员信息
        :param fg_id: 旗舰店id
        :return: json
        '''
        rs = self.controlsession.query(Clerk).filter(Clerk.store_id == fg_id).all()
        rs  = [item.to_json() for item in rs]
        print rs
        mc = MixUserCenterOp()
        data = []
        for item in rs:
            user_info = mc.get_user_info(item.get('user_id'))
            user_info["discount_rate"] = item.get('discount_rate')
            user_info["clerk_id"] = item.get('id')
            data.append(user_info)

        return json.dumps(data)


    def get_clerks_info(self, fg_id):
        from control_center.flagship_manage.flagship_info_manage.control.flagship_op import FlagShipOp
        f_op = FlagShipOp()
        users_info = f_op.get_flagship_users(fg_id)
        return users_info


    # def get_clerk_info_by_uid(self, uid):
    #     clerk = self.controlsession.query(Clerk).filter(Clerk.user_id== uid).first()
    #     if clerk is None:
    #         return {
    #             'id' : 0 ,
    #             'discount_rate': 100,
    #         }
    #     return clerk.to_json()
    def get_clerk_product_info(self, uid, flagshipid):
        data = {}
        warehouse_op = HolaWareHouse()
        product_info = warehouse_op.get_all_product_dict_info()
        product_price = warehouse_op.get_product_price(flagshipid)
        # from pprint import pprint
        # pprint(product_price)
        clerks_info = self.controlsession.query(Clerk).filter(Clerk.user_id== uid).all()
        clears_data = []
        for clerk in clerks_info:
            if not product_info.has_key(clerk.product_id):
                continue
            clear_data = clerk.to_json()
            clear_data['price'] = product_info[clerk.product_id]['price']
            clear_data['name'] = product_info[clerk.product_id]['name']
            clear_data['code'] = product_info[clerk.product_id]['code']
            clear_data['category'] = product_info[clerk.product_id]['category']
            clear_data['img'] = product_info[clerk.product_id]['img']
            if product_price.has_key(clerk.product_id):
                clear_data['flagship_price'] = product_price[clerk.product_id]['floor_price']
            else:
                clear_data['flagship_price'] = None
            clears_data.append(clear_data)
        user_op = MixUserCenterOp()
        data['user_info'] = user_op.get_user_info(uid)
        data['product_info'] = clears_data
        return data

    def edit_clerk_price_info(self, user_id, product_id, floor_price, untify_price ):
        clear_info = self.controlsession.query(Clerk).filter(Clerk.user_id== user_id, Clerk.product_id == product_id).first()
        if clear_info is None:
            clear_info = Clerk(user_id=user_id, product_id=product_id, floor_price=floor_price)
        else:
            clear_info.floor_price = floor_price
        self.controlsession.add(clear_info)
        self.controlsession.commit()


    def save_discount_rate(self, clerk_id, discount_rate):
        '''
        保存折扣额度
        :param clerk_id: 店员id
        :param discount_rate: 折扣额度
        :return: json
        '''
        try:
            cl = self.controlsession.query(Clerk).get(clerk_id)
            cl.discount_rate = discount_rate
            self.controlsession.commit()
            return json.dumps({"code": 100})
        except Exception,e:
            print e
            return json.dumps({"code": 300})



##---------------------------------------------------------##
# class FlagSaleFeatureOp(ControlEngine):
#     def __init__(self):
#         ControlEngine.__init__(self)
#
#     def GetFeature(self):
#         featureList = self.controlsession.query(FlagSaleFeature).all()
#         if not featureList:
#             print("[FlagSaleFeatureOp.GetFeature] sale feature data is null")
#             return
#         featureList = [item.ToJson() for item in featureList]
#         return featureList
#
#     #保存对象
#     def SaveObject(self, obj):
#         try:
#             self.controlsession.add(obj)
#             self.controlsession.commit()
#         except Exception,e:
#             print(e)
#             self.controlsession.rollback()
#
#     #保存对象
#     def SaveObjects(self,objsList):
#         try:
#             for obj in objsList:
#                 self.controlsession.add(obj)
#             self.controlsession.commit()
#         except Exception,e:
#             print(e)
#             self.controlsession.rollback()
#
#     #添加特征对象根据名字
#     def AddFeatureObjectByNames(self, nameList):
#         if not nameList:
#             return
#
#         for v in nameList:
#             object = FlagSaleFeature(name=v)
#             self.SaveObject(object)


# ##----------------------------------------------------`-----##
# class FlagshipFreeProductOp(ControlEngine):
#     def __init__(self):
#         ControlEngine.__init__(self)
#
#     #保存对象
#     def SaveObject(self, obj):
#         try:
#             self.controlsession.add(obj)
#             self.controlsession.commit()
#         except Exception,e:
#             print(e)
#             self.controlsession.rollback()
#
#     #保存对象
#     def SaveObjects(self,objsList):
#         try:
#             for obj in objsList:
#                 self.controlsession.add(obj)
#             self.controlsession.commit()
#         except Exception,e:
#             print(e)
#             self.controlsession.rollback()
#
#     #获取已经销售的产品信息
#     def GetGoodsBySn(self, pDeviceSn):
#         goodsInfo = self.controlsession.query(FlagshipFreeProduct).filter_by(pDeviceSn = pDeviceSn).first()
#         if not goodsInfo:
#             #print("[FlagshipFreeProductOp.GetGoodsBySn] data not find ","pDeviceSn = ",pDeviceSn)
#             return
#         goodsInfo = goodsInfo.ToJson()
#         return goodsInfo
#
#     def GetFreeItemListByOrderId(self,orderId):
#         freeItemList = self.controlsession.query(FlagshipFreeProduct).filter_by(orderId = orderId).all()
#         if not freeItemList:
#             return
#
#         freeItemList = [item.ToJson() for item in freeItemList]
#         return freeItemList

##---------------------------------------------------------##
# class FlagshipOrderInfoOp(ControlEngine):
#     def __init__(self):
#         ControlEngine.__init__(self)
#
#     #保存对象
#     def SaveObject(self, obj):
#         try:
#             self.controlsession.add(obj)
#             self.controlsession.commit()
#         except Exception,e:
#             print(e)
#             self.controlsession.rollback()
#
#     #保存对象
#     def SaveObjects(self,objsList):
#         try:
#             for obj in objsList:
#                 self.controlsession.add(obj)
#             self.controlsession.commit()
#         except Exception,e:
#             print(e)
#             self.controlsession.rollback()
#
#     def get_order_info_by_salepersionid(self, sale_uid, page=1, nums=12):
#         data = self.controlsession.query(FlagshipOrderInfo).filter(FlagshipOrderInfo.salePersonUID == sale_uid, FlagshipOrderInfo.payStatus == 1, or_(FlagshipOrderInfo.saleIsCheck == 100, FlagshipOrderInfo.saleIsCheck == 150)).all()
#         total_pages = len(data) / nums + 1
#         data = self.controlsession.query(FlagshipOrderInfo).filter(FlagshipOrderInfo.salePersonUID == sale_uid, FlagshipOrderInfo.payStatus == 1, or_(FlagshipOrderInfo.saleIsCheck == 100, FlagshipOrderInfo.saleIsCheck == 150)).limit(nums).offset((page-1)*nums).all()
#         return total_pages, [item.ToJson() for item in data]
#
#     def up_order_check_status_by_order_id(self, order_id_list, statue):
#
#         rs = self.controlsession.query(FlagshipOrderInfo).filter(FlagshipOrderInfo.orderId.in_(order_id_list)).all()
#         if len(rs)>=1:
#             for item in rs:
#                 item.saleIsCheck = statue
#                 item.checkTime = int(time.time())
#                 self.controlsession.commit()
#             return True
#         else:
#             return False
#
#     def get_sale_all_checked_order_info_by_timestramp(self, sale_uid, s_time, e_time, page=1, nums=12):
#         rs = self.controlsession.query(FlagshipOrderInfo).filter(FlagshipOrderInfo.salePersonUID == sale_uid, FlagshipOrderInfo.checkTime>= s_time, FlagshipOrderInfo.checkTime< e_time, FlagshipOrderInfo.saleIsCheck >= 200).limit(nums).offset((page-1)*nums).all()
#         print "rs",rs
#         rs = [item.ToJson() for item in rs]
#         return rs
#
#
#     # def get_personal_sale_records(self, user_id, s_time, e_time, page=1, nums=20):
#     #     rs = self.controlsession.query(FlagshipOrderInfo.orderId).filter(FlagshipOrderInfo.salePersonUID == user_id, FlagshipOrderInfo.payTime>= s_time, FlagshipOrderInfo.payTime< e_time).all()
#     #     total_pages = len(rs)/nums + 1
#     #     rs = self.controlsession.query(FlagshipOrderInfo).filter(FlagshipOrderInfo.salePersonUID == user_id, FlagshipOrderInfo.payTime>= s_time, FlagshipOrderInfo.payTime< e_time).limit(nums).offset((page-1)*nums).all()
#     #     # 订单下所有商品
#     #     data = []
#     #     for item in rs:
#     #         dict = {}
#     #         order_product = self.controlsession.query(FlagshipOrderProduct).filter(FlagshipOrderProduct.orderId == item.orderId).first()
#     #         if not order_product:
#     #             data.append(dict)
#     #             continue
#     #         # 订单id
#     #
#     #         dict["order_id"] = item.orderId
#     #         # 商品基本信息
#     #         hw = HolaWareHouse()
#     #         product_info = hw.get_product_info(order_product.productId)
#     #         dict["product_name"] = product_info.get("product_name")
#     #         dict["category_name"] = product_info.get("category_name")
#     #
#     #         # 已付金额
#     #         dict["moneyPaid"] = item.moneyPaid
#     #
#     #         # 商品sn
#     #         dict["pDeviceSn"] = order_product.pDeviceSn
#     #
#     #         # 销售时间
#     #         dict["payTime"] = item.payTime
#     #
#     #         # 订单提成
#     #         fs = FlagshipOrderProductOp()
#     #         dict["rewards"] = fs.get_order_reward_by_order_id(item.orderId)
#     #         from control_center.departments.flagship.mode.flagshipOrderInfoModel import CheckState
#     #         dict["check_status_name"] = CheckState.check_dict[300] if item.saleIsCheck <= 300 else CheckState.check_dict[400]
#     #         # 获取买家名称
#     #         fs_op = FlagShipCustomOp()
#     #         dict["custom_info"] = fs_op.GetCustomInfoByCustomId(item.customId)
#     #         data.append(dict)
#     #
#     #     return {"total_pages":total_pages, "current_page": page,"per_page_nums": nums,"data":data}
#     #     pass
#
#     # def get_personal_sale_record_details(self, order_id):
#     #     dict = {}
#     #     order_info = self.controlsession.query(FlagshipOrderInfo).filter(FlagshipOrderInfo.orderId == order_id).first()
#     #     order_product = self.controlsession.query(FlagshipOrderProduct).filter(FlagshipOrderProduct.orderId == order_id).first()
#     #     # 订单基本信息
#     #     dict["order_info"] = order_info.ToJson()
#     #     # 支付方式
#     #     paytype = FlagshipPayTypeOp()
#     #     dict["pay_type_info"] = paytype.GetPayTypeById(order_info.payType)
#     #
#     #     # 商品基本信息
#     #     hw = HolaWareHouse()
#     #     product_info = hw.get_product_info(order_product.productId)
#     #     dict["product_name"] = product_info.get("product_name")
#     #     dict["category_name"] = product_info.get("category_name")
#     #     dict["price"] = product_info.get("price")
#     #
#     #     # 商品sn
#     #     dict["pDeviceSn"] = order_product.pDeviceSn
#     #
#     #     # 旗舰店信息
#     #     falgship = flagship_op()
#     #     dict["flagship_info"] = falgship.get_flagship_info_by_flagship_id(order_info.shipId)
#     #
#     #     # 赠品信息
#     #     fs_free = FlagshipFreeProductOp()
#     #     dict["free_product_info"] = fs_free.GetFreeItemListByOrderId(order_id)
#     #
#     #     # 客户姓名
#     #     fs_op = FlagShipCustomOp()
#     #     custom_info = fs_op.GetCustomInfoByCustomId(order_info.customId)
#     #     dict["custom_info"] = custom_info
#     #
#     #     # 本单额外提成
#     #     fs = FlagshipOrderProductOp()
#     #     dict["rewards"] = fs.get_order_reward_by_order_id(order_id)
#     #     from control_center.departments.flagship.mode.flagshipOrderInfoModel import CheckState
#     #     dict["check_status_name"] = CheckState.check_dict[300] if order_info.saleIsCheck <= 300 else CheckState.check_dict[400]
#     #
#     #     return dict
#
#     def get_order_info_of_range_time(self, store_id, s_time, e_time):
#         if store_id * s_time * e_time <=0:
#             return 0,0
#
#         # 顾客量
#         custom_num = self.controlsession.query(func.count(distinct(FlagshipOrderInfo.customId))).\
#             filter(FlagshipOrderInfo.shipId == store_id, FlagshipOrderInfo.payTime>= s_time, FlagshipOrderInfo.payTime< e_time).scalar()
#
#         # 订单数
#         order_num = self.controlsession.query(func.count(distinct(FlagshipOrderInfo.orderId))).\
#             filter(FlagshipOrderInfo.shipId == store_id, FlagshipOrderInfo.payTime>= s_time, FlagshipOrderInfo.payTime< e_time).scalar()
#         return int(custom_num), int(order_num)
#
#
#     def GetOrderBySN(self, orderSn):
#         order = self.controlsession.query(FlagshipOrderInfo).filter(FlagshipOrderInfo.orderSn == orderSn).first()
#         if not order:
#             #print("[FlagshipOrderInfoOp.GetOrderBySN] data not find ","orderSn = ",orderSn)
#             return
#         return order.ToJson()
#
#     #商品出库
#     def out_product_from_warehouse(self,userId,deviceSn,reasonId,retDataList, outLogList=None):
#
#         #self.controlsession
#         if userId*reasonId <= 0 or not len(deviceSn):
#             print("[out_product_from_warehouse] input param is error","userId",userId,"deviceSn",deviceSn,"reasonId",reasonId)
#             retDataList["code"] = ServiceCode.params_error
#             retDataList["msg"] = u"出库失败! 传入参数有误！deviceSn = %s reasonId = %d"%(deviceSn,reasonId)
#             return False
#
#         #入库表修改-1
#         goodsInfo = self.controlsession.query(In_Warehouse).filter(In_Warehouse.pDeviceSn == deviceSn).first()
#         if not goodsInfo:
#             print("[out_product_from_warehouse] goods is not exist","userId",userId,"deviceSn",deviceSn,"reasonId",reasonId)
#             retDataList["code"] = ServiceCode.goodsSnNotExist
#             retDataList["msg"] = u"出库失败! 入库表中不存在此物品！deviceSn = %s reasonId = %d"%(deviceSn,reasonId)
#             return False
#
#         #入库表肯定要有该记录
#         # if not goodsInfo.num:
#         #     print("[out_product_from_warehouse] Storage table must have the record","userId",userId,"deviceSn",deviceSn,"reasonId",reasonId,"goodsInfo.num",goodsInfo.num)
#         #     return False
#
#         inGoodsId = goodsInfo.id
#         productId = goodsInfo.product_id
#         flagshipId = goodsInfo.store_id
#         fromWarehouseId = goodsInfo.warehouse_id
#         goodsInfo.updatetime = int(time.time())
#         goodsInfo.num = 0
#         self.controlsession.flush()
#
#
#         #出库表修改+1
#         outGoodsInfo = self.controlsession.query(Out_Warehouse).filter(Out_Warehouse.in_warehouse_id == inGoodsId).first()
#         if not outGoodsInfo:
#             owobj = Out_Warehouse(in_warehouse_id=inGoodsId,reason_id=reasonId,user_id=userId,num=1,addtime=int(time.time()))
#             self.controlsession.add(owobj)
#         elif not outGoodsInfo.num:
#             outGoodsInfo.num = 1
#         else:
#             outGoodsInfo.num = outGoodsInfo.num+1
#
#         self.controlsession.flush()
#
#
#         #库存表减一
#         fromWarehouseInfo = self.controlsession.query(WareHouse).filter(and_(WareHouse.store_id==flagshipId,WareHouse.warehouse_id==fromWarehouseId,WareHouse.product_id==productId)).first()
#         if not fromWarehouseInfo:
#             print("[out_product_from_warehouse]Inventory does not exist items","userId",userId,"deviceSn",deviceSn,"reasonId",reasonId)
#             retDataList["code"] = ServiceCode.goodsSnNotExist
#             retDataList["msg"] = u"出库失败! 库存中物品不存在！deviceSn = %s reasonId = %d store_id = %d"%(deviceSn,reasonId,flagshipId)
#             return False
#
#         #库存表肯定要有数量
#         if not fromWarehouseInfo.num:
#             print("[out_product_from_warehouse]There must be a number of inventory","userId",userId,"deviceSn",deviceSn,"reasonId",reasonId)
#             retDataList["code"] = ServiceCode.goodsSnNotExist
#             retDataList["msg"] = u"出库失败! 库存中物品数量不足！deviceSn = %s reasonId = %d store_id = %d"%(deviceSn,reasonId,flagshipId)
#             return False
#
#         fromWarehouseInfo.num = fromWarehouseInfo.num-1
#         #日志表添加
#         log_obj = WareHouseLog(store_id = flagshipId, product_sn = deviceSn, op_type = WareHouseLogOp.SALE_SUCCESS, remark = u'成功销售', clerk_id = userId, addtime = int(time.time()))
#         self.controlsession.add(log_obj)
#
#         if outLogList is not None:
#             outLogList.append(log_obj)
#
#         retDataList["code"] = ServiceCode.success
#         retDataList["msg"] = u"出库成功"
#         return True
#
#     #生成订单SN
#     def GenerateOrderSn(self, shipId, orderId):
#         #参数校验
#         if (not shipId) or (0 >= shipId) or (not orderId) or (0 >= orderId):
#             print("[GenerateOrderSn]  input param is error", "shipId = ",shipId, "orderId = ",orderId)
#             return
#
#         #获取当前日期
#         date = datetime.datetime.now()
#         strYear = str(date.year)
#         strMonth = (9 > date.month) and "0%d"%date.month or "%d"%date.month
#         strDay = (9 > date.day) and "0%d"%date.day or "%d"%date.day
#         strDate = strYear+strMonth+strDay
#
#         strShipId = str(shipId)
#         nShipLen = len(strShipId)
#         if nShipLen < 4:
#             diffLen = 4 - nShipLen
#             tmpStr1 = ""
#             for v in range(0,diffLen):
#                 tmpStr1 += str(0)
#             strShipId = tmpStr1+strShipId
#
#         strOrderId = str(orderId)
#         nOrderLen = len(strOrderId)
#         if nOrderLen < 4:
#             diffLen = 4 - nOrderLen
#             tmpStr2 = ""
#             for v in range(0,diffLen):
#                 tmpStr2 += str(0)
#             strOrderId = tmpStr2+strOrderId
#
#         return strShipId+strDate+strOrderId+"98"
#
#
#
#     #确保参数列表合法性
#     # def HandleOrder(self, param, retDataList):
#     #     baseGoods = param.get('baseGoods')
#     #     user = param.get('user')
#     #     goodsSn = param.get('goodsSn')
#     #     shipId = param.get('shipId')
#     #     customName = param.get('customName')
#     #     phone = param.get('phone')
#     #     flag = param.get('flag')
#     #     addr = param.get('addr')
#     #     sex = param.get('sex')
#     #     moneyPaid = param.get('moneyPaid')
#     #     couponNumber = param.get('couponNumber')
#     #     invoiceNumber = param.get('invoiceNumber')
#     #     serialNumber = param.get('serialNumber')
#     #     payBank = param.get('payBank')
#     #     freeGoodsArray = param.get('freeGoodsArray')
#     #     payType = param.get('payType')
#     #     addTime = time.time()  #支付时间
#     #     try:
#     #          #-----添加用户信息-----
#     #         custom = self.controlsession.query(FlagShipCustom).filter(FlagShipCustom.phone == phone).first()
#     #         if custom: #用户已经存在，更新数据
#     #              custom.customId = custom.customId
#     #              custom.addr = addr
#     #              custom.flag = flag
#     #              self.controlsession.add(custom)
#     #         else:
#     #             customObject = FlagShipCustom(shipId = shipId, customName = customName, phone = phone, sex = sex, flag = flag, addr = addr)
#     #             self.controlsession.add(customObject)
#     #         #-----添加订单详情-----
#     #         custom = self.controlsession.query(FlagShipCustom).filter(FlagShipCustom.phone == phone).first()
#     #         orderObject = FlagshipOrderInfo(orderSn = "", shipId = shipId, orderStatus = OrderState.SUCCESS, moneyPaid = moneyPaid,orderAmount = moneyPaid,
#     #                                       addTime = addTime, confirmTime = addTime, payTime = addTime, payStatus = PayState.PAY_SUCCESS, payType = payType,
#     #                                       serialNumber = serialNumber, payBank = payBank, couponNumber = couponNumber, invoiceNumber = invoiceNumber, salePersonUID = user.get('id'), customId = custom.customId, saleIsCheck = 100)
#     #         self.controlsession.add(orderObject)
#     #
#     #         retailPrice = baseGoods.get('price')
#     #         retailPrice = retailPrice and retailPrice or 0
#     #         orderProductObject = FlagshipOrderProduct(orderId = orderObject.orderId, productId = baseGoods.get('id'), pDeviceSn = goodsSn, retailPrice = retailPrice, salePrice = moneyPaid)
#     #         self.controlsession.add(orderProductObject)
#     #
#     #         outLogList = []
#     #         rcode = self.out_product_from_warehouse(userId = user.get('id'),deviceSn=goodsSn,reasonId=ReasonTypes.common_out,retDataList=retDataList, outLogList=outLogList)
#     #         if not rcode:
#     #             print("userId = ", user.get('id'), "goodsSn = ", goodsSn, "shipId",shipId)
#     #             raise Exception('Order products out_warehouse error!')
#     #
#     #         #-----赠品操作-----
#     #         freeGoodsList = []
#     #         if 0 < len(freeGoodsArray):
#     #             for v in freeGoodsArray:
#     #                 product = FlagshipFreeProduct(orderId = orderObject.orderId, productId = freeGoodsArray[v].get('productId'), pDeviceSn = freeGoodsArray[v].get('goodsSn'), retailPrice = freeGoodsArray[v].get('price'))
#     #                 self.controlsession.add(product)
#     #                 freeGoodsList.append(product)
#     #
#     #                 #库存减少
#     #                 rs = self.controlsession.query(In_Warehouse).filter(In_Warehouse.pDeviceSn == freeGoodsArray[v].get('goodsSn')).all()
#     #                 rs[0].num -= 1
#     #                 rs[0].updatetime = int(time.time())
#     #
#     #                 #出库登记
#     #                 rcode = self.out_product_from_warehouse(userId = user.get('id'),deviceSn=freeGoodsArray[v].get('goodsSn'),reasonId=ReasonTypes.common_out,retDataList=retDataList, outLogList=outLogList)
#     #                 if not rcode:
#     #                     print("userId = ", user.get('id'), "freeGoodsSn = ", freeGoodsArray[v].get('goodsSn'), "shipId", shipId)
#     #                     raise Exception('Order free_products out_warehouse error!')
#     #
#     #
#     #         #-----登记销售数据-----
#     #         pHolaWareHouse = HolaWareHouse()
#     #         categoryInfo = baseGoods.get('category',{})
#     #         percentage = pHolaWareHouse.get_commission_amount_by_flagship_product(shipId, baseGoods.get('id')) #获取产品提成
#     #         self.AddFlagShipSale(user.get('id'), baseGoods.get('id'), shipId, moneyPaid, percentage, categoryInfo.get('id',0))
#     #         self.controlsession.commit()
#     #
#     #         #################只有先提交订单数据了才能获取递增的订单号######################
#     #         #生成订单SN
#     #         orderSn = self.GenerateOrderSn(shipId, orderObject.orderId)
#     #         orderObject.orderSn = orderSn
#     #         #物品订单号
#     #         orderProductObject.orderId = orderObject.orderId
#     #         #赠品订单号
#     #         for v in freeGoodsList:
#     #              v.orderId = orderObject.orderId
#     #
#     #         #更新出库日志
#     #         for v in outLogList:
#     #             v.custom_id  = custom.customId
#     #             v.custom_name = custom.customName
#     #
#     #         self.controlsession.commit()
#     #
#     #         #填充返回值参数
#     #         param['orderId'] = orderObject.orderId
#     #         param['orderSn'] = orderSn
#     #     except Exception,e:
#     #         print(e)
#     #         self.controlsession.rollback()
#     #         return False
#     #     return True
#
#     def AddFlagShipSale(self,uid,productId,flagShipId,mySaleMoney,myPercentageMoney,myCategoryId):
#         gdsquery = self.controlsession.query(GlobalDailySale)
#         gmsquery = self.controlsession.query(GlobalMonthSale)
#         cdsquery = self.controlsession.query(ClerkDailySale)
#         cmsquery = self.controlsession.query(ClerkMonthSale)
#         hwop = HolaWareHouse()
#         ancestorId = hwop.get_category_ancestor(myCategoryId)
#
#         myday = get_current_date()
#         ym = get_current_month()
#         g_ds = gdsquery.filter_by(productTypeId=productId,dayTime=myday,shipId=flagShipId).scalar()
#         g_ms = gmsquery.filter_by(productTypeId=productId,yearMonth=ym,shipId=flagShipId).scalar()
#         c_ds = cdsquery.filter_by(userId=uid,dayTime=myday,productTypeId=productId,shipId=flagShipId).scalar()
#         c_ms = cmsquery.filter_by(userId=uid,yearMonth=ym,productTypeId=productId,shipId=flagShipId).scalar()
#
#         if not g_ds:
#             g_ds = GlobalDailySale(productTypeId=productId,categoryId=ancestorId,dayTime=myday,shipId=flagShipId,saleCount=1,saleMoney=mySaleMoney)
#         else:
#             g_ds.saleCount = g_ds.saleCount+1
#             g_ds.saleMoney = g_ds.saleMoney+mySaleMoney
#
#         if not g_ms:
#             g_ms = GlobalMonthSale(productTypeId=productId,categoryId=ancestorId,yearMonth=ym,shipId=flagShipId,saleCount=1,saleMoney=mySaleMoney)
#         else:
#             g_ms.saleCount = g_ms.saleCount+1
#             g_ms.saleMoney = g_ms.saleMoney+mySaleMoney
#
#         if not c_ds:
#             c_ds = ClerkDailySale(userId=uid,productTypeId=productId,shipId=flagShipId,dayTime=myday,orderCount=1,saleMoney=mySaleMoney,percentageMoney=myPercentageMoney)
#         else:
#             c_ds.orderCount = c_ds.orderCount+1
#             c_ds.saleMoney = c_ds.saleMoney+mySaleMoney
#             c_ds.percentageMoney = c_ds.percentageMoney+myPercentageMoney
#
#         if not c_ms:
#             c_ms = ClerkMonthSale(userId=uid,productTypeId=productId,shipId=flagShipId,yearMonth=ym,orderCount=1,saleMoney=mySaleMoney,percentageMoney=myPercentageMoney)
#         else:
#             c_ms.orderCount = c_ms.orderCount+1
#             c_ms.saleMoney = c_ms.saleMoney+mySaleMoney
#             c_ms.percentageMoney = c_ms.percentageMoney+myPercentageMoney
#
#         self.controlsession.add(g_ds)
#         self.controlsession.add(g_ms)
#         self.controlsession.add(c_ds)
#         self.controlsession.add(c_ms)


##---------------------------------------------------------##
# class FlagshipOrderProductOp(ControlEngine):
#     def __init__(self):
#         ControlEngine.__init__(self)
#
#     #保存对象
#     def SaveObject(self, obj):
#         try:
#             self.controlsession.add(obj)
#             self.controlsession.commit()
#         except Exception,e:
#             print(e)
#             self.controlsession.rollback()
#
#     #保存对象
#     def SaveObjects(self,objsList):
#         try:
#             for obj in objsList:
#                 self.controlsession.add(obj)
#             self.controlsession.commit()
#         except Exception,e:
#             print(e)
#             self.controlsession.rollback()
#
#     #获取已经销售的产品信息
#     def GetGoodsBySn(self, pDeviceSn):
#         goodsInfo = self.controlsession.query(FlagshipOrderProduct).filter(FlagshipOrderProduct.pDeviceSn == pDeviceSn).first()
#         if not goodsInfo:
#             #print("[FlagshipOrderProductOp.GetGoodsBySn] data not find ","pDeviceSn = ",pDeviceSn)
#             return
#         return goodsInfo.ToJson()
#
#
#     def get_order_reward_by_order_id(self, order_id):
#         '''
#         根据订单id 获取该订单奖励
#         :param order_id: 订单id
#         :return: 奖励
#         '''
#         rs = self.controlsession.query(FlagshipOrderProduct).filter(FlagshipOrderProduct.orderId == order_id).first()
#         if rs:
#             hw = HolaWareHouse()
#             rs = hw.get_product_reward_by_product_id(rs.ToJson().get("productId"))
#             return rs
#         else:
#             return 0
##---------------------------------------------------------##
# class FlagshipSalePercentageOp(ControlEngine):
#     def __init__(self):
#         ControlEngine.__init__(self)
#
#     #保存对象
#     def SaveObject(self, obj):
#         try:
#             self.controlsession.add(obj)
#             self.controlsession.commit()
#         except Exception,e:
#             print(e)
#             self.controlsession.rollback()
#
#     #保存对象
#     def SaveObjects(self,objsList):
#         try:
#             for obj in objsList:
#                 self.controlsession.add(obj)
#             self.controlsession.commit()
#         except Exception,e:
#             print(e)
#             self.controlsession.rollback()
#
#     #获取员工销售的商品的信息
#     def GetStaffSaleInfo(self, account, shipId, goodsSn):
#         staffSaleInfo = self.controlsession.query(FlagshipSalePercentage).filter(FlagshipSalePercentage.account == account, FlagshipSalePercentage.shipId == shipId, FlagshipSalePercentage.goodSn == goodsSn).first()
#         if not staffSaleInfo:
#             print("[FlagshipSalePercentageOp.GetStaffSaleInfo] data not find ","account = ",account, "shipId", shipId, "goodsSn", goodsSn)
#             return
#
#         return staffSaleInfo.ToJson()
#
#     #获取提成
#     def GetStaffSalePercentage(self, account, shipId, goodsSn):
#         staffGoodsInfo = self.GetStaffSaleInfo(account, shipId, goodsSn)
#         if not staffGoodsInfo:
#             print("[FlagshipSalePercentageOp.GetStaffSalePercentage] data not find ","account = ",account, "shipId", shipId, "goodsSn", goodsSn)
#             return 0
#
#         return staffGoodsInfo['percentage']

##---------------------------------------------------------##
# class FlagshipPayTypeOp(ControlEngine):
#      def __init__(self):
#         ControlEngine.__init__(self)
#
#      def GetPayTypeById(self, id):
#         type = self.controlsession.query(FlagshipPayType).filter_by(id = id).first()
#         return type.ToJson()
#
#      def GetPayTypeList(self):
#         typeList = self.controlsession.query(FlagshipPayType).all()
#         if not typeList:
#             #print("[FlagshipPayTypeOp.GetPayTypeList] data is not find")
#             return []
#         retData = []
#         for v in typeList:
#             data = \
#                 {
#                     'id':v.id,
#                     'payType':v.payType,
#                 }
#             retData.append(data)
#         return retData
#
#      def GetPayTypeDict(self):
#         typeList = self.controlsession.query(FlagshipPayType).all()
#         if not typeList:
#             #print("[FlagshipPayTypeOp.GetPayTypeList] data is not find")
#             return {}
#         return dict([(item.id,item.payType) for item in typeList])
#
#
#      def AddPayType(self, typeName):
#         if not typeName:
#             return
#         object = FlagshipPayType(payType = typeName)
#         try:
#             self.controlsession.add(object)
#             self.controlsession.commit()
#         except Exception,e:
#             print(e)
#             self.controlsession.rollback()
#
#      def AddPayTypeList(self, typeNameList):
#         if not typeNameList or 0 >= len(typeNameList):
#             return
#
#         list = []
#         for v in typeNameList:
#             object = FlagshipPayType(payType = v)
#             list.append(object)
#
#         for object in list:
#             try:
#                 self.controlsession.add(object)
#             except Exception,e:
#                 continue
#
#         if list:
#             try:
#                 self.controlsession.commit()
#             except Exception,e:
#                 print(e)
#                 self.controlsession.rollback()
if __name__ == '__main__':
    pass
    # oi = FlagshipOrderInfoOp()
    # print json.dumps(oi.get_order_info_by_salepersionid(2))
    # print json.dumps(oi.get_sale_all_checked_order_info_by_timestramp(2, 1468491669, 1468492569))

    # print json.dumps(oi.get_personal_sale_records(1,  1468466771, 1468466772,1,3))

    # fs_op = FlagShipCustomOp()
    # print fs_op.GetCustomInfoByCustomId(13)


    # fs = FlagshipOrderInfoOp()
    # print json.dumps(fs.get_personal_sale_record_details(24))
    # print fs.get_order_info_of_range_time( 2, 1469980800, 1470585599)

    # print oi.up_order_check_status_by_order_id([1, 2, 3, 4], 100)