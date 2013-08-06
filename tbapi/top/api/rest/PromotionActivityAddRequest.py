'''
Created by auto_sdk on 2013-04-01 16:44:41
'''
from top.api.base import RestApi
class PromotionActivityAddRequest(RestApi):
	def __init__(self,domain='gw.api.taobao.com',port=80):
		RestApi.__init__(self,domain, port)
		self.coupon_count = None
		self.coupon_id = None
		self.person_limit_count = None
		self.upload_to_taoquan = None

	def getapiname(self):
		return 'taobao.promotion.activity.add'
