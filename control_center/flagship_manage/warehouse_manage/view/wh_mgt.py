# coding:utf8

import datetime,os
import json
import time
import traceback

from config.logistics_config.logistics import logisticsConfig
from config.outcompany_config.company import companyConfig
from config.service_config.returncode import ServiceCode
from control_center.flagship_manage.flagship_info_manage.control.flagship_op import FlagShipOp
from control_center.flagship_manage.warehouse_manage.control.warehouseOp import WarehouseOp
# from control_center.departments.flagship.control.warehouseOp import InWarehouseOp,WarehouseTypeOp,ExceptInfo, OutWarehouseOp, WarehouseOp, WarehouseExchange
# from control_center.departments.flagship.mode.flagship_warehouse_mgt import Out_Reason_Dict
from control_center.flagship_manage.warehouse_manage.control.in_out_warehouse_op import InOutWarehouseOp
from control_center.flagship_manage.warehouse_manage.control.ship_in_warehouse_op import ShipInwarehouse
from control_center.flagship_manage.warehouse_manage.control.whouse_product_info_op import WhouseProductInfoOp
from data_mode.hola_flagship_store.mode.warehouse_mode.warehouse_manage import WarehouseType
from data_mode.hola_flagship_store.mode.warehouse_mode.warehouse_manage import OperateType
from flask import request, session
from flask.views import MethodView

from control_center.shop_manage.good_info_manage.control.mixOp import HolaWareHouse,Dict_Categorgory_touyingyi
from public.function import tools
from config.share.share_define import *
from public.exception.custom_exception import CodeError
from flask import make_response, send_file

class WarehouseMgt(MethodView):

    def get(self):
        return tools.flagship_render_template('storeManage/warehouse/warehouse_entry.html')

class ProductInWarehouse(MethodView):
    '''
    门店仓库首页
    '''
    def get(self):
        return_data = {'code' : ServiceCode.service_exception}
        page_num = request.values.get('page_num',1,int)
        per_page = request.values.get('per_page',10,int)
        operate_type_id = request.values.get('operate_type_id',0,int)
        start_time = request.values.get('start_time',None,str)
        end_time = request.values.get('end_time',None,str)
        flagshipid=request.values.get('flagshipid','')

        print 'flagshipid:',flagshipid

        try:
            page = page_num - 1
            if page < 0:
                page = 0
            if per_page > 60:
                per_page = 60
            start = page *per_page
            per_page = 10
            op  = ShipInwarehouse()
            if operate_type_id == 0:
                rs, total = op.GetSearchWarehouseInfo(start,per_page,start_time = start_time,end_time = end_time,flagshipid=flagshipid)
            else:
                rs, total = op.GetSearchWarehouseInfo(start,per_page,operate_type=operate_type_id,
                                                    start_time = start_time,end_time = end_time,flagshipid=flagshipid)


            print("An----"*20)

            return_data = {
                'code' : ServiceCode.success,
                'order_list' : rs,
                'total' : total
            }
            print 'addtime时间','--',rs
            pass
        except Exception,e:
            print e
            return_data = {'code' : ServiceCode.service_exception}
        return tools.flagship_render_template('storeManage/warehouse/warehouse_entry.html', result = tools.en_return_data(json.dumps(return_data)))

class InWarehouse(MethodView):
    '''
    入库
    '''
    def get(self):

        try:
            #读取物流XML文件
            logisticsType=logisticsConfig()
            logisticsList= logisticsType.logistics_get_xml()
            #生成临时订单号
            store_id = request.values.get('flagshipid', '')
            # print 'ship:',logisticsList
            warehouse_type=InOutWarehouseOp()
            # print("-"*40 + "1111" + "-"*40)
            wh=OperateType()
            in_out_number=InOutWarehouseOp.CreateNumber(store_id,wh.other_in)
            op = InOutWarehouseOp()

            #发出单位
            companyType=companyConfig()
            wh_type= companyType.company_get_xml()

            in_out_type=warehouse_type.GetInOutWarehouseType()
            in_out_list=[]
            in_out_list.append(in_out_type[0])
            in_out_list.append(in_out_type[1])

            addtime = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')


            #获取旗舰店名字
            pro=FlagShipOp()
            dataList=pro.get_flagship_info_by_flagship_id(store_id)
            fname=dataList['name']
            result = {'logisticsType':logisticsList,'name':fname,'temporaryNumber':in_out_number,"addtime":addtime,'wh_type':wh_type,"in_out_type":in_out_list}

        except Exception as e:
            print(traceback.format_exc(e))
            return tools.en_return_data(json.dumps({'code': 30000}))
        return tools.flagship_render_template('storeManage/warehouse/godown_entry.html',result=tools.en_return_data(json.dumps(result)))

