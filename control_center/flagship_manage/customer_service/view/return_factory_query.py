#/usr/bin/python
#-*- coding:utf-8 -*-

'''
Created on 2016-10-19
Author : Yuan Rong
Function : query product return factory info
'''

import time
import traceback
import json
from flask import request
from flask.views import MethodView
from control_center.admin import add_url
from config.share.share_define import *
from control_center.flagship_manage import flagship_manage, flagship_manage_prefix
from public.exception.custom_exception import CodeError
from public.function import tools
from config.service_config.returncode import *
from data_mode.hola_flagship_store.control_base.controlBase import ControlEngine
from control_center.flagship_manage.customer_service.control.mixOP import QueryReturnFactoryInfoOp
from control_center.flagship_manage.customer_service.control.after_sale_operate import AfterSaleOp

class EnterQueryReturnInfoView(MethodView):
    '''进入查询返厂信息页面'''

    def get(self):
        return_data = None
        try:
            flagship_id = request.values.get('flagshipid', int)  # 店铺id
            f_type = request.values.get('f_type', 0, int)        # 搜索类型 （默认是全部，1、产品序列号，2、客户姓名 ， 3、客户联系方式）
            f_content = request.values.get('f_content', '', str) # 搜索内容（关键字精确搜素）
            r_reason = request.values.get('r_reason', None, int)    # 返厂理由（默认是全部，1、现场换货，2、现场退货，3、待客维修， 4、返厂维修，5、其他维修，6、其他返厂）
            f_state = request.values.get('f_state', 3, int)      # 搜索返厂状态类型（默认是全部，1、待返厂，2、已返厂发货，3、全部）
            curPage = request.values.get('curPage', 1, int)      # 当前页（默认为1）
            pageList = request.values.get('pageList', 10, int)   # 当前页（默认为1）

            after = AfterSaleOp()
            # 转换参数
            # 搜索类型
            if f_type == 1:
                search_type = AfterSaleOp.SEARCH_TYPE_GOODS_SKU
            elif f_type == 2:
                search_type = AfterSaleOp.SEARCH_TYPE_CUSTOMER_NAME
            elif f_type == 3:
                search_type = AfterSaleOp.SEARCH_TYPE_CUSTOMER_PHONE
            else:
                search_type = None

            if f_state == 1:
                is_fc = False
            elif f_state == 2:
                is_fc = True
            else:
                is_fc = None

            if r_reason > 0 and r_reason in DEAL_WITH_TYPE:
                DataList, total = after.fc_search(flagship_id,
                                                  is_fc,
                                                  swhere_type=search_type,
                                                  swhere_value=f_content,
                                                  page=curPage,
                                                  page_num=pageList,
                                                  deal_type=r_reason)
            else:
                 DataList, total = after.fc_search(flagship_id,
                                                  is_fc,
                                                  swhere_type=search_type,
                                                  swhere_value=f_content,
                                                  page=curPage,
                                                  page_num=pageList)
            #DataList, total, count = op.query_info(flagship_id, f_type, f_content, r_reason, f_state, curPage, pageList)
            from copy import deepcopy
            ndata_list = deepcopy(DEAL_WITH_TYPE)
            ndata_list.pop(SELF_TREATMENT)
            count = 1
            # print '*' * 40
            # print "total", total
            # print '*' * 40
            # print "DataList:", DataList
            return_data = {'code': 100,
                               'total': total,
                               'count': count,
                               'f_type_dict': {'1':"产品序列号", '2':"客户姓名", '3':"客户联系方式"},
                               'r_reason': ndata_list,
                               'rows': DataList
                            }

        except CodeError as e:
            return_data = json.dumps(e.json_value())
        except Exception as e:
            print traceback.format_exc()
            return_data = json.dumps({"code": ServiceCode.service_exception, "msg": u'服务器错误'})
        finally:
            return tools.flagship_render_template("afterSales/BackFactory.html", result=json.dumps(return_data))

