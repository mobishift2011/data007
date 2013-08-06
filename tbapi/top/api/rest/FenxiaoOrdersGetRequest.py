'''
Created by auto_sdk on 2013-04-01 16:44:41
'''
from top.api.base import RestApi
class FenxiaoOrdersGetRequest(RestApi):
	def __init__(self,domain='gw.api.taobao.com',port=80):
		RestApi.__init__(self,domain, port)
		self.end_created = None
		self.fields = None
		self.page_no = None
		self.page_size = None
		self.purchase_order_id = None
		self.start_created = None
		self.status = None
		self.time_type = None

	def getapiname(self):
		return 'taobao.fenxiao.orders.get'