class get_Product_Infos(MethodView):

    def post(self):
        return_data = {'code':ServiceCode.service_exception}
        try:
            page_num = request.values.get('page_num', 0, type=int)
            per_page = request.values.get('per_page', 0, type=int)
            if  per_page == 0:
                per_page=5
            name = request.values.get('name', None, type=str)
            code = request.values.get('code', None, type=str)
            bar_code = request.values.get('bar_code', None, type=str)

            if name is '':
                name = None
            if code is '':
                code = None
            if bar_code is '':
                bar_code = None
            page = page_num - 1
            if page < 0:
                page = 0
            if per_page > 60:
                per_page = 60
            start = page *per_page
            HolaWareHouse_op = HolaWareHouse()
            if name is not  None or code is not  None or bar_code is not None:
                data, total = HolaWareHouse_op.show_all_product_filter(
                    start, per_page, putway=True, name=name, code=code, bar_code=bar_code)

            else:

                data,total = HolaWareHouse_op.show_all_product_filter(start,
                        per_page, putway=True)



            return_data ={
                'code' : ServiceCode.success,
                'data' : data,
                'total' : total
            }



        except Exception,e:
            print e
            return_data = {'code':ServiceCode.service_exception}

        return tools.en_return_data( json.dumps(return_data))

class QueryInvertoryInfo(MethodView):
        '''
        查询库存数量
        '''
        def get(self):
            good_id = request.values.get('good_id','')
            store_id = request.values.get('flagshipid','')
            warehouse_type_id = request.values.get('warehouse_type_id','')

            op = InOutWarehouseOp()
            rs = op.InventoryCountInfo(store_id,warehouse_type_id,good_id)
            print rs
            return_data = rs
            return tools.en_return_data(json.dumps(return_data))

class AddWarehouseRecord(MethodView):
        '''
        添加入库记录
        '''
        def post(self):
            return_data = {'code' : ServiceCode.service_exception}
            try:
                info_dict = {}
                info_dict['recv_site']=request.form.get('recv_site','',str)
                info_dict['send_site']=request.form.get('send_site','',str)
                info_dict['number']=request.form.get('number','',str)
                info_dict['amount']=request.form.get("in_out_number",'',int)
                info_dict['user']=request.form.get("user","",str)
                info_dict['operate_type']=request.form.get("operate_type",0,int)
                info_dict['warehousetype_id']=request.form.get('warehouse_type_id',WarehouseType.inventory_warehouse,int)
                info_dict['remark_info']=request.form.get("remark_info","",str)
                info_dict['flagship_id']=request.form.get("flagship_id",0,int)
                info_dict['logistics_company']=request.form.get('logistics_name',"",str)
                info_dict['good_id']=request.form.get("product_id",0,int)
                # product_type_id=request.form.get("product_type_id",0,int)
                code_list=request.form.get("code_list",'')
                in_wh=ShipInwarehouse()
                print '------------------------------------',info_dict['logistics_company']
                dataType=in_wh.CheckIsInSerialNumber(info_dict['good_id'],info_dict['warehousetype_id'],info_dict['flagship_id'])


                code_list = json.loads(code_list)

                if dataType == ServiceCode.goodsSnNotExist:
                    pass
                elif dataType == ServiceCode.success:
                    if str(code_list[0]) is not None and str(code_list[0]) is not '':
                        pass
                    else:
                        return_data = {'code' : ServiceCode.service_exception,
                                       'msg' : '该商品需要输入序列号'}
                        return json.dumps(return_data)
                else:

                    if str(code_list[0]) is not None and str(code_list[0]) is not '':

                        return_data = {'code' : ServiceCode.service_exception,
                                       'msg' : '该商品不需要输入序列号'}
                        return json.dumps(return_data)
                    else:
                        pass

                info_dict['code_list'] = code_list
                inout=InOutWarehouseOp()

                rs = in_wh.SaveInSerialNumberInfo(info_dict)
                return_data = rs

            except Exception,e:
                print e
                return_data = {'code' : ServiceCode.service_exception}

            return tools.en_return_data(json.dumps(return_data))
class CheckProductSn(MethodView):
    '''
    检测产品入库时是否有SN号，有则返回100
    '''
    def get(self):
        return_data={'code':ServiceCode.service_exception}
        try:
            flagship_id=request.args.get('flagshipid','')
            good_id=request.args.get('good_id','')
            warehouse_type_id=request.form.get('warehouse_type_id','')
            s_op=ShipInwarehouse()
            rs=s_op.CheckIsInSerialNumber(good_id,warehouse_type_id,flagship_id)
            return_data={'code':rs}


        except Exception,e:
            return_data={'code':ServiceCode.service_exception}
        return tools.en_return_data(json.dumps(return_data))

