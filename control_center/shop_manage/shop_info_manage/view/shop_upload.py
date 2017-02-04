#!/usr/bin/python
#-*- coding:utf-8 -*-
#    Copyright(c) 2015-2016 JmGo Company
#    All rights reserved.
#
#    文件名 : shop_upload.py
#    作者   : WangYi
#  电子邮箱 : ywang@jmgo.com
#    日期   : 2016/9/18 8:38
#
#     描述  : 用于店铺通用的上传文件接口
#
import os
from flask.views import MethodView
from flask import json, jsonify
from public.function import  tools
from data_mode.erp_base.control.uploadOp import UploadOp, UploadConfig
from public.exception.custom_exception import CodeError
from config.service_config.returncode import ServiceCode
import traceback
from control_center.shop_manage import shop_manage_base


class UploadFile(MethodView):
    """
    店铺管理通用上传文件接口。
    """
    def post(self):
        return_data = None
        try:
            upload_op = UploadOp()
            state, msg = upload_op.upload(upload_op.FILE, os.path.join(
                    UploadConfig.SERVER_ERP_FIle, shop_manage_base))
            if state != 0:
                print("Upload Fail:",msg)
                raise CodeError(ServiceCode.update_error, u'上传文件失败')
            else:
                result = msg['qiniu_addr']
        except CodeError as e:
            return_data = jsonify(e.json_value())
        except Exception as e:
            print traceback.format_exc()
            return_data = jsonify(
                {'code': ServiceCode.service_exception, 'msg': u"服务器失败"})
        else:
            return_data = jsonify({'code': ServiceCode.success, 'pic':result})
        finally:
            return tools.en_return_data(return_data)


class UploadImage(MethodView):
    """
    店铺管理通用上传图片接口
    """
    def post(self):
        return_data = None
        try:
            upload_op = UploadOp()
            state, msg = upload_op.upload(upload_op.IMAGE, os.path.join(
                    UploadConfig.SERVER_ERP_IMG, shop_manage_base))
            if state != 0:
                # print("Upload Fail:",msg)
                raise CodeError(ServiceCode.update_error, u'上传文件失败')
            else:
                result = msg['qiniu_addr']
        except CodeError as e:
            return_data = jsonify(e.json_value())
        except Exception as e:
            print traceback.format_exc()
            return_data = jsonify(
                {'code': ServiceCode.service_exception, 'msg': u"服务器失败"})
        else:
            return_data = jsonify({'code': ServiceCode.success, 'pic':result})
        finally:
            return tools.en_return_data(return_data)


from control_center.admin import add_url
from control_center.shop_manage import shop_manage, shop_manage_prefix

add_url.add_url(
    u"店铺管理上传文件",
    "shop_manage.ShopManageView",
     add_url.TYPE_FUNC,
    shop_manage_prefix,
    shop_manage,
    '/upload_file/',
    'upload_file',
    UploadFile.as_view('upload_file'),
    methods=['POST']
)

add_url.add_url(
    u"店铺管理上传图片",
    "shop_manage.ShopManageView",
     add_url.TYPE_FUNC,
    shop_manage_prefix,
    shop_manage,
    '/upload_image/',
    'upload_image',
    UploadImage.as_view('upload_image'),
    methods=['POST']
)