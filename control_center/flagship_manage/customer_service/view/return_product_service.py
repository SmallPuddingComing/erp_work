#/usr/bin/python
#-*- ucoding:utf-8 -*-
from control_center.flagship_manage import flagship_manage, flagship_manage_prefix
from control_center.admin import add_url
from flask import session, send_file
from control_center.flagship_manage.customer_service.control.after_sale_operate import AfterSaleOp
from flask.views import MethodView
from flask import render_template, current_app, request, url_for
from flask import jsonify
from flask import json
from pprint import pprint
from public.function import tools
from config.share.share_define import DEAL_WITH_TYPE,translate_dict_to_list, TH_VALUE_RANGE, TH_RECEIPTS,\
    APPEARANCE, PACKAGE
import traceback,datetime
from config.service_config.returncode import ServiceCode
from public.exception.custom_exception import CodeError
from control_center.flagship_manage.customer_service.control.return_product_service_op import ReturnService
from control_center.shop_manage.good_info_manage.control.mixOp import HolaWareHouse
from data_mode.hola_flagship_store.mode.warehouse_mode.warehouse_manage import *
from control_center.flagship_manage.warehouse_manage.control.in_out_warehouse_op import InOutWarehouseOp

from control_center.flagship_manage.flagship_info_manage.control.flagship_op import FlagShipOp
from control_center.flagship_manage.flagship_info_manage.control.mixOp import ClerkOp
from public.statement.engine import StatementEngine
from config.upload_config.upload_config import UploadConfig
import hashlib
import  time
import os


class ReturnIndex(MethodView):
    #退换货首页
    def get(self):
        return_data = None
        datas = {}
        flag = request.values.get('flag', 1, int)
        # red = redis.Redis(host='127.0.0.1')
        # print 'redis_name',red.get('name')
        try:
            after = AfterSaleOp()
            flagshipid = request.values.get('flagshipid', None,int)
            searchtype = request.values.get('type',0, int)
            searchvalue = request.values.get('value',None, str)
            starttime = request.values.get('starttime',None, str)
            stoptime = request.values.get('stoptime',None,str)
            dealtype = request.values.get('dealtype',None,int)
            page = request.values.get('page',1,int)
            pagenum = request.values.get('pagenum',10,int)

            #参数处理
            if flagshipid is None:
                raise CodeError(ServiceCode.params_error, u'缺少旗舰店信息')
            elif dealtype is not None and dealtype not in TH_VALUE_RANGE:
                raise CodeError(ServiceCode.params_error, u'处理方式数值不正确')
            elif searchtype != 0 and searchtype not in (1,2,3):
                #1:返修单号、2:产品名称、3:客户姓名
                raise CodeError(ServiceCode.params_error, u'目前不支持此搜索类型')

            if starttime is not None and stoptime is not None and starttime != u'' and stoptime != u'':
                start_time = datetime.datetime.strptime(starttime, '%Y-%m-%d')
                end_time = datetime.datetime.strptime(stoptime + " 23:59:59",
                                                      '%Y-%m-%d %H:%M:%S')
            else:
                start_time = None
                end_time = None

            new_page = page - 1
            if searchtype == 0:
                product_info_list,total = after.get_all_records_by_warehouse(
                        TH_RECEIPTS, flagshipid, new_page*pagenum,
                        pagenum,start_time=start_time,end_time=end_time, deal_type=dealtype)
            elif dealtype is None:
                product_info_list,total = after.search(flagshipid, searchtype,
                                                       searchvalue, page, pagenum,
                                                       start_time=start_time,
                                                       end_time=end_time,
                                                       )
            else:
                product_info_list,total = after.search(flagshipid, searchtype,
                                                       searchvalue, page, pagenum,
                                                       start_time=start_time,
                                                       end_time=end_time,
                                                       deal_type=[dealtype,]
                                                       )
        except CodeError as e:
            return_data = json.dumps(e.json_value())
        except Exception as e:
            print traceback.format_exc(e)
            return_data = json.dumps(
                    {'code': ServiceCode.service_exception, 'msg': u"服务器失败"})
        else:
            datas['code'] = ServiceCode.success
            datas['total'] = total
            datas['dealtype'] = translate_dict_to_list(DEAL_WITH_TYPE, TH_VALUE_RANGE)
            datas['rows'] = product_info_list
            return_data = json.dumps(datas)
        finally:
            if flag:
                return tools.flagship_render_template("afterSales/refundManage.html",result=return_data)
            else:
                return tools.en_return_data(return_data)