class InDetailed(MethodView):
    '''
    入库明细
    '''
    def get(self):

        warehouse_type=ShipInwarehouse()
        in_warehouse_list=warehouse_type.GetOutWarehouseList(1)
        store_id = request.args.get('flagshipid', 0, int)
        number = request.args.get('number','')

        result=warehouse_type.GetWarehouseDetailed(number,store_id)
        return tools.flagship_render_template('storeManage/warehouse/transfer_detail.html',result=tools.en_return_data(json.dumps(result)))

class InSearchInfo(MethodView):
    '''
    入库列表搜索
    '''
    def get(self):
        return_data = {'code' : ServiceCode.service_exception}
        page_num = request.values.get('page_num',1,int)
        per_page = request.values.get('per_page',10,int)
        operate_type_id = request.values.get('operate_type_id',0,int)
        start_time = request.values.get('start_time',None,str)
        end_time = request.values.get('end_time',None,str)
        flagshipid = request.values.get('flagshipid','',int)
        try:
            page = page_num - 1
            if page < 0:
                page = 0
            if per_page > 60:
                per_page = 60
            start = page *per_page
            per_page = 10
            op  = ShipInwarehouse()

            #operate_type_id 为 0 的话表示查询全部出库类型
            # if operate_type_id == 0:
            #     rs,total = op.GetSearchWarehouseInfo(start,per_page,start_time = start_time,end_time = end_time)
            # else:
            #     rs,total = op.GetSearchWarehouseInfo(start,per_page,operate_type=operate_type_id,
            #                                         start_time = start_time,end_time = end_time)

            if operate_type_id == 0:
                if start_time == '' and end_time == '' :
                    rs,total = op.GetSearchWarehouseInfo(start,per_page,flagshipid=flagshipid)
                else:
                    rs,total = op.GetSearchWarehouseInfo(start,per_page,start_time = start_time,end_time = end_time,flagshipid=flagshipid)
            else:
                if start_time =='' and end_time == '':
                    rs,total = op.GetSearchWarehouseInfo(start,per_page,operate_type=operate_type_id,flagshipid=flagshipid)
                else:
                    rs,total = op.GetSearchWarehouseInfo(start,per_page,operate_type=operate_type_id,start_time = start_time,end_time = end_time,flagshipid=flagshipid)



            return_data = {
                'code' : ServiceCode.success,
                'order_list' : rs,
                'total' : total
            }
            pass
        except Exception,e:
            print e
            return_data = {'code' : ServiceCode.service_exception}

        return tools.en_return_data(json.dumps(return_data))

class in_out_detailed_search(MethodView):
    '''
        出入库明细搜索
    '''
    def get(self):
        try:


            flagshipId=request.args.get('flagshipid','')
            stype=request.args.get('stype','')
            snumber=request.args.get('snumber','')
            flag=request.args.get('flag','')
            print 'number:',snumber
            sobj=ShipInwarehouse()
            rs=sobj.GetInOutDetails(flagshipId,stype,snumber,flag)
            return tools.en_return_data(json.dumps(rs))
        except Exception,e:
            print e
            return tools.en_return_data(json.dumps({'coe':ServiceCode.service_exception}))

class In_out_DetailedList(MethodView):
    '''
    出入库明细列表
    '''
    def get(self):

        shipid=request.values.get('flagshipid','',int)
        page_num = request.values.get('page_num',1,int)
        per_page = request.values.get('per_page',10,int)
        order_num = request.values.get('order_num',None,str)
        name = request.values.get('name',None)
        code = request.values.get('code',None)
        bar_code = request.values.get('bar_code',None)
        flag = request.values.get('flag',1,int)
        op = InOutWarehouseOp()
        page = page_num - 1
        if page < 0:
            page = 0
        if per_page > 60:
            per_page = 60
        start = page *per_page
        rs,total,oprate_list = op.QueryDetailInfo(start,per_page,shipid,order_number=order_num,name=name,code=code,bar_code=bar_code)
        return_data = {
            'code' : ServiceCode.success,
            'good_list' : rs,
            'total' : total,
            'operate_list':oprate_list
        }
        #print '---------------------------------',return_data
        if flag == 1:
            return tools.flagship_render_template('storeManage/warehouse/inOutStock-detail.html',result=json.dumps(return_data))
        else:
            return tools.en_return_data(json.dumps(return_data))

class search_list(MethodView):
    def get(self):
        try:
           in_obj= ShipInwarehouse()
           shipid=request.args.get('flagshipid','')
           stype=request.args.get("stype","")
           snumber=request.args.get("snumber","")#临时单号
           flag=request.args.get("flag","")#name:商品名称；code:商品编码；bar_code：商品条形码
           rs = in_obj.GetInOutDetails(shipid,stype=stype,snumber=snumber,flag=flag)
           return json.dumps({"code":ServiceCode.success,"data":rs})
        except Exception,e:
            return json.dumps({"code":ServiceCode.service_exception})

