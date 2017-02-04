#-*-coding:utf-8-*-


from flask.views import MethodView
from flask import  current_app, request, url_for, session

from flask import jsonify
from public.function import tools

from sqlalchemy import or_, not_
import traceback
from auth_code import ImageChar
from io import BytesIO
import time, json
import os

#from data_mode.user_center.model.admin_user import AdminUser
#from data_mode.user_center.model.admin_url import AdminUrl
from public.logger.syslog import SystemLog
from public.exception.custom_exception import CodeError

from data_mode.user_center.model.admin_user import AdminUser
from data_mode.user_center.model.admin_url import AdminUrl
from redis_cache.admin_cache.base import AdminRedisOp, KeysList


class LoginView(MethodView):
    def get(self):
        try:
            if 'logged_in' in session:
                session.pop('logged_in', None)
            # if 'user' in session:
            #     session.pop('user', None)
            # if 'url_maps' in session:
            #     session.pop('url_maps', None)
            return tools.en_render_template('main/login.html')
        except Exception, e:
            print traceback.format_exc()
            print e
        return tools.en_render_template('main/login.html')

    def post(self):
        return_data = jsonify({ 'code':300 })
        try:
            username = request.values.get('username', '')
            password = request.values.get('password', '')
            authcode = request.values.get('authcode', '')
            from data_mode.user_center.control.mixOp import MixUserCenterOp
            db_seesion = MixUserCenterOp().get_seesion()

            loacl_authcode = session['authcode']
            print "get was created code:", loacl_authcode
            print "get request code:", authcode
            if loacl_authcode.lower() != str(authcode).lower():
                raise ValueError("authcode is error", 112)

            user = db_seesion.query(AdminUser).filter(AdminUser.username == username).first()
            mtpwd= user.verify_password(password)

            if user is not None and user.verify_password(password):

                userinfo = {}
                userinfo['id'] = user.id
                userinfo['name'] = user.name
                userinfo['username'] = user.username
                userinfo['nickname'] = user.name
                userinfo['work_number'] = user.work_number
                if user.nickname is not None and len(user.nickname):
                    userinfo['nickname'] = user.nickname
                user_add_info = user.info
                if user_add_info is not None and user_add_info.avatar is not None and len(user_add_info.avatar):
                    userinfo['avatar'] = user_add_info.avatar
                else:
                    userinfo['avatar'] = ""
                userinfo['is_superuser'] = user.is_superuser
                userinfo['groups'] = []
                url_maps = {}
                # urls = db_seesion.query(AdminUrl).filter( not_(AdminUrl.type == add_url.TYPE_FUNC)).all()
                urls = db_seesion.query(AdminUrl).all()
                for i_url in urls:
                    if user.is_superuser:
                        url_maps[i_url.url] = 1
                    else:
                        url_maps[i_url.url] = 0

                # print "user.groups:", user.groups
                for group in user.groups:
                    userinfo['groups'].append(group.id)
                    for i_url in group.urls:
                        # print 'i_url:',i_url.url
                        url_maps[i_url.url] = 1
                # del request.session['']
                session['user'] = userinfo
                session['logged_in'] = True
                session['url_maps'] = url_maps
                # print '哈哈',len(url_maps),'==',url_maps
                # print
                admin_redis_op = AdminRedisOp()
                admin_redis_op.set_admin_url(k=KeysList.AdminUrlMaps, val=url_maps)

                # m_urls = db_seesion.query(AdminUrl).filter( not_(AdminUrl.endpoint == 'main.index'), AdminUrl.type==add_url.TYPE_ENTRY ).all()
                # permission_urls = session['url_maps']
                #
                # nav_url = []
                # for iurl in m_urls:
                #     if permission_urls[iurl.url]:
                #         nav_url.append(iurl.to_json())
                # session['nav_url'] = nav_url
                return_data = jsonify({
                    'code': 100,
                    'url': url_for('personal.personal')
                })

            else:
                raise ValueError("username or password is error", 107)
        except Exception, e:
            print e
            return_data = jsonify({'code': e[1]})
        finally:
            return tools.en_return_data(return_data)


