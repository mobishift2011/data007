'''
Created by auto_sdk on 2013-04-01 16:44:41
'''
from top.api.base import RestApi
class FenxiaoDiscountUpdateRequest(RestApi):
	def __init__(self,domain='gw.api.taobao.com',port=80):
		RestApi.__init__(self,domain, port)
		self.detail_ids = None
		self.detail_statuss = None
		self.discount_id = None
		self.discount_name = None
		self.discount_status = None
		self.discount_types = None
		self.discount_values = None
		self.target_ids = None
		self.target_types = None

	def getapiname(self):
		return 'taobao.fenxiao.discount.update'