class get_SN_code(MethodView):
    '''
    检测SN号是否存在
    '''
    def get(self):
        try:
            sn_code=request.args.get('sn_code','')
            flaship_id=request.args.get('flagshipid','')
            p_id=request.args.get('productid','')
            in_obj=ShipInwarehouse()
            rs=in_obj.GetSnCodeMy(sn_code,flaship_id,p_id)
            return tools.en_return_data(json.dumps({"code":rs,'msg':''}))
        except Exception,e:
            return tools.en_return_data(json.dumps({"code":ServiceCode.service_exception}))

#

#商品仓库
class ProWarehouse(MethodView):
    '''
    商品仓库列表业务
    '''

    def get(self):
        try:
            sid = request.args.get('flagshipid', 0, int)
            flag = request.args.get('flag', 0, int)
            pname = request.args.get('pname', '', str)
            pcode = request.args.get('pcode', '', str)
            pbarcode = request.args.get('pbarcode', '', str)

            issou = False
            if len(pname) or len(pcode) or len(pbarcode):
                issou = True

            if sid <= 0:
                data = {'code':ServiceCode.params_error,'msg':u'店铺id为空'}
                if 0==flag:
                    return tools.en_return_data(json.dumps(data))
                return tools.flagship_render_template('storeManage/warehouse/warehouse.html', result = tools.en_return_data(json.dumps(data)))

            lt = request.args.get('lt', 10, int)
            pg = request.args.get('pg', 0, int)

            hwhop = HolaWareHouse()
            product = {}
            if len(pname) or len(pcode) or len(pbarcode):
                product = hwhop.get_product_info_by(pname=pname,pcode=pcode,pbarcode=pbarcode)
                if not product:
                    data = {'code':ServiceCode.data_empty,'msg':u'结果为空'}
                    if 0==flag:
                        return tools.en_return_data(json.dumps(data))
                    return tools.flagship_render_template('storeManage/warehouse/warehouse.html', result = tools.en_return_data(json.dumps(data)))

            allproducts = {}
            pId = 0
            if issou:
                pId = product.id
            else:
                allproducts = hwhop.get_all_product_dict_info(False)

            wpop = WhouseProductInfoOp()
            #mrs = wpop.get_store_product_info(storeId=sid,productId=pId,num=lt,page=pg)
            mrs = wpop.get_store_product_info(storeId=sid,productId=pId)

            rs = mrs[0]
            total = mrs[1]
            if not len(rs):
                data = {'code':ServiceCode.data_empty,'msg':u'结果为空'}
                if 0==flag:
                    return tools.en_return_data(json.dumps(data))
                return tools.flagship_render_template('storeManage/warehouse/warehouse.html', result = tools.en_return_data(json.dumps(data)))

            pnum = {}
            products = {}
            from config.warehouse_config.warehouse import warehouseConfig

            off = lt*pg

            nnum = 0
            oldpid = 0
            for v in rs:
                pid = v.good_id
                if pid != oldpid:
                    nnum = nnum+1
                    oldpid = pid

                if nnum <= off:
                    continue

                if nnum-off>lt:
                    break

                num = v.inventory_amount
                wtype = v.warehouse_type_id
                mname = 'unknownd'
                if WarehouseType.inventory_warehouse == wtype:
                    mname = 'kcunnum'
                elif WarehouseType.aftersale_warehouse == wtype:
                    mname = 'shounum'
                elif WarehouseType.transit_warehouse == wtype:
                    mname = 'zzhuang'
                elif WarehouseType.back_factory_warehouse == wtype:
                    mname = 'hchang'
                elif WarehouseType.sample_warehouse == wtype:
                    mname = 'ybennum'

                n = pnum.get(pid,{})
                if not len(n):
                    n[mname] = num
                    pnum[pid] = n
                else:
                    n[mname] = num

                d = products.get(pid,{})
                if len(d):
                    continue

                if issou:
                    d['img'] = product.img
                    d['pid'] = pid
                    d['pname'] = product.name
                    d['pcode'] = product.code
                    d['pbarcode'] = product.bar_code
                    d['specifications'] = product.specification
                    d['category'] = product.category.name
                    # d['putaway'] = int(product.putaway)
                    products[pid] = d
                    continue

                product = allproducts.get(pid,{})
                # print 'p2',allproducts.get(9,{})
                d['img'] = product.get('img','')
                d['pid'] = pid
                d['pname'] = product.get('name','')
                d['pcode'] = product.get('code','')
                d['pbarcode'] = product.get('bar_code','')
                d['specifications'] = product.get('specification','')
                # d['putaway'] = int(product.get('putaway', False))
                c = product.get('category','')

                # print '-------------类型',type(c),c

                d['category'] = c.get('name','')
                products[pid] = d

            results = []
            for k,v in products.items():
                r1 = v
                r2 = pnum.get(k,{})
                r1['kcunnum'] = r2.get('kcunnum',0)
                r1['shounum'] = r2.get('shounum',0)
                r1['zzhuang'] = r2.get('zzhuang',0)
                r1['hchang'] = r2.get('hchang',0)
                r1['ybennum'] = r2.get('ybennum',0)
                results.append(r1)


            data = {}
            data['total'] = total
            data['products'] = results
            if 0==flag:
                return tools.en_return_data(json.dumps(data))
            return tools.flagship_render_template('storeManage/warehouse/warehouse.html', result = tools.en_return_data(json.dumps(data)))
        except Exception,ex:
            print traceback.format_exc()
            data = {'code':ServiceCode.service_exception,'msg':u'服务器错误'}
            if 0==flag:
                return tools.en_return_data(json.dumps(data))
            return tools.flagship_render_template('storeManage/warehouse/warehouse.html', result = tools.en_return_data(json.dumps(data)))

