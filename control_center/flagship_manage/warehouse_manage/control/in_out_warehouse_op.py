#-*- coding:utf-8 –*-

import datetime
import random
import time,os
import traceback

from flask import session
from sqlalchemy import or_,and_,func, LargeBinary
from sqlalchemy.exc import SQLAlchemyError

from control_center.flagship_manage.flagship_info_manage.control.mixOp import FlagShipOp
from config.service_config.returncode import ServiceCode
from control_center.shop_manage.good_info_manage.control.mixOp import HolaWareHouse
from data_mode.hola_flagship_store.control_base.controlBase import ControlEngine
from data_mode.hola_flagship_store.mode.warehouse_mode.warehouse_manage import *
from public.exception.custom_exception import CodeError
from config.share.share_define import NORMAL_RECEIPTS,TH_RECEIPTS,WX_RECEIPTS,FC_RECEIPTS
from public.statement.engine import StatementEngine
from public.sale_share.share_function import AutoCreateOrderInfoExp

class InOutWarehouseOp(ControlEngine):

    def __init__(self):
        '''
        控制引擎初始化
        '''
        ControlEngine.__init__(self)


    @staticmethod
    def CreateNumber(store_id,operate_type):
        '''

        :param store_id:   店铺id
        :param operate_type:   操作类型
        :return:  return_data
        '''
        return_data = {}

        store_id = str(store_id)
        userId = str(session['user']['id'])
        tm = time.localtime()
        mtime = str(tm.tm_year)[2:4]+(str(tm.tm_mon)).zfill(2)+(str(tm.tm_mday)).zfill(2)+(str(tm.tm_hour)).zfill(2)+(str(tm.tm_min)).zfill(2)+(str(tm.tm_sec)).zfill(2)
        myrand = str(random.randint(1, 100))
        myunique =store_id.zfill(3)+mtime+myrand.zfill(2)+userId.zfill(4)
        if operate_type == OperateType.purchase_in or operate_type == OperateType.other_in or operate_type == OperateType.out_over:
            return_data['number'] = "IN" + myunique
        elif operate_type == OperateType.sale_out or operate_type == OperateType.other_out:
            return_data['number'] = "OU" + myunique
        elif operate_type == OperateType.roll_over:
            return_data['number'] = "MV" + myunique
        elif operate_type == OperateType.return_service:
            return_data['number'] = "TH" + myunique
        else:
            raise CodeError(ServiceCode.service_exception, u'生成訂單失败')
        
        return_data['code'] = ServiceCode.success
        return return_data

    def InventoryCountInfo(self,store_id,warehouse_type_id,good_id):
        '''
        获取库存量
        :param store_id:   店铺id
        :param warehouse_type_id:       仓库id
        :param good_id:     商品id
        :return: return_data
        '''
        return_data = {'code' : ServiceCode.service_exception}
        try:
            rs = self.controlsession.query(Inventory).filter_by(store_id = store_id,warehouse_type_id = warehouse_type_id
                                                                ,good_id = good_id).first()
            if rs:
                inventory_count = rs.inventory_amount
            else:
                inventory_count = 0
            return_data  = {
                'code' : ServiceCode.success,
                'amount' : inventory_count
            }


        except Exception,e:
            print traceback.format_exc()
            return_data = {'code' : ServiceCode.service_exception}
        return return_data

    def QueryInventory(self,start,per_page,warehouse_type_id,store_id,name,code,bar_code):
        '''
        根据库存表中商品id查询对应的商品信息
        :param start:      从start开始
        :param per_page:    每页显示数
        :param warehouse_type_id:   仓库id
        :param store_id:            商品id
        :param name:                商品名称 （搜索条件）
        :param code:                商品编码（搜索条件）
        :param bar_code:            商品条码（搜索条件）
        :return: return_data
        '''

        return_data = {'code' : ServiceCode.service_exception}
        good_list = []
        try:
            rs = self.controlsession.query(Inventory).filter(and_(Inventory.warehouse_type_id == warehouse_type_id,
                                                             Inventory.store_id == store_id,
                                                             Inventory.inventory_amount > 0)).all()


            for rs_info in rs:
                good_id = rs_info.good_id
                op_good = HolaWareHouse()
                rs_good = op_good.get_products_detail_info_by_product_id(good_id)
                if rs_good['putaway']:
                    if name is  None and code is None and bar_code is None:
                        good_list.append(rs_good)
                    elif  name == rs_good['name']:
                        good_list.append(rs_good)

                    elif code == rs_good['code']:
                        good_list.append(rs_good)

                    elif bar_code == rs_good['bar_code']:
                        good_list.append(rs_good)
                    else:
                        pass
            l = len(good_list)
            good_list_info = good_list[start:start+per_page]
            return_data = {
                'code' : ServiceCode.success,
                'data' : good_list_info,
                'total' : l
            }
        except Exception,e:
            print traceback.format_exc()
            return_data = {'code' : ServiceCode.service_exception}
        return return_data

    def GetInOutWarehouseType(self):
        '''
        获取所有出入库类型
        :return:
        '''
        rs = self.controlsession.query(In_Out_Type).all()
        rs = [item.to_json() for item in rs]
        return rs

    def GetOutWarehouseList_1(self,start,per_page,operate_type = None,start_time = None,end_time = None,flagshipid=None):
        '''

        :param start:           开始数
        :param per_page:        每页显示数
        :param operate_type:    操作类型（搜索条件）
        :param start_time:      开始时间（搜索条件）
        :param end_time:        结束时间（搜索条件）
        :return:(rs,total)      信息list，总的页数
        '''
        relation_rs = self.controlsession.query(ProductRelation).filter(ProductRelation.flagship_id == flagshipid).all()
        relation_rs = [item.to_json() for item in relation_rs]
        relation_list=[]
        for itme in relation_rs:
            relation_list.append(itme['order_number'])
        relation_list=set(relation_list)

        if  start_time is not None and start_time is not None:
            if operate_type is None:
                rs = self.controlsession.query(InOutWarehouse).\
                        filter(and_(or_(InOutWarehouse.operate_type == OperateType.sale_out,
                                        InOutWarehouse.operate_type == OperateType.other_out),
                        InOutWarehouse.date >= datetime.datetime.strptime(start_time,'%Y-%m-%d'),
                        InOutWarehouse.date <= datetime.datetime.strptime(end_time,'%Y-%m-%d')),InOutWarehouse.number.in_(tuple(relation_list))).\
                        order_by(InOutWarehouse.id).limit(per_page).offset(start)

                total = self.controlsession.query(func.count(InOutWarehouse.id)).\
                        filter(and_(or_(InOutWarehouse.operate_type == OperateType.sale_out,
                                        InOutWarehouse.operate_type == OperateType.other_out),
                        InOutWarehouse.date >= datetime.datetime.strptime(start_time,'%Y-%m-%d'),
                        InOutWarehouse.date <= datetime.datetime.strptime(end_time,'%Y-%m-%d')),InOutWarehouse.number.in_(tuple(relation_list))).scalar()
            else:

                rs = self.controlsession.query(InOutWarehouse).filter(and_(InOutWarehouse.operate_type == operate_type,
                        InOutWarehouse.date >= datetime.datetime.strptime(start_time,'%Y-%m-%d'),
                        InOutWarehouse.date <= datetime.datetime.strptime(end_time,'%Y-%m-%d')),InOutWarehouse.number.in_(tuple(relation_list))).\
                        order_by(InOutWarehouse.id).limit(per_page).offset(start)

                total = self.controlsession.query(func.count(InOutWarehouse.id)).\
                        filter(and_(InOutWarehouse.operate_type == operate_type,
                        InOutWarehouse.date >= datetime.datetime.strptime(start_time,'%Y-%m-%d'),
                        InOutWarehouse.date <= datetime.datetime.strptime(end_time,'%Y-%m-%d')),InOutWarehouse.number.in_(tuple(relation_list))).scalar()

        else:
            if operate_type is None:
                rs = self.controlsession.query(InOutWarehouse).\
                        filter(or_(InOutWarehouse.operate_type == OperateType.sale_out,
                                        InOutWarehouse.operate_type == OperateType.other_out),InOutWarehouse.number.in_(tuple(relation_list))).\
                        order_by(InOutWarehouse.id).limit(per_page).offset(start)

                total = self.controlsession.query(func.count(InOutWarehouse.id)).\
                        filter(or_(InOutWarehouse.operate_type == OperateType.sale_out,
                                        InOutWarehouse.operate_type == OperateType.other_out),InOutWarehouse.number.in_(tuple(relation_list))).scalar()
            else:
                rs = self.controlsession.query(InOutWarehouse).\
                        filter(InOutWarehouse.operate_type == operate_type,InOutWarehouse.number.in_(tuple(relation_list))).\
                        order_by(InOutWarehouse.id).limit(per_page).offset(start)

                total = self.controlsession.query(func.count(InOutWarehouse.id)).\
                        filter(InOutWarehouse.operate_type == operate_type,InOutWarehouse.number.in_(tuple(relation_list))).scalar()

        rs = [item.to_json() for item in rs]

        return (rs,total)

    def CheckIsSerialNumber(self,good_id,warehouse_type_id,flagship_id):
        '''
        检查该商品是否是带序列号商品
        :param good_id:                    商品id
        :param warehouse_type_id:           仓库id
        :param flagship_id:             店铺id
        :return:
        '''
        rs  = self.controlsession.query(ProductRelation).filter_by(good_id = good_id,flagship_id = flagship_id,warehouse_type_id = warehouse_type_id,num =1).first()
        if rs:
            if rs.number is None or rs.number is u'':
                return ServiceCode.goodsSnNotExist
            else:
                return ServiceCode.success
        else:
            return ServiceCode.service_exception

    def CheckSerialNumber(self,sn,flagshipid,productid,wareID=None):
        '''
        检测序列号是否存在
        :param sn:
        :param flagshipid:
        :return:
        '''
        if wareID:
            wareID =wareID
        else:
           wareID = WarehouseType.inventory_warehouse
        if sn:
            rs = self.controlsession.query(ProductRelation).filter(ProductRelation.number.cast(LargeBinary) == str(sn),ProductRelation.flagship_id == flagshipid,
                                                              ProductRelation.good_id == productid,ProductRelation.warehouse_type_id == wareID,
                                                                   ProductRelation.num > 0).first()
            if rs:
              inoutsn=rs.to_json()
              if inoutsn['num'] == 1:
                return ServiceCode.success
              else:
                  return ServiceCode.goodsSnNotExist
            else:
                return ServiceCode.goodsSnNotExist

    def create_number(self,info_dict):
        '''
        创建出库单，转入样品仓，从样品仓转回库存仓
        :param info_dict:
        :return:
        '''
        rs = AutoCreateOrderInfoExp(info_dict,self.controlsession,True)
        return rs

    def delete_io_warehouse(self,billnumber=''):
        if not len(billnumber):
            return
        numberobj = self.controlsession.query(InOutWarehouse).filter_by(number=billnumber).scalar()
        if not numberobj:
            self.controlsession.delete(numberobj)
            self.controlsession.commit()

    def TurnProductToSample(self,storeId=0,productId=0,wareHouseType=0,billNumber='',serialNumber=''):
        if storeId*productId*wareHouseType <= 0 or not len(billNumber):
            return False

        #获取单号
        rs = InOutWarehouseOp.CreateNumber(storeId,OperateType.roll_over)
        snumber = rs.get('number')
        if ServiceCode.service_exception == rs.get('code') or not len(snumber):
            return False

        print  'billNumber:',billNumber

        try:
            #创建单据与单据物品
            date = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            userId = session['user']['id']
            name = session['user']['name']
            send_site = WarehouseType.get_wtype_name(wareHouseType)
            obj = InOutWarehouse(number=snumber,date=date,user=name,user_id=userId,send_site=send_site,recv_site= u'样本仓库',           in_out_number=1,operate_type=OperateType.roll_over)
            self.controlsession.add(obj)

            #这里必须先提交一次，才能插入新的单据对应ProductRelation的记录(事务的外键约束)
            self.controlsession.commit()

            #查询原单据库存
            condition = "ProductRelation.num>0,ProductRelation.flagship_id==%s,ProductRelation.warehouse_type_id==%s,ProductRelation.order_number=='%s',ProductRelation.good_id==%s " % (storeId,wareHouseType,billNumber,productId)
            if len(serialNumber):
                condition = condition+(",ProductRelation.number=='%s'" % serialNumber)
            condition = 'and_('+condition+')'

            myrs = self.controlsession.query(ProductRelation).filter(eval(condition)).limit(1).first()
            if not myrs:
                raise Exception('Not found the record in ProductRelation')

            if myrs.num < 1:
                raise Exception('ProductRelation is less 1')

            #更改原单据与物品
            myrs.num = 0
            self.controlsession.add(myrs)


            #添加新的单据与物品
            pobj = ProductRelation(number=serialNumber,good_id=productId,order_number=snumber,warehouse_type_id=WarehouseType.sample_warehouse,flagship_id=storeId,num=1)
            self.controlsession.add(pobj)

            #更改来源库存
            inobj = self.controlsession.query(Inventory).filter_by(store_id=storeId,warehouse_type_id=wareHouseType,good_id=productId).scalar()
            if not inobj:
                raise Exception('Not found the record in Inventory')
            leftcount = inobj.inventory_amount
            if leftcount < 1:
                raise Exception('inventory_amount is less 1')
            inobj.inventory_amount = leftcount-1
            self.controlsession.add(inobj)

            #更改样本库存
            oinobj = self.controlsession.query(Inventory).filter_by(store_id=storeId,warehouse_type_id=WarehouseType.sample_warehouse,good_id=productId).scalar()
            if not oinobj:#如果木有改记录，则新增
                oinobj = Inventory(good_id=productId,inventory_amount=1,warehouse_type_id=WarehouseType.sample_warehouse,store_id=storeId)
            else:
                leftcount = oinobj.inventory_amount
                oinobj.inventory_amount = leftcount+1
            self.controlsession.add(oinobj)
            self.controlsession.commit()
            return True
        except Exception,e:
            print traceback.format_exc()
            self.controlsession.rollback()
            #必须先回滚
            self.delete_io_warehouse(billnumber=snumber)
            return False

    def PackageData(self,info_list,good_dict = None,order_list = None):
        try:
            data_list = []
            op_warehouse = HolaWareHouse()
            for item in info_list:
                good_info = {}
                good_info['number'] = item[0]
                good_info['good_id'] = item[1]
                good_info['amount'] = item[2]
                if good_dict is None:
                    rs =op_warehouse.get_products_detail_info_by_product_id(good_info['good_id'])
                    good_info['name'] = rs['name']
                    good_info['code'] = rs['code']
                    good_info['bar_code'] = rs['bar_code']
                    good_info['measure'] = rs['measure']
                else:
                    good_info['name'] = good_dict['name']
                    good_info['code'] = good_dict['code']
                    good_info['bar_code'] = good_dict['bar_code']
                    good_info['measure'] = good_dict['measure']
                if order_list is None:
                    rs = self.controlsession.query(InOutWarehouse.operate_type,InOutWarehouse.date).filter(InOutWarehouse.number == good_info['number']).first()
                    good_info['operate_type'] = rs[0]
                    # good_info['date'] = rs[1]
                    #2016-10-26 修改
                    good_info['date'] = rs[1].strftime('%Y-%m-%d %H:%M:%S')
                else:
                    good_info['operate_type'] = order_list[0]
                    # good_info['date'] = order_list[1]
                    #2016-10-26 修改
                    good_info['date'] = order_list[1].strftime('%Y-%m-%d %H:%M:%S')
                data_list.append(good_info)


        except Exception,e:
            print traceback.format_exc()
        return data_list

    def QueryDetailInfo(self,start,per_page,flagship_id,order_number = None,name = None,code = None,bar_code = None):
        try:
            return_list = []
            op_warehouse = HolaWareHouse()
            good_info = {}
            total = 0
            operate_list = []
            rule = and_()
            rule.append(ProductRelation.flagship_id == flagship_id)
            rule.append(or_(ProductRelation.order_number.like("IN%") , ProductRelation.order_number.like("OU%"),
                            ProductRelation.order_number.like("MV%")))
            if name is not None or code is not None or bar_code is not None:
                good_info_list,good_total = op_warehouse.show_all_product_filter(0,100,name = name,code = code,bar_code = bar_code)
                if good_info_list:
                    for good_item in good_info_list:
                        rule.append(ProductRelation.good_id == good_item['id'])
                        if order_number is None or order_number is u'':
                            rs = self.controlsession.\
                                query(ProductRelation.order_number,ProductRelation.good_id,
                                      func.count(ProductRelation.order_number)).filter(rule).\
                                group_by(ProductRelation.order_number,ProductRelation.good_id).\
                                limit(per_page).offset(start)

                            total_item = self.controlsession.\
                                query(ProductRelation.order_number,ProductRelation.good_id,
                                      func.count(ProductRelation.order_number)).\
                                filter(rule).\
                                group_by(ProductRelation.order_number,ProductRelation.good_id).\
                                all()
                            total = total + len(total_item)
                            return_list = self.PackageData(rs,good_dict= good_item)

                            pass
                        else:
                            rule.append(ProductRelation.order_number == order_number)
                            rs = self.controlsession.\
                                query(ProductRelation.order_number,ProductRelation.good_id,
                                      func.count(ProductRelation.order_number)).\
                                filter(rule).\
                                group_by(ProductRelation.order_number,ProductRelation.good_id).\
                                limit(per_page).offset(start)
                            total_item = self.controlsession.\
                                query(ProductRelation.order_number,ProductRelation.good_id,
                                      func.count(ProductRelation.order_number)).\
                                filter(rule).\
                                group_by(ProductRelation.order_number,ProductRelation.good_id).\
                                all()
                            total = total + len(total_item)
                            return_list = self.PackageData(rs,good_dict= good_item)

                else:
                    pass
            else:
                if order_number is not None and order_number is not u'':

                    rule.append(ProductRelation.order_number == order_number)
                    rs = self.controlsession.\
                                query(ProductRelation.order_number,ProductRelation.good_id,
                                      func.count(ProductRelation.good_id)).\
                                filter(rule).\
                                group_by(ProductRelation.order_number,ProductRelation.good_id).\
                                limit(per_page).offset(start)
                    total = self.controlsession.\
                                query(ProductRelation.order_number,ProductRelation.good_id,
                                    func.count(ProductRelation.good_id)).\
                                filter(rule).\
                                group_by(ProductRelation.order_number,ProductRelation.good_id).\
                                all()
                    total = len(total)
                    order_list = self.controlsession.query(InOutWarehouse.operate_type,InOutWarehouse.date).\
                                        filter(InOutWarehouse.number == order_number).first()
                    return_list = self.PackageData(rs,order_list = order_list)
                else:
                    rs = self.controlsession.\
                                query(ProductRelation.order_number,ProductRelation.good_id,func.count(ProductRelation.good_id)).\
                                filter(rule).\
                                group_by(ProductRelation.order_number,ProductRelation.good_id).\
                                limit(per_page).offset(start).all()
                    total = self.controlsession.query(func.count(ProductRelation.good_id)).\
                                filter(rule).\
                                group_by(ProductRelation.order_number,ProductRelation.good_id).all()
                    print '1111111111111111',rs
                    total = len(total)
                    return_list = self.PackageData(rs)
            operate_list = self.get_operate_list()
        except Exception,e:
            print traceback.format_exc()
            return_list = []
            total = 0

        return return_list,total,operate_list

    def get_operate_list(self):
        '''

        :return:
        '''
        order_list = []
        try:
            rs =self.controlsession.query(In_Out_Type).all()
            order_list = [item.to_json() for item in rs]
            print '******************************',order_list
        except Exception as e:
            print traceback.format_exc()
        return order_list

    def get_detail_export_excel(self,flagship_id):
        '''
        出入库明细导出excel
        :param flagship_id:
        :return:
        '''
        try:
            opt_list_in = [OperateType.purchase_in,OperateType.other_in,OperateType.out_over]
            opt_list_out = [OperateType.sale_out,OperateType.other_out,OperateType.roll_over,OperateType.roll_factory]
            op_fs = FlagShipOp()
            rs_fs = op_fs.get_flagship_info(flagship_id)
            if rs_fs:
                fs_name = rs_fs["name"]
            else:
                raise CodeError(300,u"获取旗舰店名字失败")
            data_list = []
            rule = and_()
            rule.append(ProductRelation.flagship_id == flagship_id)
            rule.append(or_(ProductRelation.order_number.like("IN%") , ProductRelation.order_number.like("OU%"),
                            ProductRelation.order_number.like("MV%")))

            rs = self.controlsession.\
                        query(ProductRelation.order_number,ProductRelation.good_id,func.count(ProductRelation.good_id)).\
                        filter(rule).\
                        group_by(ProductRelation.order_number,ProductRelation.good_id).all()

            op_warehouse = HolaWareHouse()
            s_num = 1
            for item in rs:
                good_info = {}
                good_info["s_num"] = s_num
                good_info['number'] = item[0]
                good_info['good_id'] = item[1]

                good_info["fs_name"] = fs_name
                rs =op_warehouse.get_products_detail_info_by_product_id(good_info['good_id'])
                good_info['name'] = rs['name']
                good_info['code'] = rs['code']
                good_info['bar_code'] = rs['bar_code']
                good_info['measure'] = rs['measure']

                rs = self.controlsession.query(InOutWarehouse).\
                    filter(InOutWarehouse.number == good_info['number']).first()

                if rs:
                    rs = rs.to_json()

                    rs_opt = self.controlsession.query(In_Out_Type).filter_by(id=rs["operate_type"]).first()
                    if rs_opt:
                        rs_opt=rs_opt.to_json()
                    else :
                        raise CodeError(300,u"In_Out_Type error")
                    good_info['opt_name'] = rs_opt["name"]
                    good_info['date'] = rs["date"]
                    good_info["send_site"] = rs["send_site"]
                    good_info["recv_site"] = rs["recv_site"]
                    good_info["user"] = rs["user"]
                    good_info["remark_info"] = rs["remark_info"]
                    if rs["operate_type"] in opt_list_in:
                        good_info['amount'] = "+"+str(item[2])
                    elif rs["operate_type"] in opt_list_out:
                        good_info['amount'] = "-"+str(item[2])
                    else:
                        raise CodeError(300,u"operate_type error")
                else:
                    raise CodeError(300,u"query InOutWarehouse error")

                data_list.append(good_info)
                s_num += 1
            print '---------------------------------------------'

            title = ["序号","门店信息","类型","单号","日期","发出单位","接受单位","制单人","商品编码","商品名称","商品条码",
                     "单位","出入库数","备注"]

            key_list = ["s_num","fs_name","opt_name","number","date","send_site","recv_site","user","code","name",
                        "bar_code","measure","amount","remark_info"]
            content_list = []
            for item in data_list:
                temp = []
                for key in key_list:
                    temp.append(item.get(key))
                content_list.append(temp)

            TEMP_FILE_PATH="/data/erpfile/detail_inout/"
            # TEMP_FILE_PATH = "D:\\data\\erpfile\\detail_inout\\"

            file_path = TEMP_FILE_PATH + str(int(time.time()*1000)) + '/'
            if not os.path.exists(file_path):
                os.mkdir(file_path)
            name = file_path + u'门店出入库明细.xlsx'
            statement_engine = StatementEngine(name)
            sheet_name = u'门店出入库明细'
            sheet = statement_engine.select_sheet(sheet_name)
            statement_engine.write_row(sheet, title)
            for content in content_list:
                statement_engine.write_row(sheet, content)
            statement_engine.save()

            return name
        except Exception as e:
            print traceback.format_exc()
            raise


if __name__=="__main__":
    op = InOutWarehouseOp()
    rs = op.get_detail_export_excel(3)
