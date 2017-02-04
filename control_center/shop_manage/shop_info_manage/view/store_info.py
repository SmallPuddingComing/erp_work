#-*-coding:utf-8-*-

from flask import session, jsonify, request
from flask.views import MethodView
from public.function import tools
import json

from control_center.flagship_manage.flagship_info_manage.control.flagship_op import FlagShipOp
from data_mode.user_center.control.mixOp import MixUserCenterOp

class StoreInfoView(MethodView):
    def get(self):
        flagship_op = FlagShipOp()
        return_data = json.dumps({
            'departments': GetStoreInfoData(),
            'flagships': flagship_op.get_all_flagship_detail_info()
        })

        # return jsonify({
        #     'departments': GetStoreInfoData(),
        #     'flagships': flagship_op.get_all_flagship_detail_info()
        # })
        return tools.en_render_template('storesinfo/storeinformation.html', data=return_data)
        #return tools.en_render_template('system/System-set.html', data=return_data)

class StoreInfodata(MethodView):
    def get(self):
        return_data = jsonify({ 'code':300 })
        try:
            page = request.args.get('page', 1, type=int)
            per_page = request.args.get('per_page', 20, type=int)
            filter = request.values.get('filter', "")
            sou = request.values.get('sou', "")
            if per_page > 60:
                per_page = 60
            start = (page-1)*per_page

            flagship_op = FlagShipOp()
            data, total = flagship_op.get_all_flagship_detail_info_page(start, per_page, filter, sou)
            return_data = jsonify({
                'flagships': data,
                'total': total,
                'code' : 100
            })
        except Exception, e:
            print e
        return tools.en_return_data(return_data)


def GetStoreInfoData():
    User = MixUserCenterOp()
    data= User.get_departments_info()
    return data

class StoreCreateView(MethodView):
    def post(self):
        return_data = jsonify({ 'code':300 })
        try:
            flagship = {}
            flagship['name'] = request.values.get('name', '')
            flagship['department_id'] = request.values.get('department_id', '')
            flagship['area'] = request.values.get('area', '')
            flagship['address'] = request.values.get('address', '')
            flagship['telephone'] = request.values.get('telephone', '')
            flagship['user_id'] = request.values.get('user_id', '')
            flagship_op = FlagShipOp()
            ret = flagship_op.add_flagship(flagship)
            if ret:
                return_data = jsonify({ 'code':100 })
            else:
                return_data = jsonify({ 'code':109 })
            pass
        except Exception, e:
            print e
        return tools.en_return_data(return_data)

class StoreEditView(MethodView):
    def post(self):
        return_data = jsonify({ 'code':300 })
        try:
            flagship = {}
            flagship_id = request.values.get('flagship_id', '')
            flagship['name'] = request.values.get('name', '')
            flagship['department_id'] = request.values.get('department_id', '')
            flagship['area'] = request.values.get('area', '')
            flagship['address'] = request.values.get('address', '')
            flagship['telephone'] = request.values.get('telephone', '')
            flagship['user_id'] = request.values.get('user_id', '')
            flagship_op = FlagShipOp()
            flagship_op.edit_flagship(id=flagship_id, flagship_info=flagship)
            return_data = jsonify({ 'code':100 })
            pass
        except Exception, e:
            print e

        return tools.en_return_data(return_data)

class storeStopBussinessView(MethodView):
    def post(self):
        return_data = jsonify({ 'code':300 })
        try:
            flagship_id = request.values.get('flagship_id', '')
            password = request.values.get('password', '')
            username = session['user']['username']
            user_op = MixUserCenterOp()
            auth = user_op.auth_password(username=username, password=password)
            if auth:
                flagship_op = FlagShipOp()
                flagship_op.stop_flagship_business(flagship_id)
                return_data = jsonify({ 'code':100 })
            else:
                return_data = jsonify({ 'code':107 })
        except Exception, e:
            print e

        return tools.en_return_data(return_data)




from control_center.admin import  add_url
from control_center.shop_manage import shop_manage, shop_manage_prefix

add_url.add_url(u"店铺资料", "shop_manage.ShopManageView", add_url.TYPE_ENTRY, shop_manage_prefix,
                shop_manage, '/flagship/Info/', 'flagshipstoreInfo', StoreInfoView.as_view('flagshipstoreInfo'),90, methods=['GET'])

add_url.add_url(u"添加门店", "shop_manage.flagshipstoreInfo", add_url.TYPE_FEATURE, shop_manage_prefix,
                shop_manage, '/flagship/add/', 'flagshipstoreAdd', StoreCreateView.as_view('flagshipstoreAdd'), methods=['POST'])

add_url.add_url(u"编辑门店", "shop_manage.flagshipstoreInfo", add_url.TYPE_FEATURE, shop_manage_prefix,
                shop_manage, '/flagship/edit/', 'flagshipstoreEdit', StoreEditView.as_view('flagshipstoreEdit'), methods=['POST'])

add_url.add_url(u"开闭门店", "shop_manage.flagshipstoreInfo", add_url.TYPE_FEATURE, shop_manage_prefix,
                shop_manage, '/flagship/stop/', 'flagshipstoreStop', storeStopBussinessView.as_view('flagshipstoreStop'), methods=['POST'])

add_url.add_url(u"旗舰店分页数据", "shop_manage.flagshipstoreInfo", add_url.TYPE_FUNC, shop_manage_prefix,
                shop_manage, '/flagship/Info_page_data/', 'infopagedata', StoreInfodata.as_view('infopagedata'), methods=['GET'])