class ReturnInfoQueryView(MethodView):
    '''返厂信息查询'''

    def post(self):
        return_data = None
        try:
            flagship_id = request.values.get('flagshipid', int)  # 店铺id
            f_type = request.values.get('f_type', 0, int)  # 搜索类型 （默认是全部，1、产品序列号，2、客户姓名 ， 3、客户联系方式）
            f_content = request.values.get('f_content', '', str)  # 搜索内容（关键字精确搜素）
            r_reason = request.values.get('r_reason', None, int)  # 返厂理由（默认是全部，1、现场换货，2、现场退货，3、待客维修， 4、返厂维修，5、其他维修，6、其他返厂）
            f_state = request.values.get('f_state', 0, int)  # 搜索返厂状态类型（默认是全部，1、待返厂，2、已返厂发货，3、全部）
            curPage = request.values.get('curPage', 1, int)  # 当前页（默认为1）
            pageList = request.values.get('pageList', 10, int)  # 当前页（默认为1）

            after = AfterSaleOp()
            # 转换参数
            # 搜索类型
            if f_type == 1:
                search_type = AfterSaleOp.SEARCH_TYPE_GOODS_SKU
            elif f_type == 2:
                search_type = AfterSaleOp.SEARCH_TYPE_CUSTOMER_NAME
            elif f_type == 3:
                search_type = AfterSaleOp.SEARCH_TYPE_CUSTOMER_PHONE
            else:
                search_type = None

            if f_state == 1:
                is_fc = False
            elif f_state == 2:
                is_fc = True
            else:
                is_fc = None

            if r_reason > 0 and r_reason in DEAL_WITH_TYPE:
                DataList, total = after.fc_search(flagship_id,
                                                  is_fc,
                                                  swhere_type=search_type,
                                                  swhere_value=f_content,
                                                  page=curPage,
                                                  page_num=pageList,
                                                  deal_type=r_reason)
            else:
                 DataList, total = after.fc_search(flagship_id,
                                                  is_fc,
                                                  swhere_type=search_type,
                                                  swhere_value=f_content,
                                                  page=curPage,
                                                  page_num=pageList)
            count = 1
            from copy import deepcopy
            ndata_list = deepcopy(DEAL_WITH_TYPE)
            ndata_list.pop(SELF_TREATMENT)
            # print '*' * 40
            # print "total, count", total, count
            # print '*' * 40
            # print "DataList:", DataList
            if DataList is not None:
                return_data = {'code': 100,
                               'total': total,
                               'count': count,
                               'f_type_dict': {'1': "产品序列号", '2': "客户姓名", '3': "客户联系方式"},
                               'r_reason': ndata_list,
                               'rows': DataList
                               }

        except CodeError as e:
            return_data = json.dumps(e.json_value())
        except Exception as e:
            print traceback.format_exc()
            return_data = json.dumps({"code": ServiceCode.service_exception, "msg": u'服务器错误'})
        finally:
            return tools.en_return_data(json.dumps(return_data))

class InevoryConvertToReturnFactory(MethodView):
    '''库存仓转返厂仓'''
    def post(self):
        info_dict = {}
        info_dict['flagshipid'] = request.values.get('flagshipid', int)                   # 店铺id
        info_dict['warehouse_type_id'] = int(request.values.get('from_ware_id', int))                 # 转出仓库id
        info_dict['to_warehouse_type_id'] = int(request.values.get('to_ware_id', int))                     # 转入仓库id
        info_dict['number_type'] = MV_RETURN
        info_dict['deal_with_type'] = int(request.values.get('reason_id', int))  # 处理类型id

        good_list = []
        temp = {}
        temp['good_id'] = int(request.values.get('p_id', int))                           # 商品id
        # print "good_id ", temp['good_id'], type(temp['good_id'])
        temp['serial_number'] = request.values.get('p_sn', None)                      # 商品sn
        if temp['serial_number'] is None:
            temp['serial_number'] = None
        temp['count'] = 1
        temp['product_rem'] = request.values.get('rem', None)  # 备注
        temp['is_exchange_goods'] = 0
        good_list.append(temp)
        info_dict['good_list'] = good_list


        return_data = {}
        try:
            # print "invetory convert to factory "
            op = QueryReturnFactoryInfoOp()
            return_data = op.ConvertReturnFactory(info_dict)
            if return_data['code'] == ServiceCode.success:
                return_data = {'code':return_data['code']}
                # print "#"*40
                # print "sucess"
            else:
                # print "#" * 40
                # print "no sucess"
                return_data['code'] = ServiceCode.service_exception
                raise

        except CodeError as e:
            return_data = json.dumps(e.json_value())
        except Exception as e:
            print traceback.format_exc()
            return_data = json.dumps({"code": ServiceCode.service_exception, "msg": u'服务器错误'})
        finally:
            return tools.en_return_data(json.dumps(return_data))


add_url.flagship_add_url(u"返厂查询", "flagship_manage.AfterSale", add_url.TYPE_ENTRY, flagship_manage_prefix,
                flagship_manage, '/enter_return_info_query/', 'enter_return_info_query', EnterQueryReturnInfoView.as_view('query_retuen_info'),80, methods=['GET'])

add_url.flagship_add_url(u"返厂查询搜索", "flagship_manage.enter_return_info_query", add_url.TYPE_FEATURE, flagship_manage_prefix,
                flagship_manage, '/query_retuen_info/', 'query_retuen_info', ReturnInfoQueryView.as_view('query_retuen_info'), methods=['GET', 'POST'])

add_url.flagship_add_url(u"库存仓转返厂仓", "flagship_manage.ProStockDetail", add_url.TYPE_FEATURE, flagship_manage_prefix,
                flagship_manage, '/return_factory_operate/', 'return_factory_operate', InevoryConvertToReturnFactory.as_view('return_factory_operate'), methods=['GET', 'POST'])
