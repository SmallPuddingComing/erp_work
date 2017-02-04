#/usr/bin/python
#-*- ucoding:utf-8 -*-
import json
import time
import datetime
import random
import traceback
from sqlalchemy import func, or_, and_
from flask import session
from operator import itemgetter
from itertools import groupby
from public.sale_share.share_function import ShareFunctionOp


from public.exception.custom_exception import CodeError
from config.service_config.returncode import ServiceCode
from config.share.share_define import translate_dict_to_list, DEAL_WITH_TYPE, FC_QUERY_METHOD,WAIT_ACCEPT
from data_mode.hola_flagship_store.control_base.controlBase import ControlEngine
from control_center.flagship_manage.flagship_info_manage.control.flagship_op import FlagShipOp
from data_mode.user_center.control.mixOp import MixUserCenterOp
from config.logistics_config.logistics import logisticsConfig
from data_mode.hola_flagship_store.mode.warehouse_mode.warehouse_manage import *
from control_center.flagship_manage.customer_service.control.mixOP import QueryReturnFactoryInfoOp
from data_mode.hola_flagship_store.mode.after_sale.deal_with_infomation import DealWithInfomation
from control_center.flagship_manage.customer_service.control.after_sale_operate import AfterSaleOp
from public.sale_share.share_function import AutoCreateOrderInfoExp

def updata_order_number_state(db_session,order_number):
    '''

    :param order_number: 单据号
    :return:
    '''
    return_data = {'code':ServiceCode.service_exception}
    try:
        rs = db_session.query(InOutWarehouse).filter_by(number=order_number).first()
        if rs:
            rs.spare = "True"
            db_session.add(rs)
        else:
            raise CodeError(300,u"查询InOutWarehouse错误")
        return_data = {'code':ServiceCode.success}

    except Exception as e:
        print traceback.format_exc()
        db_session.rollback()
        return_data = {'code':ServiceCode.service_exception}
    return return_data

def updata_wx_state(db_session,deal_with_id):
    '''

    :param bill_num:  维修单号
    :return:
    '''
    return_data = {'code':ServiceCode.service_exception}
    try:
        rs = db_session.query(DealWithInfomation).filter_by(id=deal_with_id).first()
        if rs:
            rs.state = WAIT_ACCEPT
            db_session.add(rs)
        else:
            raise CodeError(300,u"查询DealWithInfomation错误")
        return_data = {'code':ServiceCode.success}
    except CodeError as e:
        print traceback.format_exc()
        db_session.rollback()
        return_data = {'code':ServiceCode.service_exception}
    except Exception as e:
        print traceback.format_exc()
        db_session.rollback()
        return_data = {'code':ServiceCode.service_exception}
    return return_data



