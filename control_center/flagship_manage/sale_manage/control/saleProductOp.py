#/usr/bin/python
#-*- coding:utf-8 -*-

import datetime
import traceback
import time, os
from flask import session
from sqlalchemy import and_, func
from sqlalchemy.exc import SQLAlchemyError

from operator import itemgetter
from itertools import groupby

from config.service_config.returncode import ServiceCode
from control_center.flagship_manage.flagship_info_manage.control.mixOp import ClerkOp, FlagShipOp
from control_center.flagship_manage.warehouse_manage.control.in_out_warehouse_op import InOutWarehouseOp
from control_center.shop_manage.good_info_manage.control.mixOp import HolaWareHouse
from data_mode.hola_flagship_store.control_base.controlBase import ControlEngine
from data_mode.hola_flagship_store.mode.sale_mode.customer_info import CustomerInfo
from data_mode.hola_flagship_store.mode.sale_mode.pay_type import NewPayType
from data_mode.hola_flagship_store.mode.sale_mode.sale_order import SaleOrder
from data_mode.hola_flagship_store.mode.sale_mode.sale_order_detail import SaleOrderDetail
from data_mode.hola_flagship_store.mode.sale_mode.set_product_record import SetProductRecord
from data_mode.hola_flagship_store.mode.sale_mode.set_record_info import SetRecordInfo
from data_mode.hola_flagship_store.mode.warehouse_mode.warehouse_manage import *
from data_mode.hola_flagship_store.mode.warehouse_mode.warehouse_manage import ProductRelation, Inventory
from public.exception.custom_exception import CodeError
from config.share.share_define import *
from public.statement.engine import StatementEngine


class SaleOrderOp(ControlEngine):
    '''operation sale_order table'''
    def __init__(self):
        '''控制引擎初始化'''
        ControlEngine.__init__(self)

    @property
    def SEND(self):
        return ALREADY_OUT_WAREHOUSE

    @property
    def NOSEND(self):
        return NOT_OUT_WAREHOUSE

    def getSendStateBySendType(self, sendType):
        '''
        @function :根据配送类型id获得配送状态
        :param sendType:
        :return:
        '''
        if sendType == '1':
            return self.getSendState(NOT_OUT_WAREHOUSE_ID)
        elif sendType == '2':
            return self.getSendState(ALREADY_OUT_WAREHOUSE_ID)

    def getSendState(self, state_id):
        '''
        @function :根据配送状态id获得配送状态
        :param state_id:
        :return:
        '''
        if state_id == ALREADY_OUT_WAREHOUSE_ID:  # '01','02'放进公共模块中
            return NOT_OUT_WAREHOUSE  # 放进公共模块中
        elif state_id == NOT_OUT_WAREHOUSE_ID:
            return ALREADY_OUT_WAREHOUSE  # 放进公共模块中

    def updateOrderSendStateByOrdNo(self, order_no, state_id):
        '''
        @function : 根据订单号更新订单配送状态信息
        :param orderNo:
        :param state_id: 01 未出库, 02 已出库配送
        :return: code
        '''
        try:
            rs = self.controlsession.query(
                SaleOrder).filter_by(orderNo=order_no).first()
            if rs is not None:
                state_type = self.getSendState(state_id)
                rs.sendState = state_type
                self.controlsession.commit()
        except Exception as e:
            self.controlsession.rollback()
            print traceback.format_exc(e)
            return False
        return True

    def updateProductSendStateBySN(self, order_no, p_sn, state_id):
        '''
        @function : 根据订单号和商品sn更新商品配送状态信息
        :param order_no:
        :param p_sn:
        :return:
        '''
        try:
            rs = self.controlsession.query(
                SaleOrder).filter_by(orderNo=order_no).first()
            if rs is not None:
                pro_info_list = self.controlsession.query(
                    SaleOrderDetail).filter_by(orderNo=order_no).all()
                if pro_info_list is not None:
                    for info in pro_info_list:
                        if info['serialNo'] == p_sn:
                            state_type = self.getSendState(state_id)
                            info['sendState'] = state_type
                            self.controlsession.add(info)

                set_meal_info_list = self.controlsession.query(
                    SetRecordInfo).filter_by(orderNo=order_no).all()
                if set_meal_info_list is not None:
                    for info in set_meal_info_list:
                        if info['serialNo'] == p_sn:
                            state_type = self.getSendState(state_id)
                            info['Rem1'] = state_type  # 给套餐中的商品更新配送状态
                            self.controlsession.add(info)
                self.controlsession.commit()
        except Exception as e:
            self.controlsession.rollback()
            print(traceback.format_exc(e))
            return False
        return True

