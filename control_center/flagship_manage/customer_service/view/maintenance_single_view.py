#/usr/bin/python
#-*- coding:utf-8 -*-

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
from control_center.flagship_manage.customer_service.control.maintenance_single_op import MaintenanceSingleOp

class SaveMaintenanceData(MethodView):
    '''保存新建维修单信息'''

    def post(self):
        flagship_id = int(request.values.get('flagshipid', int))     #旗舰店铺id
        flagship_id = int(flagship_id)
        # print "flagship_id", flagship_id, type(flagship_id)
        numberNo = request.values.get('numberNo', None)           #单据单号
        accep_net = request.values.get('accep_net', None)         #受理网点
        state_id = int(request.values.get('state_id', int))     #状态id
        state_id = int(state_id)
        user_id = request.values.get("user_id", "")             # 用户id

        cus_info_dict = request.values.get('cus_info', None)      #客户信息字典
        if cus_info_dict is not None and cus_info_dict:
            cus_info_dict = json.loads(cus_info_dict)
            # print "cus_info_dict", cus_info_dict, type(cus_info_dict)
        pro_info_dict = request.values.get('pro_info', None)      #产品信息字典

        # print "pro_info_dict", pro_info_dict, type(pro_info_dict)
        if pro_info_dict is not None and pro_info_dict != u'':
            pro_info_dict = json.loads(pro_info_dict)
            # print "pro_info_dict", pro_info_dict, type(pro_info_dict)
        deal_info_dict = request.values.get('deal_info', None)    #处理信息字典
        if deal_info_dict is not None and deal_info_dict:
            deal_info_dict = json.loads(deal_info_dict)
            # print "deal_info_dict", deal_info_dict, type(deal_info_dict)
        main_info_dict = request.values.get('main_info', None)    #维修信息字典
        if main_info_dict is not None and main_info_dict:
            main_info_dict = json.loads(main_info_dict)
            # print "main_info_dict", main_info_dict, type(main_info_dict)
        take_mach_dict = request.values.get('take_ma_info', None) #取机信息字典
        if take_mach_dict is not None and take_mach_dict:
            take_mach_dict = json.loads(take_mach_dict)
            # print "take_mach_dict", take_mach_dict, type(take_mach_dict)

        return_data = None
        try:
            # print "---------- save main info view ------------"
            main_op = MaintenanceSingleOp()
            main_op.save_mainten_info(flagship_id, numberNo, accep_net, state_id,
                                    cus_info_dict, pro_info_dict, deal_info_dict,
                                    user_id, main_info_dict, take_mach_dict)
            return_data = json.dumps({'code': ServiceCode.success})
        except CodeError as e:
            print traceback.format_exc()
            return_data = json.dumps(e.json_value())
        except Exception as e:
            print traceback.format_exc()
            return_data = json.dumps({"code": ServiceCode.service_exception, "msg": u'服务器错误'})
        finally:
            return tools.en_return_data(return_data)


add_url.flagship_add_url(u"保存维修单信息", "flagship_manage.newrepairbill", add_url.TYPE_FEATURE, flagship_manage_prefix,
                flagship_manage, '/save_maintenance_data/', 'save_maintenance_data',
                SaveMaintenanceData.as_view('save_maintenance_data'), methods=['GET', 'POST'])
