#-*-coding:utf-8-*-

from flask import session
from flask.views import MethodView
from flask import render_template, current_app, request, url_for
from flask import jsonify
from flask import json
from pprint import pprint
import json

from public.function import tools

from data_mode.user_center.control.mixOp import MixUserCenterOp
from public.upload_download.upload_download import pub_upload_picture_to_server
from public.upload_download.upload_download import pub_upload_picture_to_qiniu



class PersonalInfoView(MethodView):
    def get(self):
        op = MixUserCenterOp()
        uid = session['user']['id']
        data = op.get_user_add_info(uid)

        return_data = json.dumps({
                              'data': data
                                })
        return tools.en_render_template('personal/personbasic.html', data=return_data)


class PersonalInfoEdit(MethodView):
    def post(self):
        return_data = jsonify({ 'code':300 })
        try:
            telephone = request.values.get('telephone', 0)
            nickname = request.values.get('nickname', 0)
            uid = session['user']['id']
            op = MixUserCenterOp()
            re = op.modify_user_telephone_nickname(uid, telephone, nickname)
            if re:
                #session['user']['nickname'] = nickname
                user = session['user']
                user['nickname'] = nickname
                session['user'] = user
                #pprint(session['user'])
                return_data = jsonify({ 'code':100 })
            else:
                return_data = jsonify({ 'code':109 })
        except Exception, e:
            print e
        return tools.en_return_data(return_data)

class UpLoadAvatar(MethodView):
    def post(self):
        return_data = jsonify({ 'code':300 })
        try:
            state = pub_upload_picture_to_server()
            # local_path = state.get('path')
            s, path = pub_upload_picture_to_qiniu(state)
            if not s:
                return_data = jsonify({'code': 112})
            else:
                uid = session['user']['id']
                op = MixUserCenterOp()
                op.add_avatar(uid, path)
                user = session['user']
                user['avatar'] = path
                session['user'] = user
                return_data = jsonify({ 'code':100,
                                        'pic': path})
        except Exception, e:
            print e
        return tools.en_return_data(return_data)


from . import personal, personal_prefix
from control_center.admin import add_url

add_url.add_url(u"基本资料", "personal.personal", add_url.TYPE_ENTRY, personal_prefix,
                personal, '/info/', 'info', PersonalInfoView.as_view('info'), methods=['GET'])

add_url.add_url(u"个人信息编辑", "personal.personal", add_url.TYPE_FEATURE, personal_prefix,
                personal, '/info_edit/', 'infoedit', PersonalInfoEdit.as_view('infoedit'), methods=['POST'])

add_url.add_url(u"个人图形上传", "personal.personal", add_url.TYPE_FEATURE, personal_prefix,
                personal, '/up_avatar/', 'upavatar', UpLoadAvatar.as_view('upavatar'), methods=['POST'])

