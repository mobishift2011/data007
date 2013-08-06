'''
Created by auto_sdk on 2013-04-01 16:44:41
'''
from top.api.base import RestApi
class AlipayPointOrderGetRequest(RestApi):
	def __init__(self,domain='gw.api.taobao.com',port=80):
		RestApi.__init__(self,domain, port)
		self.auth_token = None
		self.merchant_order_no = None
		self.user_symbol = None
		self.user_symbol_type = None

	def getapiname(self):
		return 'alipay.point.order.get'