class ReturnDetailed(MethodView):
    '''
    退换货明细
    '''
    def get(self):
        result={}
        try:
            flagship_id=request.args.get('flagshipid', 0, int)
            number=request.args.get('number','')
            if not flagship_id or not number:
                result={'code':ServiceCode.params_error,'msg':'参数错误'}
                return tools.en_return_data(json.dumps(result))
            returnop= ReturnService()
            rs=returnop.GetOrderDetailedInfo(flagshipid=flagship_id,number=number)
            if rs:
                result['code']=ServiceCode.success
                result['data']=rs
            else:
                result['code']=ServiceCode.service_exception
                result['msg']='没有相关数据'
            return tools.flagship_render_template('afterSales/refundDetail.html',result=tools.en_return_data(json.dumps(result)))
        except Exception,e:
            print traceback.format_exc()
            result={'code':ServiceCode.service_exception,'msg':'服务器错误'}
            return tools.en_return_data(json.dumps(result))


class AddReturnService(MethodView):
    #创建退换货服务单
    def get(self):

        flagship_id = request.args.get('flagshipid',0,int)
        result = None
        try:
            if not flagship_id:
                data={'code':ServiceCode.params_error,'msg':u'店铺ID不能为空'}
                return tools.en_return_data(json.dumps(data))
            clerk_op = ClerkOp()
            clerk_infos = clerk_op.get_clerks_info(flagship_id)
            # print 'clerk_infos',clerk_infos
            # print '------------------'
            productInfoObj = HolaWareHouse()
            all_ca = productInfoObj.show_all_category()
            #退换货处理方式
            TH_dict = translate_dict_to_list(DEAL_WITH_TYPE, TH_VALUE_RANGE)



            productInfoObj = HolaWareHouse()
            all_ca = productInfoObj.show_all_category()
            #退换货处理方式
            TH_dict = translate_dict_to_list(DEAL_WITH_TYPE, TH_VALUE_RANGE)

            if not flagship_id:
                data={'code':ServiceCode.params_error,'msg':u'店铺ID不能为空'}
                return tools.en_return_data(json.dumps(data))
            clerk_op = ClerkOp()
            clerk_infos = clerk_op.get_clerks_info(flagship_id)
            # print 'clerk_infos',clerk_infos
            # print '------------------'
            productInfoObj = HolaWareHouse()
            all_ca = productInfoObj.show_all_category()
            #退换货处理方式
            TH_dict = translate_dict_to_list(DEAL_WITH_TYPE, TH_VALUE_RANGE)

            #退换货产品外观
            #Product_dict=Product_Appearance.treatment_method_dict
            Product_dict = translate_dict_to_list(APPEARANCE)



            #退换货产品包装
            package_dict=translate_dict_to_list(PACKAGE)
            #生成退换货单
            from public.sale_share.share_function import ShareFunctionOp
            in_out_obj=ShareFunctionOp()
            THnumber=in_out_obj.create_numberNo(flagship_id,OperateType.return_service)
            THnumber = THnumber['number']
            pro=FlagShipOp()
            dataList=pro.get_flagship_info_by_flagship_id(flagship_id)
            flagshipName=dataList['name']
            result={'code':'100','category':all_ca,
                    'clerk_infos':clerk_infos,
                    'handle_mode':TH_dict,
                    'product_exterior':Product_dict,
                    'product_packing':package_dict,
                    'dateTime':datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    'number':THnumber,
                    'network_spot':flagshipName,

            }


            # r_obj.get_material_baseinfo()
        except CodeError as e:
            result = e.json_value()
        except Exception:
            print traceback.format_exc()
            result = {'code': ServiceCode.exception_op, 'msg': u'服務器操作失敗'}
        finally:
            return tools.flagship_render_template('afterSales/newRefund.html',result=json.dumps(result))


