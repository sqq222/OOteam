import datetime
import json
from binascii import b2a_hex, a2b_hex

import requests
from Crypto.Cipher import AES
from django.conf import settings




class AESCustom:
    def __init__(self):
        self.key = settings.AES_KEY
        self.mode = AES.MODE_CBC

    # 加密函数，如果text不足16位就用空格补足为16位，
    # 如果大于16当时不是16的倍数，那就补足为16的倍数。
    def encrypt(self, text):
        cryptor = AES.new(self.key, self.mode, b'0000000000000000')
        # 这里密钥key 长度必须为16（AES-128）,
        # 24（AES-192）,或者32 （AES-256）Bytes 长度
        # 目前AES-128 足够目前使用
        length = 16
        count = len(text)
        if count < length:
            add = (length - count)
            # \0 backspace
            text = text + ('\0' * add)
        elif count > length:
            add = (length - (count % length))
            text = text + ('\0' * add)
        self.ciphertext = cryptor.encrypt(text)
        # 因为AES加密时候得到的字符串不一定是ascii字符集的，输出到终端或者保存时候可能存在问题
        # 所以这里统一把加密后的字符串转化为16进制字符串
        return b2a_hex(self.ciphertext)

    # 解密后，去掉补足的空格用strip() 去掉
    def decrypt(self, text):
        cryptor = AES.new(self.key, self.mode, b'0000000000000000')
        plain_text = cryptor.decrypt(a2b_hex(text))
        return plain_text.decode().replace('\u0000', '').replace('\u0010', '')


class TaxTool:
    @staticmethod
    def tax(price, num, is_include_tax, tax_value):
        if is_include_tax:
            tax = (price - (price / (1 + (tax_value / 100)))) * num
        else:
            tax = price * tax_value / 100 * num
        return tax


class Easemob:
    @staticmethod
    def get_token():
        url = settings.EASEMOB_BASE_URL + 'token'
        payload = {
            "grant_type": "client_credentials",
            "client_id": settings.EASEMOB_CLIENT_ID,
            "client_secret": settings.EASEMOB_SECRET
        }
        headers = {
            'content-type': "application/json",
        }
        response = requests.request('POST', url, data=json.dumps(payload), headers=headers)
        if response.status_code == 200:
            settings.EASEMOB_TOKEN = response.json().get('access_token')
            settings.EASEMOB_EXPIRES = datetime.datetime.now() + datetime.timedelta(
                seconds=response.json().get('expires_in'))

        return response.text

    @staticmethod
    def register_user(username, password, fullname):
        url = settings.EASEMOB_BASE_URL + 'users'
        payload = {
            "username": username,
            "password": password,
            "nickname": fullname
        }
        headers = {
            'content-type': "application/json",
            'Authorization': "Bearer {0}".format(settings.EASEMOB_TOKEN)
        }
        response = requests.request('POST', url, data=json.dumps(payload), headers=headers)
        if response.status_code == 200:
            return response.json().get('entities')[0].get('uuid')
        return None
