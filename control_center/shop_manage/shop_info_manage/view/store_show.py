#-*-coding:utf-8-*-

from flask import session, jsonify, request
from flask.views import MethodView
from public.function import tools
from public.upload_download.upload_download import pub_upload_picture_to_server
from public.upload_download.upload_download import pub_upload_picture_to_qiniu

import json

from control_center.flagship_manage.flagship_info_manage.control.flagship_op import FlagShipOp

class StoreShowView(MethodView):
    def get(self):
        flagship_op = FlagShipOp()
        data = flagship_op.show_flagships()
        return_data = json.dumps({
            'data': data,
        })
        return tools.en_render_template('storesinfo/storepics.html', data = return_data)


class StoreShowExampleView(MethodView):
    def get(self):
        flagship_op = FlagShipOp()
        data = flagship_op.show_flagships_example_pictures()
        return_data = json.dumps({
            'data': data,
        })
        return tools.en_render_template('storesinfo/storedemopic.html', data = return_data)

class ExampleNeedEdit(MethodView):
    def post(self):
        return_data = jsonify({ 'code':300 })
        try:
            needs = request.values.get('needs', '')
            flagship_op = FlagShipOp()
            flagship_op.edit_example_need(needs)
            return_data = jsonify({ 'code':100 })
        except Exception, e:
            print e
        return tools.en_return_data(return_data)

class ExamplePicAdd(MethodView):
    def post(self):
        return_data = jsonify({ 'code':300 })
        try:
            state = pub_upload_picture_to_server()
            local_path = state.get('path')
            s, path = pub_upload_picture_to_qiniu(state)
            if not s:
                return_data = jsonify({'code': 112})
            else:
                flagship_op = FlagShipOp()
                flagship_op.add_example_picture(path, local_path)
                return_data = jsonify({ 'code':100 })
        except Exception, e:
            print e
        return tools.en_return_data(return_data)

class ExamplePicDelete(MethodView):
    def post(self):
        return_data = jsonify({ 'code':300 })
        try:
            show_id = request.values.get('show_id', '')
            flagship_op = FlagShipOp()
            flagship_op.delete_example_picture(show_id)

            return_data = jsonify({ 'code':100 })
        except Exception, e:
            print e
        return tools.en_return_data(return_data)


class ExamplePicEdit(MethodView):
    def post(self):
        return_data = jsonify({ 'code':300 })
        try:
            show_id = request.values.get('show_id', '')
            state = pub_upload_picture_to_server()
            local_path = state.get('path')
            s, path = pub_upload_picture_to_qiniu(state)
            if not s:
                return_data = jsonify({'code': 112})
            else:
                flagship_op = FlagShipOp()
                flagship_op.edit_example_picture(show_id, path, local_path)
                return_data = jsonify({ 'code':100 })
        except Exception, e:
            print e
        return tools.en_return_data(return_data)


class OneStoreShowView(MethodView):
    def get(self):
        return_data = None
        upload = False
        try:
            flagshipid = request.values.get('flagshipid', '')
            flagship_op = FlagShipOp()
            data = flagship_op.show_flagships_pictures(flagshipid)
            if len(data['show']):
                upload = True
            return_data = json.dumps({
                'data': data,
            })
        except Exception, e:
            print e
        if upload:
            return tools.en_render_template('storesinfo/storepic-detail2.html', data = return_data)
        else:
            return tools.en_render_template('storesinfo/storepic-detail1.html', data = return_data)

# class OneStoreShowCheck(MethodView):
#     def post(self):
#         return_data = jsonify({ 'code':300 })
#         try:
#             flagshipid = request.values.get('flagshipid', '')
#             check_statu = request.values.get('check_statu', '')
#             comment = request.values.get('comment', '')
#             user_id = 1
#             if 0:
#                 user_id = session['user']['id']
#             flagship_op = FlagShipOp()
#             flagship_op.modify_check(flagshipid, check_statu, user_id, comment)
#             return_data = jsonify({ 'code':100 })
#         except Exception, e:
#             print e
#         return tools.en_return_data(return_data)

from control_center.admin import  add_url
from control_center.shop_manage import shop_manage, shop_manage_prefix

add_url.add_url(u"门店展示", "shop_manage.flagshipstoreInfo", add_url.TYPE_FEATURE, shop_manage_prefix,
                shop_manage, '/flagship/show/', 'flagshipstoreShow', StoreShowView.as_view('flagshipstoreShow'), methods=['GET'])

add_url.add_url(u"管理陈列范例", "shop_manage.flagshipstoreInfo", add_url.TYPE_FEATURE, shop_manage_prefix,
                shop_manage, '/flagship/example_show/', 'flagshipexampleshow', StoreShowExampleView.as_view('flagshipexampleshow'), methods=['GET'])

add_url.add_url(u"门店示例需求编辑", "shop_manage.flagshipexampleshow", add_url.TYPE_FEATURE, shop_manage_prefix,
                shop_manage, '/flagship/example_show_need_edit/', 'exampleshowneededit', ExampleNeedEdit.as_view('exampleshowneededit'), methods=['POST'])

add_url.add_url(u"门店示例图片增加", "shop_manage.flagshipexampleshow", add_url.TYPE_FEATURE, shop_manage_prefix,
                shop_manage, '/flagship/example_show_pic_add/', 'exampleshowpicadd', ExamplePicAdd.as_view('exampleshowpicadd'), methods=['POST'])

add_url.add_url(u"门店示例图片删除", "shop_manage.flagshipexampleshow", add_url.TYPE_FEATURE, shop_manage_prefix,
                shop_manage, '/flagship/example_show_pic_del/', 'exampleshowpicdel', ExamplePicDelete.as_view('exampleshowpicdel'), methods=['POST'])

add_url.add_url(u"门店示例图片编辑", "shop_manage.flagshipexampleshow", add_url.TYPE_FEATURE, shop_manage_prefix,
                shop_manage, '/flagship/example_show_pic_edit/', 'exampleshowpicedit', ExamplePicEdit.as_view('exampleshowpicedit'), methods=['POST'])

add_url.add_url(u"查看单个门店陈列", "shop_manage.flagshipexampleshow", add_url.TYPE_FEATURE, shop_manage_prefix,
                shop_manage, '/flagship/one_flagship_show/', 'oneflagshipshow', OneStoreShowView.as_view('oneflagshipshow'), methods=['GET'])


# add_url.add_url(u"门店展示审核", "shop_manage.oneflagshipshow", add_url.TYPE_FEATURE, shop_manage_prefix,
#                 shop_manage, '/flagship/flagship_show_check/', 'flagshipshowcheck', OneStoreShowCheck.as_view('flagshipshowcheck'), methods=['POST'])