class OrderSupplementOp(ControlEngine):
    '''get order_supplement info'''

    def __init__(self):
        '''控制引擎初始化'''
        ControlEngine.__init__(self)

    def getSendType(self, send_type):
        '''
        @function : 根据配送类型获得配送方式信息
        :param send_type:
        :return:
        '''
        if send_type == CONSTUMER_TO_ID:
            return CONSTUMER_TO
        elif send_type == STORES_DISTRIBUTION_ID:
            return STORES_DISTRIBUTION

    def getIsInvo(self, state):
        '''
        @function : 是否需要发票
        :param state:
        :return:
        '''
        result = None
        if state == NEED_INVOICE:
            result = "需要"
        elif state == NOT_NEED_INVOICE:
            result = "不需要"
        return result

    def updateOrderInfo(self, orderNo, **kwargs): #, send_tplid, newPay_tplid,
        '''
        @function : 更新订单补充信息
        :param orderNo:
        :param sendType:
        :param newPayType_id:
        :param describe:
        :param sendState:
        :return:
        '''
        try:
            rs = self.controlsession.query(
                SaleOrder).filter_by(orderNo=orderNo).first()
            if rs is not None:
                rs.describe = kwargs.get('kwargs').get('describe', "")
                is_invo = self.getIsInvo(kwargs.get('kwargs').get('is_need_in', ""))
                rs.Rem3 = is_invo #是否需药开具发票
                self.controlsession.add(rs)

                rs = self.controlsession.query(
                    CustomerInfo).filter_by(orderNo=orderNo).first()
                if rs is not None:
                    rs.name = kwargs['kwargs']['name']
                    rs.tel = kwargs['kwargs']['tel']
                    rs.invoice_name = kwargs['kwargs']['in_name']
                    rs.invoice_head = kwargs['kwargs']['in_head']
                    rs.invoice_comment = kwargs['kwargs']['in_comment']
                    rs.sex = kwargs['kwargs']['sex']
                    
                    rs.buy_prov = kwargs['kwargs']['buy_prov'] #20160927cq新增
                    rs.buy_city = kwargs['kwargs']['buy_city']
                    rs.buy_addr = kwargs['kwargs']['buy_addr']
                    # print("++++++++++++++++++++++++++++++++")
                    # print("rs.buy_prov:",rs.buy_prov)
                    # print("rs.buy_city:",rs.buy_city)
                    # print("rs.buy_addr:", rs.buy_addr)
                    # print("++++++++++++++++++++++++++++++++++++++++++++++++++++")
                    self.controlsession.add(rs)
            self.controlsession.commit()
        except Exception as e:
            self.controlsession.rollback()
            print (traceback.format_exc(e))
            return False
        return True