class ProStockDetail(MethodView):
    '''
    商品库存明细
    '''
    def get(self):

        try:
            sid = request.args.get('flagshipid', 0, int)
            flag = request.args.get('flag', 0, int)
            bill = request.args.get('bill', '', str)
            serial = request.args.get('serial', '', str)

            issou = False
            if len(bill) or len(serial):
                issou = True

            if sid <= 0:
                data = {'code':ServiceCode.params_error,'msg':u'店铺id为空'}
                if 0==flag:
                    return tools.en_return_data(json.dumps(data))
                return tools.flagship_render_template('storeManage/warehouse/warehouse-detail.html', result = tools.en_return_data(json.dumps(data)))

            wtype = request.args.get('wtype', 0, int)
            if wtype <= 0:
                data = {'code':ServiceCode.params_error,'msg':u'仓库类型错误'}
                if 0==flag:
                    return tools.en_return_data(json.dumps(data))
                return tools.flagship_render_template('storeManage/warehouse/warehouse-detail.html', result = tools.en_return_data(json.dumps(data)))

            pid = request.args.get('pid', 0, int)
            if pid <= 0:
                data = {'code':ServiceCode.params_error,'msg':u'商品id错误'}
                if 0==flag:
                    return tools.en_return_data(json.dumps(data))
                return tools.flagship_render_template('storeManage/warehouse/warehouse-detail.html', result = tools.en_return_data(json.dumps(data)))


            lt = request.args.get('lt', 10, int)
            pg = request.args.get('pg', 0, int)

            wpop = WhouseProductInfoOp()
            result = wpop.get_store_product_detail(storeId=sid,wareType=wtype,productId=pid,billNumber=bill,serialNumber=serial,num=lt,page=pg)

            rs = result[0]
            total = result[1]

            if not len(rs):
                data = {'code':ServiceCode.data_empty,'msg':u'结果为空'}
                if 0==flag:
                    return tools.en_return_data(json.dumps(data))
                return tools.flagship_render_template('storeManage/warehouse/warehouse-detail.html', result = tools.en_return_data(json.dumps(data)))

            hwhop = HolaWareHouse()
            myproduct = hwhop.get_product_byid(pid)

            products = []
            for v in rs:
                d = {}
                pid = v["good_id"]
                d['bill'] = v["order_number"]
                d['serial'] = v["number"]
                d['pname'] = myproduct.get('name','')
                d['pcode'] = myproduct.get('code','')
                d['pbarcode'] = myproduct.get('bar_code','')
                products.append(d)

            data = {}
            data['total'] = total
            data['products'] = products
            data['deal_list'] = {OTHER_RETURN_FACTORY: u'其他返厂'}
            if 0==flag:
                return tools.en_return_data(json.dumps(data))

            return tools.flagship_render_template('storeManage/warehouse/warehouse-detail.html', result = tools.en_return_data(json.dumps(data)))
        except Exception,ex:
            print traceback.format_exc()
            data = {'code':ServiceCode.service_exception,'msg':u'服务器错误'}
            if 0==flag:
                return tools.en_return_data(json.dumps(data))
            return tools.flagship_render_template('storeManage/warehouse/warehouse-detail.html', result = tools.en_return_data(json.dumps(data)))

