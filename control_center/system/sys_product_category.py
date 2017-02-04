#-*-coding:utf-8-*-

from flask import jsonify, session
from flask import request
from flask.views import MethodView
from public.function import tools
from public.upload_download.upload_download import pub_upload_picture_to_qiniu
from public.upload_download.upload_download import pub_upload_picture_to_server

from control_center.shop_manage.good_info_manage.control.mixOp import HolaWareHouse


class ProductView(MethodView):
    def get(self):
        return tools.en_render_template('system/commoditytype.html')

class AllProductData(MethodView):
    def get(self):
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        sou = request.values.get('sou', "")
        page = page - 1
        if page < 0:
            page = 0
        if per_page > 60:
            per_page = 60
        HolaWareHouse_op = HolaWareHouse()
        start = page * per_page
        data, total = HolaWareHouse_op.show_all_product_not_filter_putway(start, per_page, sou)
        return_data = jsonify({ 'code':100,
                              'products':data,
                              'total': total
                                })
        return tools.en_return_data(return_data)

class AllCategoryData(MethodView):
    def get(self):
        HolaWareHouse_op = HolaWareHouse()
        return_data = jsonify({ 'code':100,
                              'products': HolaWareHouse_op.show_all_category()
                                })
        return tools.en_return_data(return_data)

class ProductCategoryAdd(MethodView):
    def post(self):
        return_data = jsonify({ 'code':300 })
        try:
            name = request.values.get('name', "")
            parent_id = request.values.get('parent_id', 0)
            parent_id = int(parent_id)
            if len(name):
                HolaWareHouse_op = HolaWareHouse()
                re = HolaWareHouse_op.add_category(parent_id, name)
                if re:
                    return_data = jsonify({ 'code':100 })
                else:
                    return_data = jsonify({ 'code':109 })
        except Exception, e:
            print e
        return tools.en_return_data(return_data)

class ProductCategoryRename(MethodView):
    def post(self):
        return_data = jsonify({ 'code':300 })
        try:
            category_id = request.values.get('category_id', 0)
            name = request.values.get('name', "")
            if len(name):
                HolaWareHouse_op = HolaWareHouse()
                re = HolaWareHouse_op.category_rename(category_id, name)
                if re:
                    return_data = jsonify({ 'code':100 })
                else:
                    return_data = jsonify({ 'code':109 })
        except Exception, e:
            print e
        return tools.en_return_data(return_data)


class ProductCategoryDelete(MethodView):
    def post(self):
        return_data = jsonify({ 'code':300 })
        try:
            category_id = request.values.get('category_id', 0)

            HolaWareHouse_op = HolaWareHouse()
            re = HolaWareHouse_op.delete_category(category_id)
            if re:
                return_data = jsonify({ 'code':100 })
            else:
                return_data = jsonify({ 'code':111 })
        except Exception, e:
            print e
        return tools.en_return_data(return_data)

class ProductShow(MethodView):
    def post(self):
        product_id = request.values.get('product_id', 0)
        HolaWareHouse_op = HolaWareHouse()
        return_data = jsonify({
            'code': 100,
            'data': HolaWareHouse_op.show_product(product_id)
            })
        return tools.en_return_data(return_data)

class ProductAdd(MethodView):
    def post(self):
        return_data = jsonify({ 'code':300 })
        try:
            product = {}
            category_id = request.values.get('category_id', 0)
            product['name'] = request.values.get('name', '')
            product['code'] = request.values.get('code', '')
            product['specification'] = request.values.get('specification', '')
            product['measure'] = request.values.get('measure', '')
            product['remark'] = request.values.get('remark', '')
            path = None
            local_path = None
            s = None
            print "ProductAdd, product_upload_file"
            if session.has_key('product_upload_file'):
                print "ProductAdd, session, product_upload_file"
                state = session['product_upload_file']
                local_path = state.get('path')
                s, path = pub_upload_picture_to_qiniu(state)
            product['local_img'] = local_path
            product['img'] = path
            print "product['local_img'] = ", product['local_img']
            print "product['img'] = ", product['img']
            HolaWareHouse_op = HolaWareHouse()
            re = HolaWareHouse_op.add_product(category_id=category_id, product=product)

            if re:
                if s is None:
                    return_data = jsonify({ 'code':100 })
                elif s :
                    return_data = jsonify({ 'code':100 })
                else:
                    return_data = jsonify({ 'code':112 })
            else:
                return_data = jsonify({ 'code':109 })

        except Exception, e:
            print e
        if session.has_key('product_upload_file'):
            session.pop('product_upload_file')
        return tools.en_return_data(return_data)


class ProductPicAdd(MethodView):
    def post(self):
        return_data = jsonify({ 'code':300 })
        try:
            state = pub_upload_picture_to_server()
            if state:
                print "ProductPicAdd state =", state
                session['product_upload_file'] = state
                return_data = jsonify({ 'code':100 })
            else:
                return_data = jsonify({ 'code':112 })
        except Exception, e:
            print e
        return tools.en_return_data(return_data)

class ProductPicDel(MethodView):
    def post(self):
        return_data = jsonify({ 'code':300 })
        try:
            if session.has_key('product_upload_file'):
                session.pop('product_upload_file')
            return_data = jsonify({ 'code':100 })
        except Exception, e:
            print e
        return tools.en_return_data(return_data)


