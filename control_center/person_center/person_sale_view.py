#-*-coding:utf-8-*-
import time
import datetime
import calendar
from flask import session
from flask.views import MethodView
from flask import render_template, current_app, request, url_for
from flask import jsonify
from flask import json
from pprint import pprint

from public.function import tools

from data_mode.user_center.control.mixOp import MixUserCenterOp
from public.upload_download.upload_download import pub_upload_picture_to_server
from public.upload_download.upload_download import pub_upload_picture_to_qiniu
# from control_center.flagship_manage.warehouse_manage.control.mixOp import HolaWareHouse
from control_center.shop_manage.good_info_manage.control.mixOp import HolaWareHouse
from control_center.flagship_manage.flagship_info_manage.control.mixOp import FlagshipOrderInfoOp, FlagshipOrderProductOp
from config.service_config.returncode import ServiceCode

class MySaleRecordIndex(MethodView):

    def get(self):
        # 销售记录首页
        uid = session['user']['id']

        time_str = time.strftime('%Y-%m-%d',time.localtime(time.time()))
        time_strp = time.mktime(time.strptime(time_str,'%Y-%m-%d'))
        weekday = datetime.datetime.now().weekday()
        stime = time_strp - 86400*weekday
        etime = stime + 86400*7 - 1
        oi = FlagshipOrderInfoOp()
        rs = oi.get_personal_sale_records(uid, stime, etime)
        print json.dumps(rs)
        return tools.en_render_template('personal/sale-record.html', data = json.dumps(rs))


class MySaleRecord(MethodView):
    def post(self):
        print request.form
        today = request.form.get('today', 0,int)
        all = request.form.get('all', 0,int)
        seven = request.form.get('seven', 0,int)
        thirty = request.form.get('thirty', 0,int)
        stime = request.form.get('stime', 0,int)
        etime = request.form.get('etime', 0,int)
        page_num = request.form.get('page_num', 0,int)
        per_page_nums = request.form.get('per_page_nums', 0,int)
        if page_num <= 0 and per_page_nums <= 0:
            return json.dumps({'code':ServiceCode.params_error})
        time_str = time.strftime('%Y-%m-%d',time.localtime(time.time()))
        time_strp = time.mktime(time.strptime(time_str,'%Y-%m-%d'))

        uid = session['user']['id']
        oi = FlagshipOrderInfoOp()
        try:
            if today == 1:
                s_time = time_strp
                e_time = time_strp + 86400 - 1
                rs = oi.get_personal_sale_records(uid, s_time, e_time, page_num, per_page_nums)

            if all == 1:
                s_time = 0
                e_time = time_strp + 86400 - 1
                rs = oi.get_personal_sale_records(uid, s_time, e_time, page_num, per_page_nums)

            if seven == 1:
                weekday = datetime.datetime.now().weekday()
                s_time = time_strp - 86400*weekday
                e_time = s_time + 7*86400 - 1
                rs = oi.get_personal_sale_records(uid, s_time, e_time, page_num, per_page_nums)

            if thirty == 1:
                days = calendar.monthrange(time.localtime(time.time()).tm_year,time.localtime(time.time()).tm_mon)

                s_time = int(time.mktime(datetime.date(datetime.date.today().year,datetime.date.today().month,1).timetuple()))
                e_time =s_time + days[1]*86400 - 1
                rs = oi.get_personal_sale_records(uid, stime, e_time,  page_num, per_page_nums)

            if stime >0 and etime>0:
                rs = oi.get_personal_sale_records(uid, stime, etime, page_num, per_page_nums)

            return json.dumps({'code':ServiceCode.success,'data': rs})
        except Exception,e:
            print e
            return json.dumps({'code':ServiceCode.service_exception})

class MySaleRecordDetail(MethodView):
    def get(self):
        # 订单详情

        oi = FlagshipOrderInfoOp()
        order_id = request.args.get('order_id', 0, int)
        rs = oi.get_personal_sale_record_details(order_id)

        return tools.en_render_template('personal/sale-record-detail.html', data = json.dumps(rs))

class PrintSaleRecord(MethodView):
    def get(self):

        oi = FlagshipOrderInfoOp()
        order_id = request.args.get('order_id', 0, int)
        rs = oi.get_personal_sale_record_details(order_id)

        return json.dumps(rs)

class SalePercentage(MethodView):
    def get(self):
        return tools.en_render_template('personal/discount-amount.html')

class SalePricingData(MethodView):
    def get(self):
        return_data = jsonify({ 'code':300 })
        try:
            page = request.args.get('page', 1, type=int)
            per_page = request.args.get('per_page', 20, type=int)
            sou = request.values.get('sou', '')
            from control_center.shop_manage.good_info_manage.control.mixOp import Dict_Categorgory_touyingyi
            # from data_mode.hola_warehouse.control.mixOp import Dict_Categorgory_touyingyi
            category_id = request.args.get('category_id',  0)
            page = page - 1
            if per_page > 60:
                per_page = 60
            HolaWareHouse_op = HolaWareHouse()
            start = page * per_page
            data, total = HolaWareHouse_op.get_products_detail_info_by_category(category_id, start, per_page, sou)
            return_data = jsonify({ 'code':100,
                                  'products': data,
                                  'total': total
                                    })
        except Exception, e:
            print e
        return tools.en_return_data(return_data)


from . import personal, personal_prefix
from control_center.admin import add_url


# add_url.add_url(u"我的销售首页", "personal.personal", add_url.TYPE_ENTRY, personal_prefix,
#                 personal, '/sale_record_index/', 'MySaleRecordIndex', MySaleRecordIndex.as_view('MySaleRecordIndex'), methods=['GET'])


# add_url.add_url(u"查看我的销售", "personal.MySaleRecordIndex", add_url.TYPE_FEATURE, personal_prefix,
#                 personal, '/sale_record/', 'MySaleRecord', MySaleRecord.as_view('MySaleRecord'), methods=['POST'])
#
# add_url.add_url(u"我的销售详情", "personal.MySaleRecord", add_url.TYPE_FEATURE, personal_prefix,
#                 personal, '/sale_record_detail/', 'MySaleRecordDetail', MySaleRecordDetail.as_view('MySaleRecordDetail'), methods=['GET'])
#
# add_url.add_url(u"销售信息打印", "personal.MySaleRecord", add_url.TYPE_FEATURE, personal_prefix,
#                 personal, '/print_sale_record/', 'PrintSaleRecord', PrintSaleRecord.as_view('PrintSaleRecord'), methods=['GET'])
#
# add_url.add_url(u"我的折扣页面", "personal.MySaleRecordIndex", add_url.TYPE_FEATURE, personal_prefix,
#                 personal, '/sale_percentage/', 'SalePercentage', SalePercentage.as_view('SalePercentage'), methods=['GET'])
#
# add_url.add_url(u"我的折扣数据", "personal.SalePercentage", add_url.TYPE_FEATURE, personal_prefix,
#                 personal, '/SalePricingData/', 'SalePricingData', SalePricingData.as_view('SalePricingData'), methods=['GET'])
