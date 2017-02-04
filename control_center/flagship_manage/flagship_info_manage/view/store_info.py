# coding:utf8

import json

from flask import request, jsonify
from flask.views import MethodView

from control_center.flagship_manage.flagship_info_manage.control.mixOp import FlagShipOp
from control_center.flagship_manage.flagship_info_manage.control import flagship_op
from public.function import tools
from public.upload_download.upload_download import pub_upload_picture_to_qiniu
from public.upload_download.upload_download import pub_upload_picture_to_server
from control_center.admin import add_url
from control_center.flagship_manage import flagship_manage, flagship_manage_prefix

class StoreManage(MethodView):
    # 店铺管理

    def get(self):
        # store_daily/store_admin/StoreManage
        return tools.flagship_render_template('storeManage/StoreManage.html')

class StoreInfo(MethodView):
    # 店铺信息
    '''
    '''
    def get(self):
        store_id = request.args.get('flagshipid', 1,int)
        fs = FlagShipOp()
        result = fs.get_flagship_info(store_id)
        # from control_center.departments.flagship.control import flagship_op
        op = flagship_op.FlagShipOp()
        statu, picture = op.get_flagship_checkstatu(store_id)
        result['check_statu'] = statu
        result['picture'] = picture
        return tools.flagship_render_template('storeManage/StoreInfo.html', result = json.dumps(result))

    def post(self):
        # :param fs_id: 旗舰店id
        # :param telephone: 服务电话
        # :param leader_telephone: 店长电话
        print request.form

        fs_id = request.form.get("flagshipid", int)
        telephone = request.form.get("telephone",'',str)
        leader_telephone = request.form.get("leader_telephone", '', str)
        fs = FlagShipOp()
        rs = fs.save_flagship_info(fs_id, telephone, leader_telephone)
        return rs

class ExampleShow(MethodView):
    def get(self):
        flagshipOp = flagship_op.FlagShipOp()
        data = flagshipOp.show_flagships_example_pictures()
        return_data = json.dumps({
            'data': data,
        })
        return tools.flagship_render_template('storeManage/showdemopics.html', data = return_data)

class StoreShowPic(MethodView):
    def get(self):
        flagshipOp = flagship_op.FlagShipOp()
        flagshipid = request.values.get('flagshipid', '')
        data = flagshipOp.show_flagships_pictures(flagshipid)
        data['needs'] = flagshipOp.show_flagships_example_needs()
        return_data = json.dumps({
            'data': data,
        })
        return tools.flagship_render_template('storeManage/uploadpics.html', data = return_data)

class StoreShowPicAdd(MethodView):
    def post(self):
        return_data = jsonify({ 'code':300 })
        try:
            flagshipid = request.values.get('flagshipid', '')
            state = pub_upload_picture_to_server()
            local_path = state.get('path')
            s, path = pub_upload_picture_to_qiniu(state)
            if not s:
                return_data = jsonify({'code': 112})
            else:
                flagshipOp = flagship_op.FlagShipOp()
                flagshipOp.add_show_picture(flagshipid, path, local_path)
                return_data = jsonify({ 'code':100 })
        except Exception, e:
            print e
        return tools.en_return_data(return_data)

class StoreShowPicEdit(MethodView):
    def post(self):
        return_data = jsonify({ 'code':300 })
        try:
            flagshipid = request.values.get('flagshipid', '')
            show_id = request.values.get('show_id', '')
            state = pub_upload_picture_to_server()
            local_path = state.get('path')
            s, path = pub_upload_picture_to_qiniu(state)
            if not s:
                return_data = jsonify({'code': 112})
            else:
                flagshipOp = flagship_op.FlagShipOp()
                flagshipOp.edit_show_picture(show_id, path, local_path)
                return_data = jsonify({ 'code':100 })
        except Exception, e:
            print e
        return tools.en_return_data(return_data)

class StoreShowPicDel(MethodView):
    def post(self):
        return_data = jsonify({ 'code':300 })
        try:
            show_id = request.values.get('show_id', '')
            flagshipOp = flagship_op.FlagShipOp()
            flagshipOp.delete_example_picture(show_id)

            return_data = jsonify({ 'code':100 })
        except Exception, e:
            print e
        return tools.en_return_data(return_data)


add_url.flagship_add_url(u"门店基本资料", "flagship_manage.FlagshipManageView", add_url.TYPE_ENTRY, flagship_manage_prefix,
                flagship_manage, '/store_info/', 'StoreInfo', StoreInfo.as_view('StoreInfo'),90, methods=['GET','POST'])

add_url.flagship_add_url(u"查看标准示例", "flagship_manage.StoreInfo", add_url.TYPE_FEATURE, flagship_manage_prefix,
                flagship_manage, '/store_example_show/', 'storeexampleshow', ExampleShow.as_view('storeexampleshow'), methods=['GET'])

add_url.flagship_add_url(u"上传店铺展示照片", "flagship_manage.StoreInfo", add_url.TYPE_FEATURE, flagship_manage_prefix,
                flagship_manage, '/store_showpic/', 'storeshowpic', StoreShowPic.as_view('storeshowpic'), methods=['GET'])

add_url.flagship_add_url(u"增加照片", "flagship_manage.storeshowpic", add_url.TYPE_FEATURE, flagship_manage_prefix,
                flagship_manage, '/store_showpic_add/', 'storeshowpicadd', StoreShowPicAdd.as_view('storeshowpicadd'), methods=['POST'])

add_url.flagship_add_url(u"编辑照片", "flagship_manage.storeshowpic", add_url.TYPE_FEATURE, flagship_manage_prefix,
                flagship_manage, '/store_showpic_edit/', 'storeshowpicedit', StoreShowPicEdit.as_view('storeshowpicedit'), methods=['POST'])

add_url.flagship_add_url(u"删除照片", "flagship_manage.storeshowpic", add_url.TYPE_FEATURE, flagship_manage_prefix,
                flagship_manage, '/store_showpic_del/', 'storeshowpicdel', StoreShowPicDel.as_view('storeshowpicdel'), methods=['POST'])