class UpdateProSerial(MethodView):
    '''
    切换样本仓库
    '''
    def post(self):
        try:
            sid = request.form.get('flagshipid', 0, int)
            if sid <= 0:
                data = {'code':ServiceCode.params_error,'msg':u'店铺id为空'}
                return tools.en_return_data(json.dumps(data))

            wtype = request.form.get('wtype', 0, int)
            if wtype <= 0:
                data = {'code':ServiceCode.params_error,'msg':u'仓库类型为空'}
                return tools.en_return_data(json.dumps(data))

            pid = request.form.get('pid', 0, int)
            if pid <= 0:
                data = {'code':ServiceCode.params_error,'msg':u'产品id为空'}
                return tools.en_return_data(json.dumps(data))

            bill = request.form.get('bill', '', str)
            if not len(bill):
                data = {'code':ServiceCode.params_error,'msg':u'单据号不能为空'}
                return tools.en_return_data(json.dumps(data))

            serial = request.form.get('serial', '', str)

            hwhop = HolaWareHouse()
            myproduct = hwhop.get_product_byid(pid)
            ffather = myproduct.get('father_category',{})
            ffid = ffather.get('id',0)


            if not len(serial) and ffid == Dict_Categorgory_touyingyi['id']:
                data = {'code':ServiceCode.params_error,'msg':u'主机的序列号不能为空'}
                return tools.en_return_data(json.dumps(data))

            #2016-10-25 修改
            #生成单号
            rs = InOutWarehouseOp.CreateNumber(sid,OperateType.roll_over)
            if rs['number'] is None:
                return False
            print "rs['number']:",rs['number']
            send_site = WarehouseType.get_wtype_name(WarehouseType.inventory_warehouse)
            recv_site = WarehouseType.get_wtype_name(WarehouseType.sample_warehouse)
            info_dict = {}
            info_dict["number"] = rs['number']
            # info_dict["serial_number"] = bill
            info_dict["date"] = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            info_dict["user"] = session['user']['name']
            info_dict["user_id"] = session['user']['id']
            info_dict["recv_site"] = recv_site
            info_dict["send_site"] = send_site
            info_dict["operate_type"] = OperateType.roll_over
            info_dict["in_out_number"] = 1
            info_dict["flagshipid"] = sid
            info_dict["warehouse_type_id"] = wtype
            info_dict["to_warehouse_type_id"] =WarehouseType.sample_warehouse
            info_dict["all_amount"] = 1
            good_dict = {}
            good_dict["serial_number"] = serial
            good_dict["good_id"] = pid
            good_dict["count"] = 1

            info_dict["good_list"] = [good_dict]
            print '---------------------------info_dict----------------------------',info_dict
            op = InOutWarehouseOp()
            res = op.create_number(info_dict)
            print 'res:',res

            # iowobj = InOutWarehouseOp()
            # isOk = iowobj.TurnProductToSample(storeId=sid,productId=pid,wareHouseType=wtype,billNumber=bill,serialNumber=serial)

            if res["code"] != 100:
                data = {'code':ServiceCode.dealfaild,'msg':u'服务器处理失败，请检查库存'}
                return tools.en_return_data(json.dumps(data))

            data = {'code':ServiceCode.success,'msg':u'转入样本仓成功'}
            return tools.en_return_data(json.dumps(data))

        except Exception,ex:
            print traceback.format_exc()
            data = {'code':ServiceCode.service_exception,'msg':u'服务器错误'}
            return tools.en_return_data(json.dumps(data))

class GetSampleList(MethodView):
    '''
    样品仓列表
    '''
    def get(self):
        try:
            flagshipid=request.args.get('flagshipid',0,int)
            number=request.args.get('bill','')
            lt=request.args.get('lt',10,int)
            pg=request.args.get('pg',0,int)
            flag=request.args.get('flag',0,int)
            serial=request.args.get('serial','')
            goodid=request.args.get('pid','')
            shipop=ShipInwarehouse()

            if flagshipid is None:
                data={'code':ServiceCode.params_error,'msg':u'店铺ID不能为空'}
                return tools.en_return_data(json.dumps(data))
            if goodid is None:
                data={'code':ServiceCode.params_error,'msg':u'产品ID不能为空'}
                return tools.en_return_data(json.dumps(data))
            if flag == 1:
                result=shipop.GetSampleInfo(flagshipid=flagshipid,goodid=goodid,lt=lt,pg=pg)
                redata={}
                redata['total']=result[1]
                redata['products']=result[0]
                return tools.flagship_render_template('storeManage/warehouse/sample-detail.html',result=tools.en_return_data(json.dumps(redata)))
            if flag == 0:
                result=shipop.GetSampleInfo(flagshipid=flagshipid,serial=serial,lt=lt,pg=pg,number=number,goodid=goodid)
                redata={}
                redata['total']=result[1]
                redata['products']=result[0]
                return tools.en_return_data(json.dumps(redata))

        except Exception,e:
            print traceback.format_exc()
            data={'code':ServiceCode.service_exception,'msg':u'服务器错误'}
            return tools.flagship_render_template('storeManage/warehouse/sample-detail.html',result=tools.en_return_data(json.dumps(data)))