class ProductEdit(MethodView):
    def post(self):
        return_data = jsonify({ 'code':300 })
        try:
            product = {}
            product['id'] = request.values.get('product_id', 0)
            product['category_id'] = request.values.get('category_id', 0)
            product['name'] = request.values.get('name', 0)
            product['code'] = request.values.get('code', 0)
            product['specification'] = request.values.get('specification', 0)
            product['measure'] = request.values.get('measure', 0)
            product['remark'] = request.values.get('remark', 0)
            path = None
            local_path = None
            s = None
            print "ProductEdit, product_upload_file"
            if session.has_key('product_upload_file'):
                print "ProductEdit, session, product_upload_file"
                state = session['product_upload_file']
                local_path = state.get('path')
                s, path = pub_upload_picture_to_qiniu(state)

            product['img'] = path
            product['local_img'] = local_path
            print "product['local_img'] = ", product['local_img']
            print "product['img'] = ", product['img']
            HolaWareHouse_op = HolaWareHouse()
            re = HolaWareHouse_op.Edit_product(product)
            if re:
                if s is None:
                    return_data = jsonify({ 'code':112 })
                else:
                    return_data = jsonify({ 'code':100 })
            else:
                return_data = jsonify({ 'code':109 })

        except Exception, e:
            print e
        if session.has_key('product_upload_file'):
            session.pop('product_upload_file')
        return tools.en_return_data(return_data)


class ProductDelete(MethodView):
    def post(self):
        return_data = jsonify({ 'code':300 })
        try:
            product = {}
            product['id'] = request.values.get('product_id', 0)
            HolaWareHouse_op = HolaWareHouse()
            re = HolaWareHouse_op.Delete_product(product)
            if re:
                return_data = jsonify({ 'code':100 })
            else:
                return_data = jsonify({ 'code':109 })
        except Exception, e:
            print e
        return tools.en_return_data(return_data)

class ProductPutaway(MethodView):
    def post(self):
        return_data = jsonify({ 'code':300 })
        try:
            product = {}
            product['id'] = request.values.get('product_id', 0)
            HolaWareHouse_op = HolaWareHouse()
            re = HolaWareHouse_op.putaway_product(product)

            return_data = jsonify({ 'code':100 })

        except Exception, e:
            print e
        return tools.en_return_data(return_data)


from . import sys, sys_prefix

from control_center.admin import add_url

add_url.add_url(u"商品资料", 'sys.set', add_url.TYPE_ENTRY, sys_prefix,
                sys, '/all_product_show/', 'allproductshow', ProductView.as_view('allproductshow'), methods=['GET'])

add_url.add_url(u"商品类型添加", 'sys.allproductshow', add_url.TYPE_FEATURE, sys_prefix,
                sys, '/category_add/', 'categoryadd', ProductCategoryAdd.as_view('categoryadd'), methods=['POST'])

add_url.add_url(u"商品类型删除", 'sys.allproductshow', add_url.TYPE_FEATURE, sys_prefix,
                sys, '/category_delete/', 'categorydelete', ProductCategoryDelete.as_view('categorydelete'), methods=['POST'])

add_url.add_url(u"商品类型重命名", 'sys.allproductshow', add_url.TYPE_FEATURE, sys_prefix,
                sys, '/category_rename/', 'categoryrename', ProductCategoryRename.as_view('categoryrename'), methods=['POST'])

add_url.add_url(u"查看商品", 'sys.allproductshow', add_url.TYPE_FEATURE, sys_prefix,
                sys, '/product_show/', 'productshow', ProductShow.as_view('productshow'), methods=['POST'])

add_url.add_url(u"添加商品", 'sys.allproductshow', add_url.TYPE_FEATURE, sys_prefix,
                sys, '/product_add/', 'productadd', ProductAdd.as_view('productadd'), methods=['POST'])

add_url.add_url(u"添加商品图片", 'sys.productadd', add_url.TYPE_FEATURE, sys_prefix,
                sys, '/product_add_pic/', 'productaddpic', ProductPicAdd.as_view('productaddpic'), methods=['POST'])

add_url.add_url(u"删除商品图片", 'sys.productadd', add_url.TYPE_FEATURE, sys_prefix,
                sys, '/product_del_pic/', 'productdelpic', ProductPicDel.as_view('productdelpic'), methods=['POST'])

add_url.add_url(u"编辑商品", 'sys.allproductshow', add_url.TYPE_FEATURE, sys_prefix,
                sys, '/product_edit/', 'productedit', ProductEdit.as_view('productedit'), methods=['POST'])

add_url.add_url(u"删除商品", 'sys.allproductshow', add_url.TYPE_FEATURE, sys_prefix,
                sys, '/product_delete/', 'productdelete', ProductDelete.as_view('productdelete'), methods=['POST'])

add_url.add_url(u"查看所有商品", 'sys.allproductshow', add_url.TYPE_FUNC, sys_prefix,
                sys, '/all_product_data/', 'allproductdata', AllProductData.as_view('allproductdata'), methods=['GET'])

add_url.add_url(u"查看所有商品类型", 'sys.allproductshow', add_url.TYPE_FUNC, sys_prefix,
                sys, '/all_category_data/', 'allcategorydata', AllCategoryData.as_view('allcategorydata'), methods=['GET'])

add_url.add_url(u"上架或者下架产品", 'sys.allproductshow', add_url.TYPE_FUNC, sys_prefix,
                sys, '/product_putaway/', 'productputaway', ProductPutaway.as_view('productputaway'), methods=['POST'])