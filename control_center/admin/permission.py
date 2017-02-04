#-*-coding:utf-8 -*-
from flask import  redirect, request, url_for, flash, current_app, session

from data_mode.user_center.model.admin_group import AdminGroup
from data_mode.user_center.model.admin_url import AdminUrl, get_father_father
from data_mode.user_center.model.admin_log import AdminLog
from data_mode.user_center.control.mixOp import MixUserCenterOp
from sqlalchemy import or_, not_
from control_center.admin import add_url
from config.web_prefix.web_prefix_config import WebPrefixConfig
from flask import json
from redis_cache.admin_cache.base import AdminRedisOp, KeysList
import auth_view

def rep(s):
    if s[len(s) - 1] == '/':
        s = s[0:len(s) - 1]
    return s

def get_url_maps():
    admin_redis_op = AdminRedisOp()
    permission_urls = admin_redis_op.get_admin_url(KeysList.AdminUrlMaps)
    # return eval(permission_urls)
    return json.loads(permission_urls)

def inject_info():
    # 用于渲染模板时，提供静态文件前缀
    web_prefix = WebPrefixConfig().PREFIX
    if ('user' not in session or 'url_maps' not in session ):
        return dict(web_prefix=web_prefix)
    else:
        # print("1"*80)
        from data_mode.user_center.control.mixOp import MixUserCenterOp
        from control_center.flagship_manage.warehouse_manage.control.ship_in_warehouse_op import ShipInwarehouse
        store_all = ShipInwarehouse().GetStoreAll()
        db_seesion = MixUserCenterOp().get_seesion()

        m_urls = db_seesion.query(AdminUrl).filter(not_(AdminUrl.endpoint == 'main.index'),
                                                   AdminUrl.type==add_url.TYPE_ENTRY ).order_by(AdminUrl.priority.desc()).all()
        permission_urls = get_url_maps()

        flagship_id = request.values.get('flagshipid', None)
        storeName = ''
        # print("2"*80)
        if flagship_id is not None:
            for itme in store_all:
                if str(flagship_id) == str(itme['id']):
                    storeName = itme['name']

        nav_url = []
        # print("3"*80)
        for iurl in m_urls:
            # if permission_urls[iurl.url]:
            if permission_urls.get(iurl.url, None):
                nav_url.append(iurl.to_json())
        # print("4"*80)
        # print(json.dumps(nav_url))
        # print("type(nav_url):", type(nav_url))
        # print("type(json.jsonify(nav_url))", type(json.dumps(nav_url)))
        # print '导航List',json.dumps(session['url_maps'])
        # print '导航',json.dumps(nav_url)
        # print '地址栏=',session['url_maps']
        new_dict = {}
        for key, item in get_url_maps().items():
            new_dict[key.encode()] = item
        # print '结果=', new_dict
        return dict(user=session['user'], url_maps=new_dict, nav_url=json.dumps(nav_url),storeNmae=storeName,storeAll=json.dumps(store_all), web_prefix=web_prefix)

from flask import helpers


def call_before_request():
    # print "path: ", request.path
    path = request.path
    path_no_flagship = path

    index = path.find('/static/')

    let_go_url_map = {
        url_for('auth.login') : 1,
        url_for('auth.authcode') : 1,
        url_for('auth.overtimelogin') : 1,
        url_for('auth.overtimelogout'): 1,
        url_for('main.notice_alarm_count') : 1,
        url_for('main.alarm') : 1,
        url_for('main.notice_new') : 1,
        url_for('main.notice_new_detail') : 1,
        url_for('main.notice_new_data') : 1,
        url_for('main.notice_new_delete') : 1,
        url_for('main.notice_new_update_flag') : 1,
        url_for('main.notice_new_update_read') : 1,
        "/favicon.ico" : 1,
    }
    if (index != -1):
        res_path = path[index:]
        return get_resource(res_path)

    if let_go_url_map.has_key(path):
        return

    # print("5"*80)
    user_op = MixUserCenterOp()
    db_seesion = user_op.get_seesion()
    values = request.values

    flagshipid = values.get('flagshipid', '')
    in_url = None
    if len(flagshipid):
        # print("*"*80)
        flagshipid_url = "?flagshipid=%s" % flagshipid
        path = path+flagshipid_url
        in_url = db_seesion.query(AdminUrl).filter(AdminUrl.url==path).first()
        if in_url is None:
            in_url = db_seesion.query(AdminUrl).filter(AdminUrl.url==path_no_flagship).first()
            if in_url is not None:
                path = path_no_flagship
    else:
        # print("@"*80)
        in_url = db_seesion.query(AdminUrl).filter(AdminUrl.url==path).first()

    # flagshipid = None
    # if in_url is not None and in_url.type == 2:
    #     flagshipid =
    #
    # if flagshipid is not None:
    #     flagshipid_url = "?flagshipid=%s" % flagshipid
    #     path = path+flagshipid_url
    #     in_url = db_seesion.query(AdminUrl).filter(AdminUrl.url==path).first()

    if 'logged_in' not in session:
        # print('6'*80)
        return redirect(url_for('auth.login'))


    if 1:
        # print('7'*80)
        user_id = 0
        account = "匿名"
        if session.has_key('user'):
            user_id = session['user']['id']
            account = session['user']['name'] + "(" + session['user']['username'] + ")"
        url_mode = db_seesion.query(AdminUrl).filter(AdminUrl.url==path).first()
        test = request
        address_str = request.environ['REMOTE_ADDR']
        if url_mode is not None:
            url_father = get_father_father(url_mode)
            operate_module = url_father.name
            describe = url_mode.name
            data = {}
            # print('8'*80)
            for (d,x) in values.items():
                data[d] = x
            jdata = json.dumps(data)
            describe = describe + "||" + jdata
            log = AdminLog(url_path = path, user_id=user_id, ip_address=address_str, account=account,
                           operate_module=operate_module, describe=describe, operate_module_id=url_father.id)
            db_seesion.add(log)
            db_seesion.commit()

    if 1:
        # print('9'*80)
        if in_url is None:
            # print('8'*80)
            return redirect(url_for('auth.login'))

        if in_url.type == 2:
            if in_url.parent is not None:
                path = in_url.parent.url
            else:
                # print('3' * 80)
                return redirect(url_for('auth.login'))
        # url_map = get_url_maps()
        if not get_url_maps().has_key(path):
            # print('4' * 80)
            return redirect(url_for('auth.login'))
        else:
            if get_url_maps()[path] == 1:
                return
            else:
                # print("session['url_maps']:", session['url_maps'])
                # print("path:", path)
                # print("session['url_maps'][path]:", session['url_maps'][path])
                # print('5' * 80)
                return redirect(url_for('auth.login'))
    return

from control_center.create_app import root_dir, get_file
import os
from flask import Response


def get_resource(path):  # pragma: no cover
    # mimetypes = {
    #     ".css": "text/css",
    #     ".html": "text/html",
    #     ".js": "application/javascript",
    #     '.png': "application/x-png"
    # }
    root_path = root_dir()
    complete_path = None
    if 0:
        complete_path = os.path.join(root_path, path)
    else:
        complete_path = root_path+path
    return helpers.send_file(complete_path, conditional=True, add_etags=True)
    #return helpers.send_file(complete_path, add_etags=True)
    # ext = os.path.splitext(path)[1]
    # mimetype = mimetypes.get(ext, "text/html")
    # content = get_file(complete_path)
    # if ext == ".png":
    #     return Response(content, mimetype=mimetype)
    # else:
    #     return Response(content, mimetype=mimetype)

