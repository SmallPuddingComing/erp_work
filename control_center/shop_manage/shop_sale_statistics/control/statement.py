#!/usr/bin/python
#-*- coding:utf-8 -*-
#    Copyright(c) 2015-2016 JmGo Company
#    All rights reserved.
#
#    文件名 : statement.py.py
#    作者   : WangYi
#  电子邮箱 : ywang@jmgo.com
#    日期   : 2016/10/29 14:56
#
#     描述  : 销售统计报表
#
import os
import xlwt
import StringIO

class StatictisStatementOp:
    """
    销售统计报表
    """
    def __init__(self):
        pass

    @staticmethod
    def check_para(paraname, para, instance):
        if not isinstance(para, instance):
            raise TypeError("%s must be %s. %s" % (paraname, instance, type(para)))

    @staticmethod
    def write_row(sheet, row, content):
        if not isinstance(content, list):
            raise TypeError("row:[%d] content must be list. %s" % (row, type(content)))

        col = 0
        for value in content:
            sheet.write(row, col, value)
            col += 1

    @staticmethod
    def sale_rank(sheet,
                  bgn_date,
                  end_date,
                  title,
                  field_title,
                  content):
        """
        排名类表单
        :param sheet: WorkSheet
        :param bgn_date: str 起始日期
        :param end_date: str 结束日期
        :param title: str 最顶上的标题
        :param field_title: list 栏位标题
        :param content: list 数据内容。
        """
        StatictisStatementOp.check_para('sheet', sheet, xlwt.Worksheet)
        StatictisStatementOp.check_para('bgn_date', bgn_date, (str, unicode))
        StatictisStatementOp.check_para('end_date', end_date, (str, unicode))
        StatictisStatementOp.check_para('title', title, (str, unicode))
        StatictisStatementOp.check_para('field_title', field_title, list)
        StatictisStatementOp.check_para('content', content, list)
        # 写入最顶上的标题
        # sheet.write(1, 1, title)
        # 写入栏位标题
        row = len(sheet.rows)
        sheet.write(row, 0, "   ")
        row += 1
        sheet.write(row, 0, u'日期:')
        sheet.write(row, 1, bgn_date)
        sheet.write(row, 2, end_date)
        row += 1
        StatictisStatementOp.write_row(sheet, row, field_title)
        # 写入文件内容
        row += 1
        for content_list in content:
            StatictisStatementOp.write_row(sheet, row, content_list)
            row += 1

    @staticmethod
    def business_statictis(title, content, date, **kw):
        """
        旗舰店业绩统计报表
        :param title: list 标题列表
        :param content: list  标题列表对应的内容
        :param date: str 统计的年月份
        :param kw:
        filename - 保存的文件名, 如果没有这个key，则不会保存文件
        :return: StringIO 用于存储execl的文件流
        """
        if not isinstance(title, list):
            raise TypeError("title must be list")
        elif not isinstance(content, list):
            raise TypeError("content must be list")

        workbook = xlwt.Workbook()
        sheet = workbook.add_sheet(u'旗舰店业绩统计')
        row = 0
        # 前两行内容
        sheet.write(row, 0, u'旗舰店业绩统计')
        row += 1
        sheet.write(row, 0, u'日期')
        sheet.write(row, 1, date)

        # 标题栏
        row += 1
        StatictisStatementOp.write_row(sheet, row, title)

        # 内容值
        row += 1
        for content_list in content:
            StatictisStatementOp.write_row(sheet, row, content_list)
            row += 1

        if kw.get('filename') is not None:
            workbook.save(kw.get('filename'))

        return StringIO.StringIO(workbook.get_biff_data())