class UpdateStock(MethodView):
    '''
    样品仓切换库存仓
    '''
    def get(self):
        try:
            flagshipid=request.args.get('flagshipid','',)
            good_id=request.args.get('pid','')
            order_number=request.args.get('bill','')
            serial=request.args.get('serial','')

            if flagshipid is None:
                data={'code':ServiceCode.params_error,'msg':u'店铺ID不能为空'}
                return json.dumps(data)
            if good_id is None:
                data={'code':ServiceCode.params_error,'msg':u'产品ID不能为空'}
                return json.dumps(data)
            if order_number is None:
                data={'code':ServiceCode.params_error,'msg':u'单号不能为空'}
                return json.dumps(data)
            if serial is None:
                data={'code':ServiceCode.params_error,'msg':u'序列号不能为空'}
                return json.dumps(data)

            # upshipop=ShipInwarehouse()
            # res=upshipop.ProductToStock(flagshipid=flagshipid,serial=serial,order_number=order_number,good_id=good_id)

            #2016-10-25 修改
            #生成单号
            rs = InOutWarehouseOp.CreateNumber(flagshipid,OperateType.roll_over)
            if rs['number'] is None:
                return False
            print "rs['number']:",rs['number']
            send_site = WarehouseType.get_wtype_name(WarehouseType.sample_warehouse)
            recv_site = WarehouseType.get_wtype_name(WarehouseType.inventory_warehouse)
            info_dict = {}
            info_dict["number"] = rs['number']
            # info_dict["serial_number"] = bill
            info_dict["date"] = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            info_dict["user"] = session['user']['name']
            info_dict["user_id"] = session['user']['id']
            info_dict["recv_site"] = recv_site
            info_dict["send_site"] = send_site
            info_dict["operate_type"] = OperateType.out_over
            info_dict["all_amount"] = 1
            info_dict["flagshipid"] = flagshipid
            info_dict["warehouse_type_id"] = WarehouseType.sample_warehouse
            info_dict["to_warehouse_type_id"] =WarehouseType.inventory_warehouse
            good_dict = {}
            good_dict["serial_number"] = serial
            good_dict["good_id"] = good_id
            good_dict["count"] = 1

            info_dict["good_list"] = [good_dict]
            # print '---------------------------info_dict11111----------------------------',info_dict
            op = InOutWarehouseOp()
            res = op.create_number(info_dict)


            if res["code"] == 100:
                returndata={'code':ServiceCode.success,'msg':u'转出成功'}
            else:
                returndata={'code':ServiceCode.dealfaild,'msg':u'转出失败'}

            return tools.en_return_data(json.dumps(returndata))
        except Exception, e:
            print traceback.format_exc()
            data={'code':ServiceCode.service_exception,'msg':u'服务器错误'}
            return tools.en_return_data(json.dumps(data))

class ExportInOutDetail(MethodView):
    def get(self):
        return_data = None
        r_data = {}
        print '****************ExportInOutDetail*************************'
        print request.values
        try:
            fs_id = request.values.get("flagshipid",None,int)
            op = InOutWarehouseOp()
            filename_path = op.get_detail_export_excel(fs_id)

            response = make_response(send_file(filename_path))
            response.headers['Content-Type'] = 'application/vnd.ms-excel'
            response.headers['Content-Disposition'] = 'attachment;filename=%s' % (
                os.path.basename(filename_path).encode('utf-8'))

            if os.path.exists(filename_path):
                os.remove(filename_path)

            # 遇到业务错误
            if False:
                raise CodeError(300,u"服务器错误")
        except CodeError as e:
            return_data = json.dumps(e.json_value())
        except Exception as e:
            print traceback.format_exc()
            return_data = json.dumps(
                {'code': ServiceCode.service_exception, 'msg': u"服务器失败",'rows': r_data})

        else:
            return response


from control_center.admin import add_url
from control_center.flagship_manage import flagship_manage, flagship_manage_prefix

add_url.flagship_add_url(u"门店仓库管理", "flagship_manage.FlagshipManageView", add_url.TYPE_ENTRY, flagship_manage_prefix,
                flagship_manage, '/warehouse_mgt/', 'WarehouseMgt', WarehouseMgt.as_view('WarehouseMgt'), 60,methods=['GET','POST'])

add_url.flagship_add_url(u"商品入库", "flagship_manage.WarehouseMgt", add_url.TYPE_ENTRY, flagship_manage_prefix,
                flagship_manage, '/in_warehouses/', 'ProductInWarehouse', ProductInWarehouse.as_view('ProductInWarehouse'), 100, methods=['GET','POST'])

add_url.flagship_add_url(u"入库列表搜索", "flagship_manage.ProductInWarehouse", add_url.TYPE_FEATURE, flagship_manage_prefix,
                flagship_manage, '/in_search_info/', 'InSearchInfo', InSearchInfo.as_view('InSearchInfo'), methods=['GET','POST'])

