#!/usr/bin/python
# -*- coding:utf-8 -*-

import traceback
from sqlalchemy import and_
from public.exception.custom_exception import CodeError
from config.service_config.returncode import ServiceCode
from data_mode.erp_supply.control_base.controlBase import ControlEngine
from data_mode.erp_supply.mode.material_manage_mode.bom_category_info import BomCategoryInfo
from data_mode.erp_supply.mode.material_manage_mode.bom_relation_info import BomRelationInfo
from data_mode.erp_supply.mode.material_manage_mode.material_baseinfo import MaterialBaseInfo
from data_mode.erp_supply.base_op.material_op.baseinfo_op import Baseinfo_Op


class BomCategoryOp(ControlEngine):
    def __init__(self):
        """
        :return:
        """
        ControlEngine.__init__(self)

    def get_son_bom_by_id(self, g_id, p_id):
        """
        FUNCTION: 根据父bomid 获取所有的子bom
        :param p_id:
        :param g_id:
        :return:
        """
        try:
            r_data = []
            condition = and_()
            condition.append(BomRelationInfo.parent_id == int(p_id))
            condition.append(MaterialBaseInfo.bom_code.isnot(None))
            condition.append(MaterialBaseInfo.id == BomRelationInfo.material_id)

            rs = self.controlsession.query(
                    BomRelationInfo.material_id,
                    BomRelationInfo.parent_id,
                    MaterialBaseInfo.bom_code,
                    MaterialBaseInfo.name,
                    MaterialBaseInfo.bom_category_id).\
                filter(condition).group_by(BomRelationInfo.material_id).all()

            for item in rs:
                item_dict = dict()
                item_dict["id"] = item[0]
                item_dict["g_id"] = g_id + "_" + str(item[0])
                item_dict["g_code"] = item[2]
                item_dict["g_name"] = item[3]
                item_dict["p_id"] = g_id                        # 一级BOM的父id为分组id
                item_dict["g_state"] = 1                        # 1表示是BOM

                r_data.append(item_dict)
                rs_d = self.get_son_bom_by_id(item_dict["g_id"], item[0])
                r_data += rs_d

        except Exception:
            raise
        else:
            return r_data

    def get_bomcategory_info(self):

        """
        获取BOM所有的分组信息
        :return:
        """
        r_data = []
        try:
            rs_b = self.controlsession.query(BomCategoryInfo).all()
            for item in rs_b:
                item_dict = dict()
                item_dict["id"] = item.id
                item_dict["g_id"] = str(item.id)+"g"
                item_dict["g_code"] = item.code
                item_dict["g_name"] = item.name
                item_dict["level"] = item.level
                if item.parent_id:
                    item_dict["p_id"] = str(item.parent_id) + "g"
                else:
                    item_dict["p_id"] = 0               # 0表示一级分组
                item_dict["g_state"] = 0                # 0表示是BOM分组
                r_data.append(item_dict)
            for item in rs_b:
                condition_m = and_()
                condition_m.append(MaterialBaseInfo.bom_code.isnot(None))
                condition_m.append(MaterialBaseInfo.bom_category_id == item.id)
                rs_m = self.controlsession.query(MaterialBaseInfo).filter(condition_m).all()
                for m_item in rs_m:
                    item_dict = dict()
                    item_dict["id"] = m_item.id
                    item_dict["g_id"] = str(m_item.bom_category_id) + "_" + str(m_item.id)
                    item_dict["g_code"] = m_item.bom_code
                    item_dict["g_name"] = m_item.name
                    item_dict["p_id"] = str(m_item.bom_category_id) + "g"         # 一级BOM的父id为分组id
                    item_dict["g_state"] = 1                                    # 1表示是BOM
                    r_data.append(item_dict)
                    rs = self.get_son_bom_by_id(item_dict["g_id"], m_item.id)
                    r_data += rs

        except CodeError:
            raise
        except Exception:
            raise

        return r_data

    @staticmethod
    def get_bom_overview(bom_id=None):
        """
        获取BOM概览信息
        :param bom_id:
        :return:
        """
        r_data = {}
        try:
            op_b = Baseinfo_Op()
            rs = op_b.get_baseinfo_by_id(bom_id)
            if rs[1] and rs[0] == 0:
                r_data["b_code"] = rs[1]["bom_code"]
                r_data["b_version"] = rs[1]["bom_version"]
                r_data["m_code"] = rs[1]["code"]
                r_data["m_name"] = rs[1]["name"]
                r_data["m_spec"] = rs[1]["specifications"]
                r_data["m_attr"] = op_b.get_attribute_name(rs[1]["attribute_id"])
                r_data["b_rem"] = rs[1]["bom_rem"] if rs[1]["bom_rem"] is not None else ""
            else:
                raise CodeError(300, u"查询BOM错误")
        except CodeError:
            raise
        except Exception:
            raise
        return r_data

    def check_category_code(self, b_code):
        """
        检查分组代码
        :param b_code:
        :return: True 该分组存在，False 该分组不存在
        """

        rs = self.controlsession.query(BomCategoryInfo).filter_by(code=b_code).first()
        if rs:
            return True
        else:
            return False

    def save_category(self, b_code, b_name, p_id, level):
        """
        保存分组信息
        :param b_code: 分组代码
        :param b_name: 分组名称
        :param p_id:    父分组id
        :param level:    分组层级
        :return:
        """
        try:
            if p_id == 0 or p_id is None or p_id is u"":
                b_obj = BomCategoryInfo(code=b_code, name=b_name, level=level)
            else:
                b_obj = BomCategoryInfo(code=b_code, name=b_name, parent_id=p_id, level=level)
            self.controlsession.add(b_obj)
            self.controlsession.commit()
        except Exception:
            self.controlsession.rollback()
            raise

    def update_category(self, g_id, g_name, g_code):
        """
        更新分组信息
        :param g_id:        #分组id
        :param g_name:      #分组名称
        :param g_code:      #分组代码
        :return:
        """
        try:
            b_obj = self.controlsession.query(BomCategoryInfo).filter_by(id=g_id).first()
            if b_obj:
                b_obj.code = g_code
                b_obj.name = g_name
                self.controlsession.add(b_obj)
            else:
                raise CodeError(300, u"更新失败")

            self.controlsession.commit()
        except CodeError:
            self.controlsession.rollback()
            raise
        except Exception:
            self.controlsession.rollback()
            raise

    def check_is_category(self, g_id):
        """
        检查分组是否为空
        :param g_id:
        :return:  True 为空 ，False存在子分组或者子Bom
        """
        g_rs = self.controlsession.query(BomCategoryInfo).filter_by(parent_id=g_id).first()

        b_rs = self.controlsession.query(MaterialBaseInfo).filter_by(bom_category_id=g_id).first()

        if g_rs is not None or b_rs is not None:
            return False
        else:
            return True

    def delete_category(self, g_id):
        """
        删除分组
        :param g_id: 分组id
        :return:
        """
        try:
            rs = self.check_is_category(g_id)
            if not rs:
                raise CodeError(300, u"分组不为空")
            else:
                rs = self.controlsession.query(BomCategoryInfo).filter_by(id=g_id).first()
                self.controlsession.delete(rs)
                self.controlsession.commit()

        except CodeError:
            raise
        except Exception:
            self.controlsession.rollback()
            raise

    def bom_info_search(self, key=None, value=None):
        """

        搜索BOM
        :param key:
        :param value:
        :return:
        """
        r_data = []
        try:
            rs = {}
            if key is None or value is None or key is u"" or value is u"" or value is "":
                r_data = self.get_bomcategory_info()
            else:
                if key in ("b_name", "b_code"):
                    b_op = Baseinfo_Op()
                    if key == "b_name":
                        rs = b_op.get_info_by_name(value)
                    elif key == "b_code":
                        rs = b_op.get_info_by_code(value)
                else:
                    raise CodeError(300, u"key error")

                if isinstance(rs, list):
                    for item in rs:
                        r_dict = dict()
                        r_dict["id"] = item["id"]
                        r_dict["g_code"] = item["bom_code"]
                        r_dict["g_name"] = item["name"]
                        r_dict["g_state"] = 1                       # 前端需要 没有实际业务意义
                        r_dict["p_id"] = 0                          # 前端需要 没有实际业务意义
                        r_dict["g_id"] = str(r_dict["id"])+"b"      # 前端需要 没有实际业务意义
                        r_data.append(r_dict)
                elif isinstance(rs, dict) and rs:
                    r_dict = dict()
                    r_dict["id"] = rs.get("id", None)
                    r_dict["g_code"] = rs.get("bom_code", None)
                    r_dict["g_name"] = rs.get("name", None)
                    r_dict["g_state"] = 1                       # 前端需要 没有实际业务意义
                    r_dict["p_id"] = 0                          # 前端需要 没有实际业务意义
                    r_dict["g_id"] = str(r_dict["id"])+"b"      # 前端需要 没有实际业务意义
                    r_data.append(r_dict)
        except CodeError:
            raise
        except Exception:
            raise
        return r_data

    def get_bom_category(self, category_id):
        datas = self.controlsession.query(BomCategoryInfo).filter(BomCategoryInfo.id==category_id).first()
        if datas is None:
            raise CodeError(ServiceCode.service_exception, msg=u"BOM分组ID为%s的记录不存在" % category_id)
        else:
            return datas.to_json()


if __name__ == "__main__":

    op = BomCategoryOp()
    op.test()