class GetReturnProductList(MethodView):
    def get(self):
        try:
            categories_id=request.args.get('categories_id',0,int)
            if not categories_id:
                data={'code':ServiceCode.params_error,'msg':u'产品类别ID不能为空'}
                return tools.en_return_data(json.dumps(data))
            returnop= ReturnService()
            print 'categories_id',categories_id
            rs=returnop.GetReturnProductInfo(categories_id=categories_id)

            print 'rs',rs

            return_data={'code':ServiceCode.success,'msg':'OK','data':rs}
            return tools.en_return_data(json.dumps(return_data))
        except Exception,e:
            print traceback.format_exc()
            return_data={'code':ServiceCode.service_exception,'msg':'服务器错误'}
            return return_data
class GetOrderQuery(MethodView):
    def get(self):
        #查询订单
        try:
            flagshipid = request.args.get('flagshipid',0,int)
            product_name = request.args.get('product_id','')
            serial = request.args.get('serial','')
            category = request.args.get('category','')
            pl = request.args.get('pl',0,int)
            pagesize = request.args.get('pagesize',10,int)
            work_number = request.args.get('work_number','')




            if not flagshipid:
                r_data={'code':ServiceCode.params_error,'msg':'店铺ID不能为空'}
                return r_data
            if not product_name:
                r_data={'code':ServiceCode.params_error,'msg':'商品名称不能为空'}
                return r_data

            flagshipid_dict = {'flagshipid': flagshipid,
                               'serial': serial,
                               'product_name': product_name,
                               'pl': pl,
                               'pagesize': pagesize,
                               'category': category,
                               'work_number': work_number}
            returnop = ReturnService()
            result = returnop.GetOrderQuery(flagshipid_dict)

            # print 'result----',flagshipid_dict


            redata={}
            # redata['total']=result[1]
            # redata['data']=result[0]
            return tools.en_return_data(json.dumps(result))
        except Exception , e:
            print traceback.format_exc()
            re_data={'code':ServiceCode.service_exception,'msg':'服务器异常'}
            return re_data

class GetOrderInfos(MethodView):
    def get(self):
        result={}
        try:
            #通过订单查询订单下详细详细
            pl=request.args.get('pl',0,int)
            pagesize=request.args.get('pagesize',5,int)
            flagshipid=request.args.get('flagshipid',0,int)
            order_number=request.args.get('order_number','')
            if not flagshipid:
                r_data={'code':ServiceCode.params_error,'msg':'店铺ID不能为空'}
                return tools.en_return_data(json.dumps(r_data))
            if not order_number:
                r_data={'code':ServiceCode.params_error,'msg':'订单号不能为空'}
                return tools.en_return_data(json.dumps(r_data))
            order_list={'flagshipid':flagshipid,'order_number':order_number,'pl':pl,'pagesize':pagesize}
            returnop= ReturnService()
            try:
                result=returnop.GetOrderInfos(order_list)
            except Exception,e:
                print traceback.format_exc()
            redata={}
            # redata['total']=result[1]
            # redata['data']=result[0]
            result['code']=ServiceCode.success
            return tools.en_return_data(json.dumps(result))
        except Exception,e:
            print traceback.format_exc()
            re_data={'code':ServiceCode.service_exception,'msg':'服务器异常'}
            return tools.en_return_data(json.dumps(re_data))


