'''
Created by auto_sdk on 2013-04-01 16:44:41
'''
from top.api.base import RestApi
class FenxiaoDistributorItemsGetRequest(RestApi):
	def __init__(self,domain='gw.api.taobao.com',port=80):
		RestApi.__init__(self,domain, port)
		self.distributor_id = None
		self.end_modified = None
		self.page_no = None
		self.page_size = None
		self.product_id = None
		self.start_modified = None

	def getapiname(self):
		return 'taobao.fenxiao.distributor.items.get'