class ReturnedFactory(ControlEngine):

    def __init__(self):
        '''
        控制引擎初始化
        '''
        ControlEngine.__init__(self)



    def create_order_info(self,flagship_id,user_id):
        '''

        :param flagship_id:
        :return:
        '''
        r_data = {}
        try:

            out_type = u"返厂出库"
            out_type_id = OperateType.to_factory
            op_share = ShareFunctionOp()
            fc_number = op_share.create_numberNo(flagship_id,out_type_id)
            if fc_number["code"] == ServiceCode.success:
                fc_number = fc_number["number"]
            else:
                raise CodeError(300,u"创建返厂单失败")
            date_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            # userId = str(session['user']['id'])
            user_op = MixUserCenterOp()
            rs_user = user_op.get_user_info(user_id)
            if rs_user:
                user_name = rs_user["name"]
            else:
                user_name = ""
                raise CodeError(300,"can not find user")
            flagship_op = FlagShipOp()
            rs_flagship = flagship_op.get_flagship_info_by_flagship_id(flagship_id)
            if rs_flagship:
                send_site = rs_flagship["name"]
            else:
                send_site = ""
                raise CodeError(300,"can not find flagship")



            logisticsType=logisticsConfig()
            logisticsList= logisticsType.logistics_get_xml()
            # print '-------------------------------',logisticsList
            logistics_company_list = []
            i = 1

            for item in logisticsList:
                item_dict = {}
                item_dict["id"] = i
                item_dict["name"] = item
                i = i+1
                logistics_company_list.append(item_dict)


            r_data = {
            'number' : fc_number,
            'date' :  date_time,
            'user_name' : user_name,
            'send_site':send_site,
            'out_type' : out_type,
            'out_type_id' : out_type_id,
            'logistics_company_list' : logistics_company_list
            }

        except CodeError as e:
            print traceback.format_exc()
        return r_data

    def query_fc_product_info(self,data_dict):

        r_data = {}
        try:
            #返厂理由
            fc_reason_list = translate_dict_to_list(DEAL_WITH_TYPE)
            #搜索条件
            search_list = translate_dict_to_list(FC_QUERY_METHOD)

            op = QueryReturnFactoryInfoOp()
            after_op = AfterSaleOp()
            if data_dict["value_type"] == 1:
                search_type = AfterSaleOp.SEARCH_TYPE_GOODS_SKU
            elif data_dict["value_type"] == 2:
                search_type = AfterSaleOp.SEARCH_TYPE_CUSTOMER_NAME
            elif data_dict["value_type"] == 3:
                search_type = AfterSaleOp.SEARCH_TYPE_CUSTOMER_PHONE
            else:
                search_type = None


            if data_dict["fc_reason"] >0 and data_dict["fc_reason"] in DEAL_WITH_TYPE:

                data_list,total = after_op.fc_search(
                        data_dict["flagship_id"],
                        data_dict["f_state"],
                        search_type,
                        data_dict["value"],
                        data_dict["page_num"],
                        data_dict["per_page"],
                        deal_type= data_dict["fc_reason"])
            else:
                data_list,total = after_op.fc_search(
                        data_dict["flagship_id"],
                        data_dict["f_state"],
                        search_type,
                        data_dict["value"],
                        data_dict["page_num"],
                        data_dict["per_page"])

            r_data = {
                'data_list': data_list,
                'total' : total,
                'fc_reason_list':fc_reason_list,
                'search_list': search_list
            }

        except CodeError as e:
            print traceback.format_exc()

        return r_data

    def save_fc_info(self,fc_info_dict):

        r_data = False
        try:

            product_list = fc_info_dict["good_list"]
            in_out_number = len(product_list)

            #判断同一维修单号的所有商品是否已全部选中

            rs_check = self.check_number(product_list)
            if rs_check["code"] != ServiceCode.success:
                raise CodeError(300,u"同一维修单号的所有商品没有全部选中")
            #创建返厂单

            rs = AutoCreateOrderInfoExp(fc_info_dict,self.controlsession)
            if rs["code"] != ServiceCode.success:
                raise CodeError(300,u"服务器错误")
            op_fc = ReturnedFactory()
            #修改对应维修单号的状态
            for item in product_list:
                if item["deal_with_information_id"] is not None:
                    rs = updata_wx_state(self.controlsession,item["deal_with_information_id"])
                    if rs["code"] != ServiceCode.success:
                        raise CodeError(300,u"updata_wx_state error")
                else:
                    continue

            product_list.sort(key=itemgetter("bill_num"))
            for value ,items in groupby(product_list,key=itemgetter("bill_num")):
                rs = updata_order_number_state(self.controlsession,value)
                if rs["code"] != ServiceCode.success:
                    raise CodeError(300,u"更新单号为已返厂失败")
            self.controlsession.commit()
            r_data = True
        except CodeError as e:
            print traceback.format_exc()
            self.controlsession.rollback()
            raise
        except Exception as e:
            print traceback.format_exc()
            self.controlsession.rollback()
            raise

        return r_data

    def check_number(self,product_list):


        return_data = {"code":ServiceCode.service_exception}
        try:
            bill_number_list =[]
            product_id_list = []
            # print '---------------------------',product_list
            product_list.sort(key=itemgetter("bill_num"))
            for value ,items in groupby(product_list,key=itemgetter("bill_num")):
                bill_number_list.append(value)
            product_list.sort(key=itemgetter("serial_number","good_id","bill_num"))
            for value,items in groupby(product_list,key=itemgetter("serial_number","good_id","bill_num")):
                count = len(list(items))
                # print '------value--------',value,count
                value_list = list(value)
                value_list.append(count)
                value = tuple(value_list)
                product_id_list.append(value)
            # print '-----bill_number_list-----------',bill_number_list,product_id_list
            for item in bill_number_list:
                rs = self.controlsession.\
                query(ProductRelation.number,ProductRelation.good_id,ProductRelation.order_number,func.count(ProductRelation.id))\
                    .filter(and_(ProductRelation.order_number==item,ProductRelation.num==1)).\
                    group_by(ProductRelation.number,ProductRelation.good_id).all()
                for itme in rs:
                    # print '--------itme--------------',itme
                    if itme not in product_id_list:
                        # print '--------sdfasdfs--------------',item
                        raise CodeError(300,"hahaha")
            return_data = {"code":ServiceCode.success}
        except CodeError as e:
            print traceback.format_exc()
            return_data = {"code":ServiceCode.service_exception}

        return return_data


if __name__ == "__main__":
    pass