class GetStockInfoVew(MethodView):
    '''
        查看库存
    '''
    def get(self):
        result={}
        try:
            flagship_id=request.args.get('flagshipid',0,int)
            pl=request.args.get('pl',0,int)
            pagesize=request.args.get('pagesize',5,int)
            product_id_list=request.args.get('product_id_list')
            product_id_list=json.loads(product_id_list)
            if not product_id_list:
                product_id_list=[]

            print 'product_id_list',product_id_list,type(product_id_list),len(product_id_list)

            # product_id_list=product_id_list.split(',')
            if not flagship_id:
                result={'code':ServiceCode.params_error,'msg':'店铺ID不能为空'}
                return result
            returnop= ReturnService()
            res=returnop.GetStockInfo(flagshipid=flagship_id,pl=pl,pagesize=pagesize,product_id_list=product_id_list)
            if res:
                pro=FlagShipOp()
                dataList=pro.get_flagship_info_by_flagship_id(flagship_id)
                flagshipName=dataList['name']
                res['code']=ServiceCode.success
                res['network_spot']=flagshipName
                res['msg']='OK'
            else:
                res['code']=ServiceCode.service_exception
                res['msg']='返回数据失败'
            return tools.en_return_data(json.dumps(res))
        except Exception,e:
            print traceback.format_exc()
            result={'code':ServiceCode.service_exception,'msg':'服务器错误'}
            return tools.en_return_data(json.dumps(result))


class CheckSnCode(MethodView):
    def get(self):
        result={}
        try:
            flashipid=request.args.get('flagshipid',0,int)
            sn=request.args.get('sn','')
            productid=request.args.get('productid',0,int)
            if not flashipid or not sn or not productid:
                result={'code':ServiceCode.params_error,'msg':'参数错误'}
                return tools.en_return_data(json.dumps(result))
            returnop= ReturnService()
            rs=returnop.CheckSn(flashipid,productid,sn)
            if rs == 100:
                result={'code':ServiceCode.success,'msg':'成功'}
            else:
                result={'code':ServiceCode.service_exception,'msg':'该商品部存在或者已出库'}
            return tools.en_return_data(json.dumps(result))
        except Exception,e:
            print traceback.format_exc()
            result={'code':ServiceCode.service_exception,'msg':'服务器错误'}
            return tools.en_return_data(json.dumps(result))
