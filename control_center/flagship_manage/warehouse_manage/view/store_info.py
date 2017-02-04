# # coding:utf8
#
# import json
#
# from flask.views import MethodView
# from flask import current_app, request, url_for, session, jsonify
#
# from public.function import tools
# from control_center.departments.flagship.control.mixOp import FlagShipOp,ClerkOp
# from public.upload_download.upload_download import pub_upload_picture_to_server
# from public.upload_download.upload_download import pub_upload_picture_to_qiniu
#
# class StoreManage(MethodView):
#     # 店铺管理
#
#     def get(self):
#         # store_daily/store_admin/StoreManage
#         return tools.flagship_render_template('storeManage/StoreManage.html')
#
#
# class StoreInfo(MethodView):
#     # 门店基本资料
#     '''
#     '''
#     def get(self):
#         store_id = request.args.get('flagshipid', 1,int)
#         fs = FlagShipOp()
#         result = fs.get_flagship_info(store_id)
#         from control_center.flagship_manage.flagship_info_manage.control import flagship_op
#         op = flagship_op.FlagShipOp()
#         statu, picture = op.get_flagship_checkstatu(store_id)
#         result['check_statu'] = statu
#         result['picture'] = picture
#         return tools.flagship_render_template('storeManage/StoreInfo.html', result = json.dumps(result))
#
#     def post(self):
#         # :param fs_id: 旗舰店id
#         # :param telephone: 服务电话
#         # :param leader_telephone: 店长电话
#         print request.form
#
#         fs_id = request.form.get("fs_id", int)
#         telephone =  request.form.get("telephone",'',str)
#         leader_telephone =  request.form.get("leader_telephone", '', str)
#         fs = FlagShipOp()
#         rs = fs.save_flagship_info(fs_id, telephone, leader_telephone)
#         return rs
#
# class ExampleShow(MethodView):
#     def get(self):
#         from control_center.flagship_manage.flagship_info_manage.control.flagship_op import FlagShipOp
#         # from control_center.departments.flagship.control.flagship_op import FlagShipOp
#         flagship_op = FlagShipOp()
#         data = flagship_op.show_flagships_example_pictures()
#         return_data = json.dumps({
#             'data': data,
#         })
#         return tools.flagship_render_template('storeManage/showdemopics.html', data = return_data)
#
# class StoreShowPic(MethodView):
#     def get(self):
#         from control_center.flagship_manage.flagship_info_manage.control.flagship_op import FlagShipOp
#         # from control_center.departments.flagship.control.flagship_op import FlagShipOp
#         flagship_op = FlagShipOp()
#         flagshipid = request.values.get('flagshipid', '')
#         data = flagship_op.show_flagships_pictures(flagshipid)
#         data['needs'] = flagship_op.show_flagships_example_needs()
#         return_data = json.dumps({
#             'data': data,
#         })
#         return tools.flagship_render_template('storeManage/uploadpics.html', data = return_data)
#
# class StoreShowPicAdd(MethodView):
#     def post(self):
#         from control_center.flagship_manage.flagship_info_manage.control.flagship_op import FlagShipOp
#         # from control_center.departments.flagship.control.flagship_op import FlagShipOp
#         return_data = jsonify({ 'code':300 })
#         try:
#             flagshipid = request.values.get('flagshipid', '')
#             state = pub_upload_picture_to_server()
#             local_path = state.get('path')
#             s, path = pub_upload_picture_to_qiniu(state)
#             if not s:
#                 return_data = jsonify({'code': 112})
#             else:
#                 flagship_op = FlagShipOp()
#                 flagship_op.add_show_picture(flagshipid, path, local_path)
#                 return_data = jsonify({ 'code':100 })
#         except Exception, e:
#             print e
#         return tools.en_return_data(return_data)
#
# class StoreShowPicEdit(MethodView):
#     def post(self):
#         # from control_center.departments.flagship.control.flagship_op import FlagShipOp
#         from control_center.flagship_manage.flagship_info_manage.control.flagship_op import FlagShipOp
#         return_data = jsonify({ 'code':300 })
#         try:
#             flagshipid = request.values.get('flagshipid', '')
#             show_id = request.values.get('show_id', '')
#             state = pub_upload_picture_to_server()
#             local_path = state.get('path')
#             s, path = pub_upload_picture_to_qiniu(state)
#             if not s:
#                 return_data = jsonify({'code': 112})
#             else:
#                 flagship_op = FlagShipOp()
#                 flagship_op.edit_show_picture(show_id, path, local_path)
#                 return_data = jsonify({ 'code':100 })
#         except Exception, e:
#             print e
#         return tools.en_return_data(return_data)
#
# class StoreShowPicDel(MethodView):
#     def post(self):
#         # from control_center.departments.flagship.control.flagship_op import FlagShipOp
#         from control_center.flagship_manage.flagship_info_manage.control.flagship_op import FlagShipOp
#         return_data = jsonify({ 'code':300 })
#         try:
#             show_id = request.values.get('show_id', '')
#             flagship_op = FlagShipOp()
#             flagship_op.delete_example_picture(show_id)
#
#             return_data = jsonify({ 'code':100 })
#         except Exception, e:
#             print e
#         return tools.en_return_data(return_data)
#