class OrderDetail(ControlEngine):
    '''get order_detail info'''

    def __init__(self):
        '''控制引擎初始化'''
        ControlEngine.__init__(self)

    def getPayType(self):
        '''
        @function : 获得数据表中所有支付方式显示顺序
        :return: {}
        '''
        try:
            payTypeInfo = self.controlsession.query(NewPayType).all()
            infoDict = []
            for info in payTypeInfo:
                info = info.to_json()
                type = info['type']
                name = info['name']
                sorted_id = info['sorted_id']
                infoDict.append({'type': type, 'name': name, 'sorted_id': sorted_id})
            return infoDict
        except Exception as e:
            print e
            raise

    def getPayTypeNameById(self, type):
        '''
        function : 根据支付类型type获得支付方式
        :param type:
        :return: str
        '''
        try:
            if type is not None:
                payTypeInfo = self.controlsession.query(
                    NewPayType).filter_by(type=type).first()
                info = payTypeInfo.to_json()
                if type == info['type']:
                    return info['name']
            else:
                # raise ValueError("pay type is None!")
                return None
        except ValueError:
            raise

    def getPayTypeByName(self, name):
        '''
        @function : 根据支付类型获得支付方式
        :param type:
        :return: id
        '''
        try:
            payTypeInfo = self.controlsession.query(
                NewPayType).filter_by(name=name).first()
            info = payTypeInfo.to_json()
            if name == info['name']:
                return info['type']
            return None
        except Exception as e:
            print e
            raise

    def getAllSalesman(self, flagshipid):
        '''
        @function : 根据店铺id获得店铺下所有的店员列表
        :param flagshipid:
        :return: []
        '''
        try:
            op = ClerkOp()
            salesman_dict = {}
            clerk_list = op.get_clerks_info(flagshipid)
            if clerk_list is not None:
                for clerk in clerk_list:
                    salesman_dict[clerk['work_number']] = clerk.get('name', "")
                return salesman_dict
            else:
                ValueError("flahship has no number infor!")
        except ValueError:
            print traceback.format_exc()
            raise

    def getSaleNameById(self, flagshipid, id):
        '''
        @function : 根据销售员id获得店销售员名字
        :param flagshipid:
        :param id:
        :return: str
        '''
        try:
            op = ClerkOp()
            clerk_list = op.get_clerks_info(flagshipid)
            if clerk_list is not None:
                for clerk in clerk_list:
                    # print "saleman id :", id
                    if clerk['work_number'] == id:
                        return clerk.get('name', "")
                    else:
                        ValueError('salesman is not exist!')
            else:
                ValueError('flagship is not exist!')
        except ValueError:
            print traceback.format_exc()
            raise

    def getOrderDetail(
            self,
            flagshipid,
            be_time=None,
            end_time=None,
            salesman=None,
            pay_type_id=None,
            orderNo=None,
            page=1,
            per_page=10):
        '''
        @function : 获得订单详情列表
        :param flagshipid: 旗舰店ID
        :param be_time: 起始时间
        :param end_time: 结束时间
        :param salesman: 促销员
        :param pay_type_id: 支付方式id
        :param orderNo: 订单号
        :param page: 分页的当前页数
        :param per_page: 每页显示的记录数
        :return: []
        '''
        try:
            page = page - 1
            if page < 0:
                page = 0
            if per_page > SALE_ORDER_DETAIL_SHOW_PER_PAGE:
                per_page = SALE_ORDER_DETAIL_SHOW_PER_PAGE
            start = page * per_page

            orderList = None
            # if orderNo is None or orderNo == u"":
            rules = None
            if be_time and end_time: #is not None
                # print "be_time", be_time
                # print "end_time",end_time
                rules = and_(
                    SaleOrder.seltDate >= be_time,
                    SaleOrder.seltDate <= end_time)
            if salesman:
                if rules is not None:
                    rules = and_(SaleOrder.salesman.like(str(salesman)), rules)
                else:
                    rules = and_(SaleOrder.salesman.like(str(salesman)))
            if pay_type_id:
                if rules is not None:
                    rules = and_(
                        SaleOrder.newPayType_id.like(
                            str(pay_type_id)), rules)
                else:
                    rules = and_(
                        SaleOrder.newPayType_id.like(
                            str(pay_type_id)))
            if orderNo:
                if rules is not None:
                    rules = and_(
                        SaleOrder.orderNo.like(str(orderNo)), rules)
                else:
                    rules = and_(
                        SaleOrder.orderNo.like(str(orderNo)))

            #没有搜索条件，全局搜索
            if rules is None:
                rules = SaleOrder.store_id.like(str(flagshipid))
            else:
                rules = and_(rules, SaleOrder.store_id.like(str(flagshipid)))
            # 在订单数据表中搜索出对应店铺下满足条件的数据条数
            orderList = self.controlsession.query(SaleOrder).filter(
                rules).limit(per_page).offset(start).all()

            op = FlagShipOp()
            orderDataList = []
            for orderData in orderList:
                data = orderData.to_json()
                if int(data['store_id']) == int(flagshipid):
                    tempDict = {}
                    tempDict['flagship_name'] = op.getFlagshipNameById(flagshipid)
                    tempDict['orderNo'] = data['orderNo']
                    tempDict['datetime'] = data[
                        'seltDate'] + " " + data['seltTime']
                    tempDict['orderPrice'] = data['Rem2']/COVERT_DATA_TO_MONEY_NUMBER
                    tempDict['salesman'] = self.getSaleNameById(
                        flagshipid, data['salesman'])
                    tempDict['payType'] = self.getPayTypeNameById(
                        data['newPayType_id'])
                    tempDict['sendType'] = data['sendType']
                    tempDict['sendStat'] = data['sendState']
                    tempDict['is_invo'] = data['Rem3']
                    orderDataList.append(tempDict)

            # 搜索出相应条件满足的数据条数
            total = self.controlsession.query(func.count(SaleOrder.id)).filter(
                rules, SaleOrder.store_id==flagshipid).scalar()
            if total >= 10:
                count = 10
            else:
                count = total
            return orderDataList, total, count
        except Exception as e:
            print e
            raise

    def getDataFromExport(self, flagshipid, be_time, end_time, salesman,
                                                   pay_type_id, orderNo):
        '''
        @function : export all data abort this flagship
        :param flagshipid:
        :param be_time:
        :param end_time:
        :param salesman:
        :param pay_type_id:
        :param orderNo:
        :return: []
        '''
        try:
            orderList = None
            rules = None
            if be_time and end_time:  # is not None
                rules = and_(
                    SaleOrder.seltDate >= be_time,
                    SaleOrder.seltDate <= end_time)
            if salesman:
                if rules is not None:
                    rules = and_(SaleOrder.salesman.like(str(salesman)), rules)
                else:
                    rules = and_(SaleOrder.salesman.like(str(salesman)))
            if pay_type_id:
                if rules is not None:
                    rules = and_(
                        SaleOrder.newPayType_id.like(
                            str(pay_type_id)), rules)
                else:
                    rules = and_(
                        SaleOrder.newPayType_id.like(
                            str(pay_type_id)))
            if orderNo:
                if rules is not None:
                    rules = and_(
                        SaleOrder.orderNo.like(str(orderNo)), rules)
                else:
                    rules = and_(
                        SaleOrder.orderNo.like(
                            str(orderNo)))

            # 没有搜索条件，全局搜索
            if rules is None:
                rules = SaleOrder.store_id.like(str(flagshipid))

            # 在订单数据表中搜索出对应店铺下满足条件的数据条数
            orderList = self.controlsession.query(SaleOrder).filter(
                rules).all()

            op = FlagShipOp()
            # 在订单数据表中搜索出对应店铺下满足条件的数据
            if orderList is not None:
                orderDataList = []
                for orderData in orderList:
                    data = orderData.to_json()
                    if data['store_id'] == long(flagshipid.encode()):
                        tempDict = {}
                        tempDict['flagship_name'] = op.getFlagshipNameById(flagshipid)
                        tempDict['orderNo'] = data['orderNo']
                        tempDict['datetime'] = data['seltDate'] + " " + data['seltTime']
                        tempDict['orderPrice'] = data['Rem2']/COVERT_DATA_TO_MONEY_NUMBER
                        tempDict['salesman'] = self.getSaleNameById(
                            flagshipid, data['salesman'])
                        tempDict['payType'] = self.getPayTypeNameById(
                            data['newPayType_id'])
                        tempDict['sendType'] = data['sendType']
                        tempDict['sendStat'] = data['sendState']
                        tempDict['is_invo'] = data['Rem3']
                        orderDataList.append(tempDict)
                return orderDataList
            else:
                ValueError("this flagship has no data!")
        except Exception as e:
            print e
            raise


    def getDataFromExportExp(self, flagshipid, be_time, end_time, salesman,
                                                   pay_type_id, orderNo):
        '''
        @function : export all data abort this flagship
        :param flagshipid:
        :param be_time:
        :param end_time:
        :param salesman:
        :param pay_type_id:
        :param orderNo:
        :return: []
        '''
        try:
            orderList = None
            rules = None
            from data_mode.user_center.control.mixOp import MixUserCenterOp
            mix_op = MixUserCenterOp()
            if be_time and end_time:  # is not None
                rules = and_(
                    SaleOrder.seltDate >= be_time,
                    SaleOrder.seltDate <= end_time)
            if salesman:
                if rules is not None:
                    rules = and_(SaleOrder.salesman.like(str(salesman)), rules)
                else:
                    rules = and_(SaleOrder.salesman.like(str(salesman)))
            if pay_type_id:
                if rules is not None:
                    rules = and_(
                        SaleOrder.newPayType_id.like(
                            str(pay_type_id)), rules)
                else:
                    rules = and_(
                        SaleOrder.newPayType_id.like(
                            str(pay_type_id)))
            if orderNo:
                if rules is not None:
                    rules = and_(
                        SaleOrder.orderNo.like(str(orderNo)), rules)
                else:
                    rules = and_(
                        SaleOrder.orderNo.like(
                            str(orderNo)))

            # 没有搜索条件，全局搜索
            if rules is None:
                rules = SaleOrder.store_id.like(str(flagshipid))

            # 在订单数据表中搜索出对应店铺下满足条件的数据条数
            orderList = self.controlsession.query(SaleOrder).filter(
                rules).all()

            op = FlagShipOp()
            orderDataList = []
            # 在订单数据表中搜索出对应店铺下满足条件的数据
            # print("##"*40)
            if orderList is not None:
                for orderData in orderList:
                    data = orderData.to_json()
                    if data['store_id'] == long(flagshipid.encode()):

                        # 收集订单中商品的信息（名字， 数量， 是否是赠品）
                        tempProDict = {}
                        pro_info = self.controlsession.query(SaleOrderDetail).filter_by(orderNo=data['orderNo']).all()
                        for info in pro_info:
                            info = info.to_json()
                            if info['name'] in tempProDict:
                                tempProDict[info['name']]['count'] += 1
                                tempProDict[info['name']]['shop_price'] += info['salePrice'] # cq
                            else:
                                info['count'] = 1
                                info['shop_price'] = info['salePrice'] # cq
                                tempProDict[info['name']] = info

                        # 收集订单中套餐包含的商品的信息（名字， 数量， 是否是赠品）
                        pro_set_info = self.controlsession.query(SetRecordInfo).filter_by(orderNo=data['orderNo']).all()
                        for set_info in pro_set_info:
                            set_info = set_info.to_json()
                            set_info['state'] = set_info['Rem1']
                            if set_info['name'] in tempProDict:
                                tempProDict[set_info['name']]['count'] += 1
                                tempProDict[set_info['name']]['shop_price'] +=set_info['price'] #cq
                            else:
                                set_info['count'] = 1
                                set_info['shop_price'] = set_info['price'] # cq
                                tempProDict[set_info['name']] = set_info

                        # 将收集到的商品信息记录到总记录中
                        # print "*" * 40
                        # print "tempProDict:", tempProDict
                        # print "*" * 40
                        # print("%%"*40)
                        for key, info_val in tempProDict.items():
                            tempDict = {}

                            for k, v in info_val.items():
                                if k in ['name', 'state', 'count']:
                                    if k == 'state':
                                        tempDict[k] = "是" if info_val[k] == 'gift' else "否"
                                        continue
                                    tempDict[k] = v

                            tempDict['flagship_name'] = op.getFlagshipNameById(flagshipid)
                            # print("^^"*40)
                            tempDict['orderNo'] = data['orderNo']
                            tempDict['datetime'] = data['seltDate'] + " " + data['seltTime']
                            tempDict['orderPrice'] = data['Rem2'] / COVERT_DATA_TO_MONEY_NUMBER
                            # tempDict['actPrice'] = data['actPrice'] / COVERT_DATA_TO_MONEY_NUMBER #新增
                            tempDict['actPrice'] = info_val['shop_price'] / COVERT_DATA_TO_MONEY_NUMBER # cq 2016-12-28

                            tempDict['salesman'] = self.getSaleNameById(
                                flagshipid, data['salesman'])
                            if data.get('Rem1') is None or data['Rem1'] == "":
                                tempDict['cashier'] = u"管理员"
                            else:
                                tempDict['cashier'] = mix_op.get_salesmen_name(data['Rem1'])
                                # tempDict['cashier'] = self.getSaleNameById(flagshipid, data['Rem1']) #新增
                                print "tempDict['cashier']:", tempDict['cashier']
                            tempDict['payType'] = self.getPayTypeNameById(
                                data['newPayType_id'])
                            tempDict['sendType'] = data['sendType']     #配送方式
                            tempDict['sendState'] = data['sendState']    #配送状态
                            tempDict['outNumber'] = data['Rem4']        #新增 出库单
                            tempDict['is_invo'] = data['Rem3']          #是否需要发票
                            tempDict['describe'] = data['describe']     #订单备注
                            # print("$$"*40)
                            # 收集联系人表的信息
                            customer_info = self.controlsession.query(CustomerInfo).filter_by(orderNo=data['orderNo']).all()
                            for cus_info in customer_info:
                                cus_info = cus_info.to_json()
                                tempDict['consignee'] = cus_info['Rem1'] #收货人
                                tempDict['consignee_tel'] = cus_info['Rem2']
                                tempDict['consignee_addr'] = cus_info['province']+cus_info['city']+cus_info['addr']
                                tempDict['invoice_name'] = cus_info['invoice_name']
                                tempDict['invoice_head'] = cus_info['invoice_head']
                                tempDict['invoice_comment'] = cus_info['invoice_comment']
                                tempDict['cus_name'] = cus_info['name']
                                tempDict['cus_sex'] = cus_info['sex']
                                tempDict['cus_tel'] = cus_info['tel']
                            # print "tempDict:", tempDict
                            orderDataList.append(tempDict)
                            # print "!!!orderDataList:", orderDataList

                        # print "*" * 40
                        # print "orderDataList:", orderDataList
                        # print "*" * 40

                # 生成xlsx表格
                content_list = []
                title_list = ['序号', '门店信息', '销售订单号', '订单时间', '订单金额', '实收金额', '商品名称',
                              '商品数量', '是否赠品', '促销员', '收银员', '支付方式', '交货方式', '收货人', '手机号码',
                              '收货地址', '订单状态', '出库单号', '发票信息', '发票抬头', '发票内容', '顾客姓名',
                              '性别', '手机号码', '备注']
                key_list = ['number', 'flagship_name', 'orderNo', 'datetime', 'orderPrice', 'actPrice', 'name', 'count',
                              'state', 'salesman', 'cashier', 'payType', 'sendType', 'consignee', 'consignee_tel',
                              'consignee_addr', 'sendState', 'outNumber', 'is_invo', 'invoice_head', 'invoice_comment',
                              'cus_name', 'cus_sex', 'cus_tel', 'describe']
                number = 1
                for list in orderDataList:
                    temp = []
                    list['number'] = number
                    for key in key_list:
                        temp.append(list.get(key))
                    content_list.append(temp)
                    number += 1

                # StatementEngine
                TEMP_FILE_PATH="/data/erpfile/temp/"
                file_path = TEMP_FILE_PATH + str(int(time.time()*1000)) + '/'
                os.mkdir(file_path)

                # TEMP_FILE_PATH = "F:/data/erpfile/temp/"
                # file_path = TEMP_FILE_PATH + str(int(time.time()*1000)) + '/'
                # os.makedirs(file_path)

                name = file_path + u'门店销售记录.xlsx'
                statement_engine = StatementEngine(name)
                sheet_name = u'门店销售记录'
                sheet = statement_engine.select_sheet(sheet_name)
                statement_engine.write_row(sheet, title_list)
                print "content_list:", content_list
                for content in content_list:
                    statement_engine.write_row(sheet, content)
                statement_engine.save()

                return name
            else:
                ValueError("this flagship has no data!")
        except Exception as e:
            raise