# 新建入库记录
add_url.flagship_add_url(u"新入库登记", "flagship_manage.ProductInWarehouse", add_url.TYPE_FEATURE, flagship_manage_prefix,
                flagship_manage, '/in_warehouse_mgt/', 'InWarehouse', InWarehouse.as_view('InWarehouse'), methods=['GET','POST'])

add_url.flagship_add_url(u"获取所有商品", "flagship_manage.InWarehouse", add_url.TYPE_FEATURE, flagship_manage_prefix,
                flagship_manage, '/Product_Infos/', 'get_Product_Infos', get_Product_Infos.as_view('get_Product_Infos'), methods=['GET','POST'])

add_url.flagship_add_url(u"检测SN号是否存在", "flagship_manage.InWarehouse", add_url.TYPE_FEATURE, flagship_manage_prefix,
                flagship_manage, '/is_sn_code/', 'get_SN_code', get_SN_code.as_view('get_SN_code'), methods=['GET','POST'])

add_url.flagship_add_url(u"检测入库商品SN号是否存在", "flagship_manage.InWarehouse", add_url.TYPE_FEATURE, flagship_manage_prefix,
                flagship_manage, '/check_sn_code/', 'CheckProductSn', CheckProductSn.as_view('CheckProductSn'), methods=['GET','POST'])

add_url.flagship_add_url(u"查询库存数量", "flagship_manage.InWarehouse", add_url.TYPE_FEATURE, flagship_manage_prefix,
                flagship_manage, '/QueryInvertoryInfo/', 'QueryInvertoryInfo', QueryInvertoryInfo.as_view('QueryInvertoryInfo'), methods=['GET','POST'])

add_url.flagship_add_url(u"保存入库信息", "flagship_manage.InWarehouse", add_url.TYPE_FUNC, flagship_manage_prefix,
                flagship_manage, '/addwarehouseInfo/', 'AddWarehouseRecord', AddWarehouseRecord.as_view('AddWarehouseRecord'), methods=['GET','POST'])

# 出入库明细
add_url.flagship_add_url(u"出入库明细", "flagship_manage.WarehouseMgt", add_url.TYPE_ENTRY, flagship_manage_prefix,
                flagship_manage, '/In_out_detailed_list/', 'In_out_DetailedList', In_out_DetailedList.as_view('In_out_DetailedList'), 70, methods=['GET','POST'])

add_url.flagship_add_url(u"出入库明细搜索", "flagship_manage.In_out_DetailedList", add_url.TYPE_FEATURE, flagship_manage_prefix,
                flagship_manage, '/search_list/', 'search_list', search_list.as_view('search_list'), methods=['GET','POST'])

add_url.flagship_add_url(u"入库单明细", "flagship_manage.In_out_DetailedList", add_url.TYPE_FEATURE, flagship_manage_prefix,
                flagship_manage, '/In_detailed/', 'InDetailed', InDetailed.as_view('InDetailed'), methods=['GET','POST'])

add_url.flagship_add_url(u"出入库明细导出", "flagship_manage.InDetailed", add_url.TYPE_FEATURE, flagship_manage_prefix,
                flagship_manage, '/export_excel/', 'ExportInOutDetail', ExportInOutDetail.as_view('ExportInOutDetail'), methods=['POST','GET'])

# 商品仓库
add_url.flagship_add_url(u"商品库存", "flagship_manage.WarehouseMgt", add_url.TYPE_ENTRY, flagship_manage_prefix,
                flagship_manage, '/pwhouse/', 'ProWarehouse', ProWarehouse.as_view('ProWarehouse'), 80,methods=['GET'])

add_url.flagship_add_url(u"商品明细", "flagship_manage.ProWarehouse", add_url.TYPE_FEATURE, flagship_manage_prefix,
                flagship_manage, '/psdetail/', 'ProStockDetail', ProStockDetail.as_view('ProStockDetail'), methods=['GET'])

add_url.flagship_add_url(u"商品操作", "flagship_manage.ProStockDetail", add_url.TYPE_FEATURE, flagship_manage_prefix,
                flagship_manage, '/pupate/', 'UpdateProSerial', UpdateProSerial.as_view('UpdateProSerial'), methods=['POST'])

add_url.flagship_add_url(u"样品仓", "flagship_manage.ProWarehouse", add_url.TYPE_FEATURE, flagship_manage_prefix,
                flagship_manage, '/sample/', 'GetSampleList', GetSampleList.as_view('GetSampleList'), methods=['POST','GET'])

add_url.flagship_add_url(u"样品仓转出", "flagship_manage.ProWarehouse", add_url.TYPE_FEATURE, flagship_manage_prefix,
                flagship_manage, '/supdate/', 'UpdateStock', UpdateStock.as_view('UpdateStock'), methods=['POST','GET'])