class AuthLogoutView(MethodView):
    def get(self):
        try:
            session.pop('logged_in', None)
            session.pop('user', None)
            session.pop('url_maps', None)
        except Exception, e:
            print e
        return tools.en_render_template('main/login.html')

    def post(self):
        try:
            session.pop('logged_in', None)
            user = session.pop('user', None)
            session.pop('url_maps', None)
            if user is not None:
                username = user['username']
            else:
                raise CodeError(101, u'无相关用户名')
        except CodeError as e:
            return tools.en_return_data(jsonify(e.json_value()))
        else:
            return tools.en_return_data(jsonify({'username': username}))


class AuthCodeView(MethodView):
    def get(self):
        buf_str = ''
        try:
            img = ImageChar()
            authcode, image = img.randChar(4, 'alphabet')
            session['authcode'] = authcode
            print "create authcode:", authcode
            session['code_time'] = time.localtime(time.time()).tm_min
            o = BytesIO()
            image.save(o, 'PNG')
            buf_str = o.getvalue()
        except Exception, e:
            print e
        return buf_str,  200, {'Content-Type': 'image/PNG' }


class OverTimeLogin(MethodView):
    def post(self):
        return_data = jsonify({ 'code':300 })
        try:
            username = request.values.get('username', '')
            password = request.values.get('password', '')
            from data_mode.user_center.control.mixOp import MixUserCenterOp
            db_seesion = MixUserCenterOp().get_seesion()

            user = db_seesion.query(AdminUser).filter(AdminUser.username == username).first()
            mtpwd= user.verify_password(password)

            if user is not None and user.verify_password(password):

                userinfo = {}
                userinfo['id'] = user.id
                userinfo['name'] = user.name
                userinfo['username'] = user.username
                userinfo['nickname'] = user.name
                userinfo['work_number'] = user.work_number
                if user.nickname is not None and len(user.nickname):
                    userinfo['nickname'] = user.nickname
                user_add_info = user.info
                if user_add_info is not None and user_add_info.avatar is not None and len(user_add_info.avatar):
                    userinfo['avatar'] = user_add_info.avatar
                else:
                    userinfo['avatar'] = ""
                userinfo['is_superuser'] = user.is_superuser
                userinfo['groups'] = []
                url_maps = {}
                urls = db_seesion.query(AdminUrl).filter( not_(AdminUrl.type == add_url.TYPE_FUNC)).all()
                for i_url in urls:
                    if user.is_superuser:
                        url_maps[i_url.url] = 1
                    else:
                        url_maps[i_url.url] = 0

                for group in user.groups:
                    userinfo['groups'].append(group.id)
                    for i_url in group.urls:
                        url_maps[i_url.url] = 1
                session['user'] = userinfo
                session['logged_in'] = True
                session['url_maps'] = url_maps
                admin_redis_op = AdminRedisOp()
                admin_redis_op.set_admin_url(k=KeysList.AdminUrlMaps, val=url_maps)
                return_data = jsonify({
                    'code': 100
                })
            else:
                raise CodeError(107, u"输入密码错误")
        except CodeError as e:
            return_data = jsonify(e.json_value())
        # except Exception, e:
        #     print e
        #     return_data = jsonify({'code': e[1]})
        finally:
            return tools.en_return_data(return_data)


class OverTimeLogout(MethodView):
    def post(self):
        try:
            session.pop('logged_in',None)
            user = session.pop('user',None)
            session.pop('url_maps', None)
            if user is not None:
                username = user['username']
            else:
                raise CodeError(101, u'无相关用户名')
        except CodeError as e:
            return tools.en_return_data(jsonify(e.json_value()))
        else:
            return tools.en_return_data(jsonify({'username': username, 'code': 100}))

from control_center.admin import add_url
from . import auth, auth_prefix

auth.add_url_rule('/login/', 'login', LoginView.as_view('login'), methods=['GET', 'POST'])

auth.add_url_rule('/authcode/', 'authcode', AuthCodeView.as_view('authcode'), methods=['GET', 'POST'])

auth.add_url_rule('/logout/', 'logout', AuthLogoutView.as_view('logout'), methods=['GET', 'POST'])

auth.add_url_rule('/overtime_login/', 'overtimelogin', OverTimeLogin.as_view('overtimelogin'), methods=['POST'])

auth.add_url_rule('/overtime_logout/', 'overtimelogout', OverTimeLogout.as_view('overtimelogout'), methods=['POST'])
