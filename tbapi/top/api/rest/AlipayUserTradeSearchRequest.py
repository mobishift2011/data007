'''
Created by auto_sdk on 2013-04-01 16:44:41
'''
from top.api.base import RestApi
class AlipayUserTradeSearchRequest(RestApi):
	def __init__(self,domain='gw.api.taobao.com',port=80):
		RestApi.__init__(self,domain, port)
		self.alipay_order_no = None
		self.end_time = None
		self.merchant_order_no = None
		self.order_from = None
		self.order_status = None
		self.order_type = None
		self.page_no = None
		self.page_size = None
		self.start_time = None

	def getapiname(self):
		return 'alipay.user.trade.search'