class SaveOrderInfos(MethodView):
    def post(self):
        result={}
        try:
            flagshipid=request.form.get('flagshipid',0,int)
            number=request.form.get('number','')
            customerName=request.form.get('customerName','')
            customerPhone=request.form.get('customerPhone','')
            customerEmail=request.form.get('customerEmail','')
            customerAddress=request.form.get('customerAddress','')

            relation_order_number=request.form.get('relation_order_number','')
            buy_machine_tiem=request.form.get('buy_machine_tiem','')#购机时间
            invoice=request.form.get('invoice','')
            product_id=request.form.get('product_id','')
            serial=request.form.get('serial','')
            is_shop_voucher=request.form.get('is_shop_voucher','')
            treatment_list=request.form.get('treatment_list','')

            # print 'treatment_list',treatment_list
            treatment_list=(treatment_list)
            other_info=request.form.get('other_info','')

            treatment=request.form.get('treatment','')
            problem_describe=request.form.get('problem_describe','')
            other_info_list=request.form.get('other_info_list','')
            other_info_list=(other_info_list)
            quote=request.form.get('quote','')
            actual_amount=request.form.get('actual_amount','')
            dateTime=request.form.get('dateTime','')
            add_user=request.form.get('add_user','')
            rem=request.form.get('rem','')
            #print 'flagshipid',flagshipid,'customerName',customerName,'customerPhone',customerPhone,'treatment',treatment
            if not flagshipid or not customerName or not customerPhone or not product_id or not treatment:
                result={'code':ServiceCode.params_error,'msg':'参数错误'}
                return tools.en_return_data(json.dumps(result))
            from control_center.flagship_manage.warehouse_manage.control.ship_in_warehouse_op import ShipInwarehouse
            shipinwarehosueop = ShipInwarehouse()

            new_treatment_list = json.loads(treatment_list)
            new_other_info_list = json.loads(other_info_list)
            if len(new_other_info_list) > 0:
                if len(new_treatment_list) == len(new_other_info_list):
                    pass
                else:
                    result = {'code': ServiceCode.params_error, 'msg': '退换货数量不一致'}
                    return tools.en_return_data(json.dumps(result))

                treatment_list_number = []
                new_other_info_number = []

                for item in new_treatment_list:
                    if item['serial']:
                        treatment_list_number.append(item['serial'])

                for item in new_other_info_list:
                    if item['serial_number']:
                        new_other_info_number.append(item['serial_number'])

                tmp = [val for val in treatment_list_number if val in new_other_info_number]
                if len(tmp) > 0:
                    result = {'code': ServiceCode.params_error, 'msg': '退换货货序列号重复'}
                    return tools.en_return_data(json.dumps(result))

                for item in new_other_info_list:
                    res_sn = shipinwarehosueop.CheckProductSN(item['good_id'])
                    if res_sn['code'] == ServiceCode.success:
                        if not item['serial_number']:
                            result = {'code': ServiceCode.params_error, 'msg': '请输入产品序列号'}
                            return tools.en_return_data(json.dumps(result))
            returnop= ReturnService()
            return_dict={}
            return_dict['flagshipid']=flagshipid
            return_dict['product_id']=product_id
            return_dict['number']=number
            return_dict['customerName']=customerName
            return_dict['customerPhone']=customerPhone
            return_dict['customerEmail']=customerEmail
            return_dict['customerAddress']=customerAddress
            return_dict['relation_order_number']=relation_order_number
            return_dict['buy_machine_tiem']=buy_machine_tiem
            return_dict['invoice']=invoice
            return_dict['serial']=serial
            return_dict['is_shop_voucher']=is_shop_voucher
            return_dict['treatment_list']=treatment_list
            return_dict['other_info']=other_info
            return_dict['treatment']=treatment

            return_dict['problem_describe']=problem_describe
            return_dict['other_info_list']=other_info_list
            return_dict['quote']=quote
            return_dict['actual_amount']=actual_amount
            return_dict['dateTime']=dateTime
            return_dict['add_user']=add_user
            return_dict['rem']=rem



            rs=returnop.AddServiceInfo(return_dict)
            if rs['code'] == ServiceCode.success:
                result={'code':ServiceCode.success,'msg':'添加成功','th_number':rs['th_number'],'in_number':rs['in_number'],'out_number':rs['out_number']}
            else:
                result={'code':ServiceCode.service_exception,'msg':'添加失败'}
            return tools.en_return_data(json.dumps(result))
        except Exception,e:
            print traceback.format_exc()
            result={'code':ServiceCode.service_exception,'msg':'服务器错误'}
            return tools.en_return_data(json.dumps(result))


