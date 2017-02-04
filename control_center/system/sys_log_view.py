#-*-coding:utf-8-*-


from datetime import datetime
from flask.views import MethodView
from flask import render_template, current_app, request, url_for
from flask import jsonify, session
from public.function import tools
from data_mode.user_center.control.mixOp import MixUserCenterOp





from sqlalchemy import func

from sqlalchemy import or_, not_
from sqlalchemy.exc import IntegrityError
import traceback
import json


class SyslogView(MethodView):
    def get(self):
        user_op = MixUserCenterOp()
        return_data = json.dumps({
                              'moudle': user_op.get_log_moudle()
                                })

        return_data_test = jsonify({
            'moudle': user_op.get_log_moudle()
        })
        return tools.en_render_template('system/operationlog.html', data=return_data)

class SyslogData(MethodView):
    def get(self):
        hehe = request.values
        user_op = MixUserCenterOp()
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        name = request.values.get('name', '')
        date_start = request.values.get('date_start', '')
        if not len(date_start):
            date_start = '2000-01-01 00:00:00'
        date_end = request.values.get('date_end', '')
        if not len(date_end):
            date_end = '2020-01-01 00:00:00'
        moudle_id = request.values.get('moudle_id', '')
        date_start = datetime.strptime(date_start, "%Y-%m-%d %H:%M:%S").date()
        date_end = datetime.strptime(date_end, "%Y-%m-%d %H:%M:%S").date()

        page = page - 1
        if per_page > 60:
            per_page = 60

        start = page * per_page
        data, total = user_op.get_log_info(start, per_page, name, date_start, date_end, moudle_id)
        return_data = jsonify({ 'code':100,
                              'data': data,
                              'total': total
                                })
        return tools.en_return_data(return_data)


from . import sys, sys_prefix
from control_center.admin import add_url

add_url.add_url(u"日志页面", 'sys.set', add_url.TYPE_ENTRY, sys_prefix,
                sys, '/log/', 'log', SyslogView.as_view('log'), methods=['GET'])

add_url.add_url(u"日志数据", 'sys.set', add_url.TYPE_FEATURE, sys_prefix,
                sys, '/log_data/', 'logdata', SyslogData.as_view('logdata'), methods=['GET'])