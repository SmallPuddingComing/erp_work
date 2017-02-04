#!/usr/bin/python
# -*- coding:utf-8 -*-
#    Copyright(c) 2015-2016 JmGo Company
#    All rights reserved.
#
#    文件名 : trash_op.py
#    作者   : tangjinxing
#    日期   : 2016年11月30日10:50:00
#     描述  : 物料信息-->回收站页面 op
#

from sqlalchemy import and_, func
from public.exception.custom_exception import CodeError
from config.service_config.returncode import ServiceCode
from data_mode.erp_supply.control_base.controlBase import ControlEngine
from config.share.share_define import SupplyAttr
from data_mode.erp_supply.mode.supply_manage_mode.supplier_attribute import SupplierAttribute
from data_mode.erp_supply.mode.material_manage_mode.material_baseinfo import MaterialBaseInfo
from data_mode.erp_supply.base_op.material_op.category_op import CategoryOp


class TrashOp(ControlEngine):
    """
    回收站页面op
    """
    def __init__(self):
        """
        控制引擎初始化
        """
        ControlEngine.__init__(self)

    def trash_material_info(self):
        """
        获取所有的已删除的物料信息
        :return:
        """
        material_info = []
        try:
            rs = self.controlsession.query(MaterialBaseInfo).filter_by(state="7-4").\
                        limit(10).offset(0).all()
            total = self.controlsession.query(func.count(MaterialBaseInfo.id)).\
                filter_by(state="7-4").scalar()
            if rs:
                for item in rs:
                    j_data = item.to_material_json()
                    item_dict = dict()
                    item_dict["m_id"] = j_data["id"]
                    item_dict["m_code"] = j_data["code"]
                    item_dict["m_name"] = j_data["name"]
                    item_dict["m_state"] = SupplyAttr.MATERIAL_STATE_TYPE[j_data["state"]]
                    item_dict["old_code"] = j_data["old_code"]
                    item_dict["m_spec"] = j_data["specifications"]
                    m_attr = self.controlsession.query(SupplierAttribute.name).\
                        filter_by(id=j_data["attribute_id"]).first()
                    if not m_attr:
                        raise CodeError(ServiceCode.service_exception, u"属性查询error")
                    item_dict["m_attr"] = m_attr[0]
                    material_info.append(item_dict)
        except CodeError:
            raise
        except Exception:
            raise
        return material_info, total

    @staticmethod
    def material_attr_info():
        """
        获取物料所有的属性信息
        :return:
        """
        m_attr_list = []
        a_dict = {
            "attr_id": "0",
            "attr_name": u"物料属性"
        }
        m_attr_list.append(a_dict)
        for key, value in SupplyAttr.MATERIAL_ATTRIBUTE_TYPE.items():
            item_dict = dict()
            item_dict["attr_id"] = key
            item_dict["attr_name"] = value
            m_attr_list.append(item_dict)

        return m_attr_list

    @staticmethod
    def material_category_info():
        """
        获取所有的物料分类信息
        :return:
        """
        m_category_info = []
        try:
            category_op = CategoryOp()
            body = category_op.get_all_category()
            for item in body:
                item_dict = dict()
                item_dict["m_cate_id"] = item["id"]
                item_dict["m_cate_code"] = item["code"]
                item_dict["m_cate_name"] = item["name"]
                item_dict["p_cate_id"] = item["pid"]
                print item_dict
                m_category_info.append(item_dict)
        except Exception:
            raise
        return m_category_info

    def trash_info(self):
        """
        获取进入回收站页面所需数据
        :return:
        """
        try:
            m_attr_list = self.material_attr_info()
            m_category_info = self.material_category_info()
            material_info, total = self.trash_material_info()
            r_data = {
                "m_attr_list": m_attr_list,
                "m_category_info": m_category_info,
                "material_info": material_info,
                "total": total
            }
        except CodeError:
            raise
        except Exception:
            raise
        return r_data

    def trash_search_info(self, search_dict):
        """
        回收站信息搜索接口
        :param search_dict ={
             page:        第几页
             per_page:    每页显示数
             key:         搜索条件
             value:       搜索值
             m_attr:      物料属性id
             }
        :return:
        """
        try:
            page = search_dict["page"]
            per_page = search_dict["per_page"]
            key = search_dict["key"]
            value = search_dict["value"]
            m_attr = search_dict["m_attr"]
            m_cate_id = search_dict["m_cate_id"]
            material_info = []
            start = (page-1)*per_page
            condition = and_()
            condition.append(MaterialBaseInfo.state == '7-4')
            if value is not None and value is not u"" and value is not "":
                if key == "m_code":
                    condition.append(MaterialBaseInfo.code == value)
                if key == "m_name":
                    condition.append(MaterialBaseInfo.name == value)
                if key == "old_code":
                    condition.append(MaterialBaseInfo.old_code == value)
            if m_attr is not None and m_attr is not "0" and m_attr is not u"" and m_attr is not "":
                condition.append(MaterialBaseInfo.attribute_id == m_attr)
            if m_cate_id is not None and m_cate_id is not u"" and m_cate_id is not "":
                op_cate = CategoryOp()
                cate_list = op_cate.get_child_category(list(m_cate_id))
                cate_list.append(int(m_cate_id))
                condition.append(MaterialBaseInfo.category_id.in_(cate_list))

            rs = self.controlsession.query(MaterialBaseInfo).filter(condition).\
                limit(per_page).offset(start).all()
            total = self.controlsession.query(func.count(MaterialBaseInfo.id)).filter(condition).scalar()
            if rs:
                for item in rs:
                    data_json = item.to_material_json()
                    item_dict = dict()
                    item_dict["m_id"] = data_json["id"]
                    item_dict["m_code"] = data_json["code"]
                    item_dict["m_name"] = data_json["name"]
                    item_dict["m_state"] = SupplyAttr.MATERIAL_STATE_TYPE[data_json["state"]]
                    item_dict["old_code"] = data_json["old_code"]
                    item_dict["m_spec"] = data_json["specifications"]
                    m_attr = self.controlsession.query(SupplierAttribute.name).\
                        filter_by(id=data_json["attribute_id"]).first()
                    if not m_attr:
                        raise CodeError(ServiceCode.service_exception, u"属性查询error")
                    item_dict["m_attr"] = m_attr[0]
                    material_info.append(item_dict)
            r_data = {
                'material_info': material_info,
                'total': total
            }
        except CodeError:
            raise
        except Exception:
            raise
        return r_data

    def material_batch_del(self, id_list):
        """
        根据id删除物料
        :param id_list:  物料 id 列表
        :return:
        """
        r_data = {}
        try:
            if id_list:
                for item in id_list:
                    r_obj = self.controlsession.query(MaterialBaseInfo).filter_by(id=item).first()
                    if r_obj:
                        self.controlsession.delete(r_obj)
                    else:
                        raise CodeError(ServiceCode.service_exception, u"删除失败")
            else:
                raise CodeError(ServiceCode.service_exception, u"id 为空")

            self.controlsession.commit()
        except CodeError:
            self.controlsession.rollback()
            raise
        except Exception:
            self.controlsession.rollback()
            raise
        return r_data

    def material_batch_recover(self, id_list):
        """
        根据id恢复物料
        :param id_list:  物料 id 列表
        :return:
        """
        r_data = {}
        try:
            if id_list:
                for item in id_list:
                    r_obj = self.controlsession.query(MaterialBaseInfo).filter_by(id=item).first()
                    if r_obj:
                        r_obj.state = "7-1"
                    else:
                        raise CodeError(ServiceCode.service_exception, u"恢复失败")
                    self.controlsession.add(r_obj)
            else:
                raise CodeError(ServiceCode.service_exception, u"id 为空")

            self.controlsession.commit()
        except CodeError:
            self.controlsession.rollback()
            raise
        except Exception:
            self.controlsession.rollback()
            raise
        return r_data

    def test(self):
        rs = self.material_category_info()
        pass


if __name__ == "__main__":
    op = TrashOp()
    op.test()
