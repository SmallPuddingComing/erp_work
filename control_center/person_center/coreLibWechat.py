# -*- coding: utf-8 -*-

import json
import types
import urllib
import hashlib
import urllib2
from xml.etree import ElementTree

class CoreLibWechat(object):
    ''' 微信接口 '''
    MSGTYPE_TEXT      = 'text'
    
    API_URL_PREFIX    = 'https://api.weixin.qq.com/cgi-bin'
    AUTH_URL          = '/token?grant_type=client_credential&'
    QRCODE_CREATE_URL = '/qrcode/create?'
    QRCODE_IMG_URL    = 'https://mp.weixin.qq.com/cgi-bin/showqrcode?ticket='
    USER_INFO_URL     = '/user/info?'
    TRANSFER_URL      = 'https://api.mch.weixin.qq.com/mmpaymkttransfers/promotion/transfers'
    
    #加密KEY
    SGIN_KEY          = 'ULGcLuEIdLPbcghSIU2SJ9b61erZaJJy'
    #微信商户号
    MCHID             = '39484589458'

    def __init__(self, token, appid, appSecret, logCallBack = None):
        ''' 
            初始化微信类
        '''
        self._msg          = {}
        self._receive      = None
        self.errCode       = 40001
        self.errMsg        = 'NO ACCESS'
        self.access_token  = ''
        
        self.token         = token
        self.appid         = appid
        self.appSecret     = appSecret
        self.__logCallBack = logCallBack if type(logCallBack) == types.FunctionType else None

    def __randomStrLength(self, randomlength = 8):
        ''' 生成固定长度随机数 '''
        str = ''
        chars = 'qwertyuiopasdfghjklzxcvbnm0123456789'
        length = len(chars) - 1
        random = Random()
        for i in range(randomlength):
            str += chars[random.randint(0, length)]
        return str

    def __getSgin(self, params):
        ''' 生成sign '''
        keyStr = urllib.urlencode(sorted(params.iteritems())) + '&key=' + CoreLibWechat.SGIN_KEY
        return hashlib.md5(keyStr).hexdigest().upper()

    def __arrayToXml(self, params):
        ''' 字典转XML '''
        xml = "<xml>"
        for key,value in params.items():
            if isinstance(value, (int, float)):
                xml += ("<%s>%s</%s>" % (key, value, key))
            else:
                xml += ("<%s><![CDATA[%s]]></%s>" % (key, value, key))
        xml += "</xml>"
        return xml

    def __xmlToArray(self, params):
        ''' xml转Array '''
        paramsArray = {}
        paramsXML = str(params)
        root = ElementTree.fromstring(paramsXML)

        for child in root:
            fieldName = str(child.tag)
            childNode = root.getiterator(fieldName)
            paramsArray[fieldName] = childNode[0].text

        return paramsArray

    def checkSignature(self, signature, timestamp, nonce):
        ''' 验证TOKEN '''
        signature = signature or ''; timestamp = timestamp or ''; nonce = nonce
        sginStr = hashlib.md5(''.join(map(str, sorted([self.token, timestamp, nonce])))).hexdigest().upper()
        return sginStr == signature

    def getRev(self, params):
        ''' 获取微信服务器发来的信息 '''
        if self._receive:
            return self
        self._receive = self.__xmlToArray(params)

    def getRevFrom(self):
        ''' 消息发送者 '''
        if self._receive:
            return self._receive.get('FromUserName', False)
        return False

    def getRevTo(self):
        ''' 消息接收者 '''
        if self._receive:
            return self._receive.get('ToUserName', False)
        return False

    def getRevType(self):
        ''' 消息类型 '''
        if self._receive:
            return self._receive.get('MsgType', False)
        return False

    def getRevID(self):
        ''' 消息ID '''
        if self._receive:
            return self._receive.get('MsgId', False)
        return False

    def getRevCtime(self):
        ''' 消息发送时间 '''
        if self._receive:
            rest = self._receive.get('CreateTime', False)
            if rest:
                return int(rest)
        return False

    def getRevContent(self):
        ''' 消息内容正文 '''
        if self._receive:
            return self._receive.get('Content', False)
        return False

    def text(self, value):
        ''' 文本回复 '''
        self._msg = {
            'ToUserName': self.getRevFrom(),
            'FromUserName': self.getRevTo(),
            'CreateTime': int(time.time()),
            'MsgType': CoreLibWechat.MSGTYPE_TEXT,
            'Content': str(value)
        }

        return self

    def reply(self, msg = None):
        ''' 回复微信服务器 '''
        if msg is None:
            msg = self._msg
        return msg if not isinstance(msg, (dict, list)) else self.__arrayToXml()

    def httpGET(self, url, params = None):
        ''' http get 请求 '''
        params = urllib.urlencode({} if params is None else params)
        url += '' if not params else '?' + params if url.find('?') < 0 else params if url.endswith('?') or url.endswith('&') else '&' + params
        try:
            response = urllib2.urlopen(url).read()
            return response
        except urllib2.URLError, e:
            pass
        return False

    def httpPOST(self, url, data = None):
        ''' http post 请求 '''
        if isinstance(data, (dict, list)):
            data = urllib.urlencode({} if data is None else data)

        try:
            return urllib2.urlopen(url = url, data = data).read()
        except urllib2.URLError, e:
            pass
        return False

    def checkAuth(self, appid = None, appSecret = None): 
        ''' 通用auth验证方法 '''
        appid = appid or self.appid
        appSecret = appSecret or self.appSecret
        rest = self.httpGET(CoreLibWechat.API_URL_PREFIX + CoreLibWechat.AUTH_URL, {'appid': appid, 'secret': appSecret})
        
        if rest:
            restJSON = json.loads(rest)
            if restJSON.get('errcode'):
                self.errCode = restJSON.get('errcode')
                self.errMsg = restJSON.get('errmsg')
                return False

            self.access_token = restJSON.get('access_token')
            expire = 3600 if not restJSON.get('expires_in') else int(restJSON.get('expires_in'))
            return self.access_token

        return False

    def getQRCode(self, scene, code = 0, expire = 1800):
        '''
            创建二维码ticket
            scene 场景值
            code 0:临时二维码
            code 1:永久二维码
            code 2:永久二维码(永久的字符串参数值)
            expire 过期时间
        '''
        expire = min(2592000, max(60, expire))
        if not self.access_token and not self.checkAuth():
            return False

        if code not in [0, 1, 2]:
            return False

        data = {
            #二维码类型，QR_SCENE为临时,QR_LIMIT_SCENE为永久,QR_LIMIT_STR_SCENE为永久的字符串参数值
            'action_name': 'QR_SCENE' if code == 0 else 'QR_LIMIT_SCENE' if code == 1 else 'QR_LIMIT_STR_SCENE',
            'expire_seconds': expire,
            'action_info': {
                'scene': {
                    'scene_id': scene
                }
            }
        }

        if type(scene) == types.StringType:
            #场景值ID（字符串形式的ID），字符串类型，长度限制为1到64，仅永久二维码支持此字段
            if data.get('action_name') != 'QR_LIMIT_STR_SCENE':
                return False
            else:
                del data['action_info']['scene']['scene_id']
                data['action_info']['scene']['scene_str'] = scene

        if code in [1, 2]:
            del data['expire_seconds']

        url = CoreLibWechat.API_URL_PREFIX + CoreLibWechat.QRCODE_CREATE_URL + 'access_token=' + self.access_token
        rest = self.httpPOST(url, json.dumps(data))

        if rest:
            restJSON = json.loads(rest)
            if restJSON.get('errcode'):
                self.errCode = restJSON.get('errcode')
                self.errMsg = restJSON.get('errmsg')
                return False
            return restJSON
        return False

    def getQRUrl(self, ticket):
        ''' 获取二维码图片 '''
        return CoreLibWechat.QRCODE_IMG_URL + ticket

    def getUserInfo(self, openid):
        ''' 获取关注者详细信息 '''
        if not self.access_token and not self.checkAuth():
            return False

        rest = self.httpGET(CoreLibWechat.API_URL_PREFIX + CoreLibWechat.USER_INFO_URL, {'access_token': self.access_token, 'openid': openid})
        if rest:
            restJSON = json.loads(rest)
            if restJSON.get('errcode'):
                self.errCode = restJSON.get('errcode')
                self.errMsg = restJSON.get('errmsg')
                return False
            return restJSON
        return False

    def transfer(self, openid, amount, ordersn, desc, ip):
        ''' 转账接口 '''
        params = {
            'mch_appid': self.appid,
            'mchid': CoreLibWechat.MCHID,
            'nonce_str': self.__randomStrLength(32),
            'partner_trade_no': ordersn,
            'openid': openid,
            'check_name': 'NO_CHECK',
            'amount': amount,
            'desc': desc,
            'spbill_create_ip': ip
        }

        params['sign'] = self.__getSgin(params)
        xmlData = self.__arrayToXml(params)

        rest = self.httpPOST(CoreLibWechat.TRANSFER_URL, xmlData)
        if rest:
            rest = self.__xmlToArray(rest)
            if rest.get('return_code') != 'SUCCESS':
                return {'code': rest.get('return_code'), 'msg': rest.get('return_msg')}
            if rest.get('result_code') != 'SUCCESS':
                return {'code': rest.get('result_code'), 'msg': rest.get('err_code_des')}

            return {
                'code': rest.get('err_code_des'),
                'ordersn': rest.get('payment_no'),
                'paytime': rest.get('payment_time')
            }
        return False