'''
Created by auto_sdk on 2013-04-01 16:44:41
'''
from top.api.base import RestApi
class FenxiaoOrderCustomfieldUpdateRequest(RestApi):
	def __init__(self,domain='gw.api.taobao.com',port=80):
		RestApi.__init__(self,domain, port)
		self.isv_custom_key = None
		self.isv_custom_value = None
		self.purchase_order_id = None

	def getapiname(self):
		return 'taobao.fenxiao.order.customfield.update'