class UpdateSaveInfos(MethodView):
    def get(self):
        result={}
        try:
            params_dict={}
            params_dict['flagshipid']=request.args.get('flagshipid',0,int)
            params_dict['number']=request.args.get('number','')
            params_dict['customerName']=request.args.get('customerName','')
            params_dict['customerPhone']=request.args.get('customerPhone','')
            params_dict['customerEmail']=request.args.get('customerEmail','')
            params_dict['customerAddress']=request.args.get('customerAddress','')
            params_dict['is_shop_voucher']=request.args.get('is_shop_voucher','')
            params_dict['problem_describe']=request.args.get('problem_describe','')
            params_dict['quote']=request.args.get('quote','')
            params_dict['actual_amount']=request.args.get('actual_amount','')
            params_dict['other_info']=request.args.get('other_info','')
            params_dict['rem']=request.args.get('rem','')

            if not params_dict['flagshipid'] or not params_dict['number']:
                result={'code':ServiceCode.params_error,'msg':'参数错误'}
                return tools.en_return_data(json.dumps(result))
            returnop= ReturnService()
            res=returnop.UpdateOrderInfo(params_dict)
            if res:
                result={'code':ServiceCode.success,'msg':'成功'}
            else:
                result={'code':ServiceCode.service_exception,'msg':'编辑失败'}
            return tools.en_return_data(json.dumps(result))
        except Exception,e:
            print traceback.format_exc()
            result={'code':ServiceCode.service_exception,'msg':'服务器错误'}
            return tools.en_return_data(json.dumps(result))

class GetPackageInfos(MethodView):
    def get(self):
        result={}
        try:
            package_number = request.args.get('package_number','')
            order_no = request.args.get('order_no','')
            flagship_id = request.args.get('flagshipid','')
            if not package_number or not flagship_id or not order_no:
                result={'code':ServiceCode.params_error,'msg':'参数错误'}
                return tools.en_return_data(json.dumps(result))
            returnop = ReturnService()
            res=returnop.GetPackageInfo(package_number,order_no)
            if res:
                result = {'code':ServiceCode.success,'msg':'成功','data':res}
            else:
                result = {'code':ServiceCode.service_exception,'msg':'没有相应数据'}
            return tools.en_return_data(json.dumps(result))
        except Exception,e:
            print traceback.format_exc()
            result = {'code':ServiceCode.service_exception,'msg':'服务器错误'}
            return tools.en_return_data(json.dumps(result))

class GetPrintTicket(MethodView):
    def get(self):
        result={}
        try:
            flagship_id=request.args.get('flagshipid',0,int)
            number=request.args.get('number','')
            if not flagship_id or not number:
                result={'code':ServiceCode.params_error,'msg':'参数错误'}
                return tools.en_return_data(json.dumps(result))
            returnop = ReturnService()
            res=returnop.GetPrintTick(flagship_id,number)

            if res:
                res['code'] = ServiceCode.success
                return tools.en_return_data(json.dumps(res))
            else:
                result = {'code':ServiceCode.service_exception,'msg':'没有相关数据'}
                return tools.en_return_data(json.dumps(result))
        except Exception,e:
            print traceback.format_exc()
            result={'code':ServiceCode.success,'msg':'服务器错误'}
            return tools.en_return_data(json.dumps(result))

class RefundSuccess(MethodView):
    def get(self):
        result={}
        try:
            flagshipid=request.args.get('flagshipid','')
            th_number=request.args.get('th_number','')
            in_number=request.args.get('in_number','')
            out_number=request.args.get('out_number','')
            if not flagshipid:
                result={'code':ServiceCode.params_error,'msg':'店铺ID'}
                return tools.en_return_data(json.dumps(result))
            result={'th_number':th_number,'in_number':in_number,'out_number':out_number}
            return tools.flagship_render_template("afterSales/refundSuccess.html",result=tools.en_return_data(json.dumps(result)))
        except Exception,e:
            result={'code':ServiceCode.service_exception,'mgs':'服务器错误'}
            return tools.en_return_data(json.dumps(result))


