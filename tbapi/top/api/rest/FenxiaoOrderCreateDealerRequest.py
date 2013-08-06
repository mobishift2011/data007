'''
Created by auto_sdk on 2013-04-01 16:44:41
'''
from top.api.base import RestApi
class FenxiaoOrderCreateDealerRequest(RestApi):
	def __init__(self,domain='gw.api.taobao.com',port=80):
		RestApi.__init__(self,domain, port)
		self.addr = None
		self.buyer_name = None
		self.city = None
		self.country = None
		self.logistic_fee = None
		self.logistic_type = None
		self.message = None
		self.mobile_phone = None
		self.outer_id = None
		self.pay_type = None
		self.phone = None
		self.province = None
		self.sub_order_detail = None
		self.zip_code = None

	def getapiname(self):
		return 'taobao.fenxiao.order.create.dealer'
