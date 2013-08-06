'''
Created by auto_sdk on 2013-04-01 16:44:41
'''
from top.api.base import RestApi
class PromotionCouponAddRequest(RestApi):
	def __init__(self,domain='gw.api.taobao.com',port=80):
		RestApi.__init__(self,domain, port)
		self.condition = None
		self.denominations = None
		self.end_time = None
		self.start_time = None

	def getapiname(self):
		return 'taobao.promotion.coupon.add'
