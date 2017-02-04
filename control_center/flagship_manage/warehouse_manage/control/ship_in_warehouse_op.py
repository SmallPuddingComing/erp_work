#-*- coding:utf-8 –*-

import datetime
import re

from flask import session
from sqlalchemy import LargeBinary, and_
from sqlalchemy import or_, func

from config.service_config.returncode import ServiceCode
from control_center.flagship_manage.warehouse_manage.control.in_out_warehouse_op import InOutWarehouseOp
from control_center.shop_manage.good_info_manage.control.mixOp import HolaWareHouse
from data_mode.hola_flagship_store.control_base.controlBase import ControlEngine
from data_mode.hola_flagship_store.mode.warehouse_mode.warehouse_manage import *
import traceback

# from rediscluster import StrictRedisCluster
# from redis import WatchError

class ShipInwarehouse(ControlEngine):

    def __init__(self):
        '''
        控制引擎初始化
        '''
        ControlEngine.__init__(self)

    def GetWarehouseType(self):
        '''
        获取所有仓库类型
        :return:
        '''
        rs = self.controlsession.query(WarehouseTypes).all()
        rs = [item.to_json() for item in rs]
        return rs

    def GetInOutWarehouseType(self):
        '''
        获取所有出入库类型
        :return:
        '''
        rs = self.controlsession.query(In_Out_Type).all()
        rs = [item.to_json() for item in rs]
        return rs


    def SaveInSerialNumberInfo(self,info_dict):
        '''
        :return:
        '''
        try:

            good_id = info_dict['good_id']
            number = info_dict['number']
            warehousetype_id = info_dict['warehousetype_id']
            flagship_id = info_dict['flagship_id']
            code_list = info_dict['code_list']
            amount = info_dict['amount']

             #更新出入库表
            # time_date = info_dict['time_date']
            send_site = info_dict['send_site']
            recv_site = info_dict['recv_site']
            logistics_company = info_dict['logistics_company']
            remark_info = info_dict['remark_info']
            operate_type = info_dict['operate_type']
            user= info_dict['user']
            time_date=datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')


            obj = InOutWarehouse(number = number,date = time_date,user = user,send_site = send_site,
                                 recv_site= recv_site,logistics_company = logistics_company,
                                 remark_info = remark_info,in_out_number = amount,
                                 operate_type = operate_type,user_id=session['user']['id'],spare = None)

            self.controlsession.add(obj)
            self.controlsession.commit()

            return_data = {'code' : ServiceCode.success}

            #更新ProductRelation记录表
            l = 0
            for serial_number in code_list:
                if serial_number is not None or serial_number is not '':
                    obj = ProductRelation(good_id = good_id,order_number = number,warehouse_type_id = warehousetype_id,
                                         flagship_id = flagship_id,number = serial_number,num=1)
                    self.controlsession.add(obj)
                    l = l+1
            n = amount -l
            while n>0:
                obj = ProductRelation(good_id = good_id,order_number = number,warehouse_type_id = warehousetype_id,
                                         flagship_id = flagship_id,num=1)
                self.controlsession.add(obj)

            # 更新库存表
            store_id = info_dict['flagship_id']

            rs = self.controlsession.query(Inventory).filter_by(store_id = flagship_id,warehouse_type_id = warehousetype_id
                                                                    ,good_id = good_id).first()


            if rs:
                inventory_count = rs.inventory_amount
                rs.inventory_amount = inventory_count + amount
                self.controlsession.add(rs)
                return_data = {'code' : ServiceCode.success}

            else:
                obj = Inventory(store_id = flagship_id,warehouse_type_id = warehousetype_id,good_id =good_id,inventory_amount = amount)
                self.controlsession.add(obj)
                return_data = {'code' : ServiceCode.success}

            self.controlsession.commit()
            return_data = {'code' : ServiceCode.success}
        except Exception,e:
            print e
            return_data = {'code' : ServiceCode.service_exception}
            self.controlsession.rollback()
            rs = self.controlsession.query(InOutWarehouse).filter(InOutWarehouse.number == number).first()
            if rs:
                self.controlsession.delete(rs)
                self.controlsession.commit()
        # print '----------------------成功',return_data
        return return_data

    def GetOutWarehouseList(self,type = None):
        '''
        获取入库信息
        :return:
        '''
        if type == 1:
            rs = self.controlsession.query(InOutWarehouse).filter(or_(InOutWarehouse.operate_type==OperateType.purchase_in,InOutWarehouse.operate_type==OperateType.other_in)).all()
            rs = [item.to_json() for item in rs]
            return rs
        else :
            rs = self.controlsession.query(InOutWarehouse).filter(or_(InOutWarehouse.operate_type==3,InOutWarehouse.operate_type==4)).all()
            rs = [item.to_json() for item in rs]
            return rs

    def CheckIsInSerialNumber(self,good_id,warehouse_type_id,flagship_id):


        #库里面没有查到120；100有序列号；121没有序列号
        if warehouse_type_id:
            warehouse_type_id=warehouse_type_id
        else:
            warehouse_type_id=WarehouseType.inventory_warehouse

        rs  = self.controlsession.query(ProductRelation).filter_by(good_id = good_id,flagship_id = flagship_id,warehouse_type_id = warehouse_type_id).first()
        if rs:

            if rs.number:
                return ServiceCode.success

            else:

                return ServiceCode.goodsHasSold
        else:
            return ServiceCode.goodsSnNotExist

    def CheckProductSN(self, product_id):
        '''
        检测产品是否有序列号
        :param product_id:
        :return:
        '''
        try:
            if not product_id:
                return {'code': ServiceCode.params_error, 'msg': '产品ID不能为空'}
            res = self.controlsession.query(ProductRelation).filter(ProductRelation.good_id == product_id).first()
            if res:
                if res.number:
                    return {'code': ServiceCode.success, 'msg': '此产品有序列号'}
                else:
                    return {'code': ServiceCode.goodsTypeError, 'msg': '此产品无序列号'}
            else:
                return {'code': ServiceCode.data_empty, 'msg': '没有查到对应数据'}
        except Exception,e:
            print traceback.format_exc()
            return {'code': ServiceCode.service_exception, 'msg': '服务器处理失败'}

    def GetSearchWarehouseInfo(self,typename=None,startTime=None,endTime=None,page=None,pageSize=None):
        '''
        入库搜索接口
        :param typename:搜索名字
        :param startTime:开始时间
        :param endTime:结束时间
        :param page:当前页码
        :param pageSize:每页显示多少条
        :return:
        '''
        in_out_name=self.controlsession.query(In_Out_Type).filter(In_Out_Type.name == typename).first()
        type_name_list=in_out_name.to_json()

        rs=self.controlsession.query(InOutWarehouse).filter().all()

    def GetSearchWarehouseInfo(self,start,per_page,operate_type = None,start_time = None,end_time = None,flagshipid = None):
        '''
        :param start:
        :param per_page:
        :param operate_type:
        :param start_time:
        :param end_time:
        :return:
        '''

        relation_rs_test = self.controlsession.query(ProductRelation.order_number,ProductRelation.flagship_id).filter(ProductRelation.flagship_id == flagshipid).all()
        relation_rs_test=set(relation_rs_test)
        print 'relation_rs_test:',relation_rs_test

        relation_rs = self.controlsession.query(ProductRelation).filter(ProductRelation.flagship_id == flagshipid).all()
        relation_rs = [item.to_json() for item in relation_rs]
        relation_list=[]
        for itme in relation_rs:
            relation_list.append(itme['order_number'])
        relation_list=set(relation_list)

        print 'relation_rs:',relation_list

        if  start_time is not None and start_time is not None:
            if operate_type is None:
                rs = self.controlsession.query(InOutWarehouse).\
                        filter(and_(or_(InOutWarehouse.operate_type == OperateType.purchase_in,InOutWarehouse.operate_type == OperateType.other_in),
                        InOutWarehouse.date >= datetime.datetime.strptime(start_time,'%Y-%m-%d'),
                        InOutWarehouse.date <= datetime.datetime.strptime(end_time,'%Y-%m-%d')),InOutWarehouse.number.in_(tuple(relation_list))).\
                        order_by(InOutWarehouse.id).limit(per_page).offset(start)

                total = self.controlsession.query(func.count(InOutWarehouse.id)).\
                        filter(and_(or_(InOutWarehouse.operate_type == OperateType.purchase_in,InOutWarehouse.operate_type == OperateType.other_in),
                        InOutWarehouse.date >= datetime.datetime.strptime(start_time,'%Y-%m-%d'),
                        InOutWarehouse.date <= datetime.datetime.strptime(end_time,'%Y-%m-%d')),InOutWarehouse.number.in_(tuple(relation_list))).scalar()

            else:
                total = self.controlsession.query(func.count(InOutWarehouse.id)).\
                        filter(and_(InOutWarehouse.operate_type == operate_type,
                        InOutWarehouse.date >= datetime.datetime.strptime(start_time,'%Y-%m-%d'),
                        InOutWarehouse.date <= datetime.datetime.strptime(end_time,'%Y-%m-%d')),InOutWarehouse.number.in_(tuple(relation_list))).scalar()
                #print 'to-----------------------',total,operate_type

                rs = self.controlsession.query(InOutWarehouse).filter(and_(InOutWarehouse.operate_type == operate_type,
                        InOutWarehouse.date >= datetime.datetime.strptime(start_time,'%Y-%m-%d'),
                        InOutWarehouse.date <= datetime.datetime.strptime(end_time,'%Y-%m-%d')),InOutWarehouse.number.in_(tuple(relation_list))).\
                        order_by(InOutWarehouse.id).limit(per_page).offset(start)

               # print '-----------------------呵呵',rs
        else:




            if operate_type is None:
                rs = self.controlsession.query(InOutWarehouse).\
                        filter(or_(InOutWarehouse.operate_type == OperateType.purchase_in,InOutWarehouse.operate_type == OperateType.other_in),InOutWarehouse.number.in_(tuple(relation_list))).\
                        order_by(InOutWarehouse.id).limit(per_page).offset(start)

                total = self.controlsession.query(func.count(InOutWarehouse.id)).\
                        filter(or_(InOutWarehouse.operate_type == OperateType.purchase_in,InOutWarehouse.operate_type == OperateType.other_in),InOutWarehouse.number.in_(tuple(relation_list))).scalar()
            else:
                rs = self.controlsession.query(InOutWarehouse).\
                        filter(or_(InOutWarehouse.operate_type == operate_type),InOutWarehouse.number.in_(tuple(relation_list))).\
                        order_by(InOutWarehouse.id).limit(per_page).offset(start)

                total = self.controlsession.query(func.count(InOutWarehouse.id)).\
                        filter(InOutWarehouse.operate_type == operate_type,InOutWarehouse.number.in_(tuple(relation_list))).scalar()

        rs = [item.to_json() for item in rs]

        return (rs,total)

    def GetWarehouseDetailed(self,in_id=None,flagshipid=None):
        '''
        获取产品出入明细信息
        :param type:
        :param in_id:
        :return:
        '''
        try:

            rs=self.controlsession.query(ProductRelation).filter(ProductRelation.order_number == in_id,ProductRelation.flagship_id == flagshipid).all()
            rs = [item.to_json() for item in rs]

           # productid=rs[0]['good_id']

            productInfoObj=HolaWareHouse()
            #proInfo=productInfoObj.get_products_detail_info_by_product_id(productid)

            winfo=self.controlsession.query(InOutWarehouse).filter(InOutWarehouse.number == in_id).first()
            winfos=winfo.to_json()

            plist={}
            parr=[]
            for itme in rs:

                productid=itme['good_id']
                proInfo=productInfoObj.get_products_detail_info_by_product_id(productid)

                pminlist = {}
                pminlist['serialNumber']=itme['number']
                pminlist['code']=proInfo['code']
                pminlist['bar_code']=proInfo['bar_code']
                pminlist['name']=proInfo['name']
                pminlist['category_name']=proInfo['category']['name']




                parr.append(pminlist)


            Coun=InOutWarehouseOp()
            warehouseNuber=Coun.InventoryCountInfo(rs[0]['flagship_id'],rs[0]['warehouse_type_id'],rs[0]['good_id'])
            in_out_type=self.controlsession.query(In_Out_Type).filter(In_Out_Type.id == winfos['operate_type']).first()
            in_out_type_name=in_out_type.to_json()

            plist['oddNumber']=winfos['number']
            plist['user']=winfos['user']
            plist['date']=winfos['date']
            plist['send_site']=winfos['send_site']
            plist['recv_site']=winfos['recv_site']
            plist['operate_type']=in_out_type_name['name']
            plist['remark_info']=winfos['remark_info']
            plist['logistics_company']=winfos['logistics_company']


            plist['list']=parr

            #print '------------------查询结果:',plist

            return plist
        except Exception,e:
            # print '-------------e---------------',e
            print traceback.format_exc()


    def CheckSpace(self,sn):
        if re.search(r'^[0-9a-zA-Z]{0,128}$', sn) is None:
            return False
        else:
            return True



    def GetOutWarehouseList_1(self,start,per_page,operate_type,start_time = None,end_time = None):



        rs = self.controlsession.query(InOutWarehouse).filter_by(operate_type = operate_type).\
            order_by(InOutWarehouse.id).limit(per_page).offset(start)
        rs = [item.to_json() for item in rs]
        return rs
    def GetInOutDetails(self,flagshipid,stype=None,snumber=None,flag=None,start = None,pageSize=None):
        try:
            # print '单号:',snumber
            #/\s/g
            if snumber:
                if not self.CheckSpace(snumber):
                  return ServiceCode.service_exception
                rs=self.controlsession.query(InOutWarehouse).filter(InOutWarehouse.number == snumber).all()
            else:
                rs=self.controlsession.query(InOutWarehouse).all()
            rs=[itme.to_json() for itme in rs]
            productInfoObj=HolaWareHouse()
            if not stype:
                productId=[]
                for itme in (rs):
                    # if itme['user']:
                    rsid=self.controlsession.query(ProductRelation).filter(ProductRelation.order_number == itme['number'],ProductRelation.flagship_id == flagshipid).all()
                    rsid=[itme.to_json() for itme in rsid]
                    productId.append(rsid)
                parr=[]

                #print '--------res:',rs,'-------number:',snumber

                for itme in productId:
                    plist={}
                    if len(itme):
                        proInfo=productInfoObj.get_products_detail_info_by_product_id(itme[0]['good_id'])
                        plist['in_out']=itme
                        plist['proInfo']=proInfo
                        parr.append(plist)
                jsonObj={}
                jsonArr=[]
                for key,itme in enumerate(rs):
                    for key1,itme1 in enumerate(parr):
                        if itme['number'] == itme1['in_out'][0]['order_number']:
                            jsonList={}
                            typeList=self.controlsession.query(In_Out_Type).filter(In_Out_Type.id == itme['operate_type']).first()
                            list=typeList.to_json()
                            jsonList['typename']=list['name']
                            jsonList['list1']= itme
                            jsonList['list2']=itme1['proInfo']
                            jsonArr.append(jsonList)

                # print '--------op_data:',jsonArr
                jsonObj['data']=jsonArr
                return jsonObj
            else:
                if flag == 'name':
                    product = productInfoObj.get_product_info_by(pname=stype)
                elif flag == 'code':
                    product = productInfoObj.get_product_info_by(pcode=stype)
                elif flag == 'bar_code':
                    product = productInfoObj.get_product_info_by(pbarcode=stype)

                list=product.to_json()
                if snumber:
                    rsidl=self.controlsession.query(ProductRelation).filter(ProductRelation.good_id == list['id'],ProductRelation.order_number == snumber).all()
                else:
                    rsidl=self.controlsession.query(ProductRelation).filter(ProductRelation.good_id == list['id']).all()
                rsidl=[itme.to_json() for itme in rsidl]
                d=[]
                a={}
                keys=[]
                for key, itme in enumerate(rsidl):
                    keys.append(itme['order_number'])

                keys=set(keys)

                qlist=[]
                for itme in keys:
                    hh=[]
                    for itme1 in rsidl:
                        if itme == itme1['order_number']:
                            hh.append(itme1)
                    qlist.append(hh)


                for itme in qlist:
                    m={}
                    typeList=self.controlsession.query(InOutWarehouse).filter(InOutWarehouse.number == itme[0]['order_number']).all()
                    typeList=[itme1.to_json() for itme1 in typeList]
                    if typeList[0]['operate_type'] == OperateType.purchase_in:
                        tname='采购入库'
                    elif typeList[0]['operate_type'] == OperateType.other_in:
                        tname='其他入库'
                    elif typeList[0]['operate_type'] == OperateType.sale_out:
                        tname='销售出库'
                    elif typeList[0]['operate_type'] == OperateType.other_out:
                        tname='其他出库'
                    m['typename']=tname
                    m['list2']=list
                    m['list1']=typeList[0]
                    d.append(m)
                    # print '---------list----lla',m


                #myList = list(set(d['list1']['number']))

                a['data']=d

                return a
        except Exception,e:
            #print e
            return ServiceCode.service_exception






    def GetSnCode(self,sn,flagshipid,productid,wareID=None):
        '''
        检测SN是否存在
        :param sn:
        :param flagshipid:
        :return:
        '''
        if not self.CheckSpace(sn):
            return ServiceCode.service_exception
        if wareID:
            wareID =wareID
        else:
           wareID = WarehouseType.inventory_warehouse
        if sn:
            try:

             rs = self.controlsession.query(ProductRelation).filter(ProductRelation.number.cast(LargeBinary)==str(sn),ProductRelation.flagship_id == flagshipid,
                                                           ProductRelation.good_id == productid,ProductRelation.warehouse_type_id == wareID).all()


            except Exception,e:
                print e
                raise Exception('GetSnCode--error')
            snflag=False
            if rs:
              inoutsn=[itme.to_json() for itme in rs]
              for itme in inoutsn:
                  if itme['num'] == 1:
                      return ServiceCode.success
                  else:
                      snflag=True
              if snflag:
                   return ServiceCode.goodsHasSold
              # if inoutsn['num'] == 1:
              #   return ServiceCode.success
              # else:
              #     return ServiceCode.goodsHasSold
            else:
                return ServiceCode.goodsSnNotExist

    def GetSnCodeMy(self,sn,flagshipid,productid,wareID=None):
        '''
        检测SN是否存在
        :param sn:
        :param flagshipid:
        :return:
        '''

        if not self.CheckSpace(sn):
            return ServiceCode.service_exception
        if wareID:
            wareID =wareID
        else:
           wareID = WarehouseType.inventory_warehouse
        #print 'sn----------',sn,'flagshipid',flagshipid,'productid',productid,'wareID',wareID,'sntype',type(sn),type(str(sn))
        if sn:
            try:
             rs = self.controlsession.query(ProductRelation).filter(ProductRelation.number.cast(LargeBinary)==str(sn)).first()
            except Exception,e:
                print e
                raise Exception('GetSnCode--error')
            if rs:
               return ServiceCode.goodsHasSold
            else:
                return ServiceCode.goodsSnNotExist

    def GetStoreAll(self):
        from data_mode.hola_flagship_store.mode.ship_model.flagship_store_info import FlagShipStoreInfo

        try:
            rs = self.controlsession.query(FlagShipStoreInfo).all()
            rs=[itme.to_json() for itme in rs]
        except Exception,e:
            print traceback.format_exc()
            return ServiceCode.data_empty
        return rs

    def GetSampleInfo(self,flagshipid=None,serial=None,pname=None,pcode=None,pbarcode=None,number=None,pg=None,lt=None,goodid=None):
        '''
        :param flagshipid:
        :param serial:序列号
        :param pname:产品名称
        :param pcode:产品编码
        :param pbarcode:条形码
        :param number:单号
        :param pg:当前页码
        :param lt:每次读取条数
        :return:
        '''
        if pg:
            if pg > 0:
                start=lt*pg
            else:
                start=0
        else:
            start=0
        condition = "ProductRelation.flagship_id==%s,ProductRelation.good_id==%s,ProductRelation.warehouse_type_id==%s,\
                     ProductRelation.num==%s" % (flagshipid,goodid,WarehouseType.sample_warehouse,1)
        if serial:
            condition =condition+ ",ProductRelation.number=='%s'" % serial
        if number:
            condition =condition+ ",ProductRelation.order_number=='%s'" % number

        condition='and_('+condition+')'
        relationlist=self.controlsession.query(ProductRelation).filter(eval(condition)).order_by(ProductRelation.id.asc()).limit(lt).offset(start).all()
        total=self.controlsession.query(func.count(ProductRelation.id)).filter(eval(condition)).scalar()
        result=[itme.to_json() for itme in relationlist]
        hop=HolaWareHouse()
        proInfos=hop.get_products_detail_info_by_product_id(goodid)
        products=[]
        for itme in result:
            jsonps={}
            jsonps['bill']=itme['order_number']
            jsonps['pname']=proInfos['name']
            jsonps['pcode']=proInfos['code']
            jsonps['pbarcode']=proInfos['bar_code']
            jsonps['serial']=itme['number']
            products.append(jsonps)
        return (products,total)

    def ProductToStock(self,flagshipid=None,serial=None,order_number=None,good_id=None):
        '''

        :param flagshipid:di店铺ID
        :param serial:序列号
        :param order_number:单号
        :param good_id:产品ID
        :return:
        '''
        print 'flagshipid',flagshipid,'serial',serial,'order_number',order_number,'good_id',good_id
        #生成单号
        rs = InOutWarehouseOp.CreateNumber(flagshipid,OperateType.out_over)
        if rs['number'] is None:
            return False
        print "rs['number']:",rs['number']
        #创建转库单
        try:
            date = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            userId = session['user']['id']
            name = session['user']['name']

            recv_site = WarehouseType.get_wtype_name(WarehouseType.inventory_warehouse)
            obj=InOutWarehouse(number=rs['number'],date=date,user=name,user_id=userId,send_site=u'样品仓',recv_site=recv_site,in_out_number=1,operate_type=OperateType.out_over)
            self.controlsession.add(obj)
            #修改原有数据状态
            condition='ProductRelation.good_id==%s,ProductRelation.number=="%s",ProductRelation.order_number=="%s", \
                      ProductRelation.warehouse_type_id==%s' % (good_id,serial,order_number,WarehouseType.sample_warehouse)
            print 'condition:',condition
            condition='and_('+condition+')'
            relationResult=self.controlsession.query(ProductRelation).filter(eval(condition)).limit(1).first()

            print 'relationResult:',relationResult, 'relationResult.num:',relationResult.num

            if not relationResult:
                raise Exception('Not found the record in ProductRelation')
            if relationResult.num < 1:
                raise Exception('ProductRelation is less 1')
            relationResult.num =0
            self.controlsession.add(relationResult)

            #添加一条新的数据
            addRelation=ProductRelation(number=serial,good_id=good_id,order_number=rs['number'],warehouse_type_id=WarehouseType.inventory_warehouse,
                                        flagship_id=flagshipid,num=1)
            self.controlsession.add(addRelation)

            #更新库存表
            StockRes=self.controlsession.query(Inventory).filter(Inventory.good_id==good_id,Inventory.store_id == flagshipid,Inventory.warehouse_type_id == WarehouseType.inventory_warehouse).first()
            if not StockRes:#如果没有则新增一条数据
                StockRes=Inventory(good_id=good_id,store_id = flagshipid,warehouse_type_id = WarehouseType.inventory_warehouse,inventory_amount=1)
            else:
                amount = StockRes.inventory_amount
                StockRes.inventory_amount=amount+1
            self.controlsession.add(StockRes)

            UpdateRes=self.controlsession.query(Inventory).filter(Inventory.good_id==good_id,Inventory.store_id == flagshipid,Inventory.warehouse_type_id == WarehouseType.sample_warehouse).first()
            if not UpdateRes:
                raise Exception('Not found the record in Inventory')
            else:
                lamount=UpdateRes.inventory_amount
                UpdateRes.inventory_amount=lamount-1
            self.controlsession.add(UpdateRes)
            self.controlsession.commit()
            return True
        except Exception ,e:
            print traceback.format_exc()
            #失败回滚
            self.controlsession.rollback()
            return False

    def get_productinfo_by_productid(self, product_id):
        rs = self.controlsession.query(ProductRelation).filter(ProductRelation.good_id==product_id).first()
        if rs:
            return rs.to_json()
        else:
            return {}


if __name__=="__main__":
    import redis
    from redis import WatchError
    from rediscluster import StrictRedisCluster

    is_q= ShipInwarehouse()