class ExportTHData(MethodView):
    """
    导出旗舰店相应的数据
    """
    def get(self):
        from datetime import datetime

        try:
            flagship_id = request.values.get('flagshipid', None, int)
            print("flagship_id:",flagship_id,"|" ,type("flagship_id"))
            if flagship_id is None:
                raise CodeError(ServiceCode.params_error, u'请指定旗舰店')

            title = [u'序号', u'门店信息', u'处理方式', u'退货单号',
                     u'受理人', u'受理时间', u'客户姓名', u'客户联系方式',
                     u'关联订单号', u'购机日期', u'发票单号', u'关联订单金额',
                     u'关联订单应收金额', u'关联订单实收金额', u'换机商品名称',
                     u'换机商品数量', u'换机金额', u'退换货差价金额', u'退换货实收金额']
            # 创建文件，写入标题
            filepath = UploadConfig.SERVER_ERP_FIle + hashlib.md5(str(time.time())).hexdigest() + '.xlsx'
            statement = StatementEngine(filepath)
            sheet = statement.select_sheet(u'退换货单')
            statement.write_row(sheet, title)
            # 获取搜索内容
            after = AfterSaleOp()
            content_list = after.th_export_data(int(flagship_id))

            filename = content_list[0][1] + u'_退换货单EXECL表_' + datetime.now().strftime("%Y%m%d") + u'.xlsx'
            # 写入内容
            for row in content_list:
                statement.write_row(sheet, row)

            # 将内容保存后，转换为报文流
            statement.save()
            content = send_file(filepath)
            os.remove(filepath)
        except CodeError as e:
            return tools.en_return_data(json.dumps(e.json_value()))
        except Exception as e:
            print traceback.format_exc()
            return tools.en_return_data(json.dumps({
                'code': 300,
                'msg': u'服务器错误'
            }))
        else:
            return tools.en_return_execl(content=content, filename=filename)

class CheckHaveInHand(MethodView):
    def get(self):
        result = {}
        try:
            returnop = ReturnService()
            flagshipid=request.args.get('flagshipid',0,int)
            serial_list = request.args.get('serial_list','')
            serial_list = json.loads(serial_list)
            if not flagshipid:
                result = {'code':ServiceCode.params_error,'msg':'参数错误'}
                return tools.en_return_data(json.dumps(result))
            rs=returnop.CheckProductIsFlow(flagshipid,serial_list)
            if len(serial_list) > 0:
                flag_flow=True
                error_serial = ''
                for key,val in enumerate(rs):
                    # print '--==--',val[serial_list[key]],type(val[serial_list[key]])
                    if val[serial_list[key]] == 'True':
                        pass
                    else:
                      error_serial=serial_list[key]
                      flag_flow = False
                      # print '-----------',flag_flow
                      break
                    # print 'serial_list[key]',serial_list[key]
                # print 'flag_flow',flag_flow
                if flag_flow:
                    result = {'code':ServiceCode.success,'msg':'OK'}
                else:
                    result = {'code':ServiceCode.service_exception,'msg':'序列号为'+error_serial+'在维修中'}
            else:
                result = {'code':ServiceCode.success,'msg':'OK'}

            return tools.en_return_data(json.dumps(result))

        except Exception , e:
            print traceback.format_exc()
            result = {'code':ServiceCode.service_exception,'msg':'服务器错误'}
            return tools.en_return_data(json.dumps(result))


add_url.flagship_add_url(u"退换管理", "flagship_manage.AfterSale", add_url.TYPE_ENTRY, flagship_manage_prefix,
                flagship_manage, '/returnservice/', 'ReturnIndex', ReturnIndex.as_view('ReturnIndex'), 100,methods=['GET'])

# 新建退换货服务单
add_url.flagship_add_url(u"新建退换服务单", "flagship_manage.ReturnIndex", add_url.TYPE_FEATURE, flagship_manage_prefix,
                flagship_manage, '/addservice/', 'AddReturnService', AddReturnService.as_view('ReturnDetailed'), 60,methods=['GET','POST'])

add_url.flagship_add_url(u"查询订单", "flagship_manage.AddReturnService", add_url.TYPE_FEATURE, flagship_manage_prefix,
                flagship_manage, '/orderquery/', 'GetOrderQuery', GetOrderQuery.as_view('GetOrderQuery'), 60,methods=['GET','POST'])

add_url.flagship_add_url(u"通过销售订单查详细", "flagship_manage.AddReturnService", add_url.TYPE_FEATURE, flagship_manage_prefix,
                flagship_manage, '/orderqueryinfo/', 'GetOrderInfos', GetOrderInfos.as_view('GetOrderInfos'), 60,methods=['GET','POST'])

add_url.flagship_add_url(u"获取库存所有产品信息", "flagship_manage.AddReturnService", add_url.TYPE_FEATURE, flagship_manage_prefix,
                flagship_manage, '/getstockinfos/', 'GetStockInfoVew', GetStockInfoVew.as_view('GetStockInfoVew'), 60,methods=['GET','POST'])

add_url.flagship_add_url(u"通过产品类别获取对应产品", "flagship_manage.AddReturnService", add_url.TYPE_FEATURE, flagship_manage_prefix,
                flagship_manage, '/getproductlist/', 'GetReturnProductList', GetReturnProductList.as_view('GetReturnProductList'), 60,methods=['GET','POST'])

add_url.flagship_add_url(u"检测序列号", "flagship_manage.AddReturnService", add_url.TYPE_FEATURE, flagship_manage_prefix,
                flagship_manage, '/ischecksn/', 'CheckSnCode', CheckSnCode.as_view('CheckSnCode'), 60,methods=['GET','POST'])

add_url.flagship_add_url(u"保存新建退换", "flagship_manage.AddReturnService", add_url.TYPE_FEATURE, flagship_manage_prefix,
                flagship_manage, '/savecustomerorder/', 'SaveOrderInfos', SaveOrderInfos.as_view('SaveOrderInfos'), 60,methods=['GET','POST'])

add_url.flagship_add_url(u"获取套餐相应信息", "flagship_manage.AddReturnService", add_url.TYPE_FEATURE, flagship_manage_prefix,
                flagship_manage, '/getpackageinfo/', 'GetPackageInfos', GetPackageInfos.as_view('GetPackageInfos'), 60,methods=['GET','POST'])

add_url.flagship_add_url(u"成功跳转", "flagship_manage.AddReturnService", add_url.TYPE_FEATURE, flagship_manage_prefix,
                flagship_manage, '/gotosuccess/', 'RefundSuccess', RefundSuccess.as_view('RefundSuccess'), 60,methods=['GET','POST'])

add_url.flagship_add_url(u"导出退换数据", "flagship_manage.AddReturnService", add_url.TYPE_FEATURE, flagship_manage_prefix,
                         flagship_manage, '/get_th_statement/', 'ExportTHData', ExportTHData.as_view('ExportTHData'), 20, methods=['GET'])

add_url.flagship_add_url(u"检测退换货是否在维修中", "flagship_manage.AddReturnService", add_url.TYPE_FEATURE, flagship_manage_prefix,
                         flagship_manage, '/have_in_hand/', 'CheckHaveInHand', CheckHaveInHand.as_view('CheckHaveInHand'), 20, methods=['GET'])

# 编辑保存
add_url.flagship_add_url(u"退换货明细", "flagship_manage.ReturnIndex", add_url.TYPE_FEATURE, flagship_manage_prefix,
                flagship_manage, '/returndetailed/', 'ReturnDetailed', ReturnDetailed.as_view('ReturnDetailed'), 60,methods=['GET','POST'])

add_url.flagship_add_url(u"编辑保存", "flagship_manage.ReturnDetailed", add_url.TYPE_FEATURE, flagship_manage_prefix,
                flagship_manage, '/updatesavecustomer/', 'UpdateSaveInfos', UpdateSaveInfos.as_view('UpdateSaveInfos'), 60,methods=['GET','POST'])

add_url.flagship_add_url(u"打印pos小票", "flagship_manage.ReturnDetailed", add_url.TYPE_FEATURE, flagship_manage_prefix,
                flagship_manage, '/printticket/', 'GetPrintTicket', GetPrintTicket.as_view('GetPrintTicket'), 60,methods=['GET','POST'])










