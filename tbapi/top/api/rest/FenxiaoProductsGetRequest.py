'''
Created by auto_sdk on 2013-04-01 16:44:41
'''
from top.api.base import RestApi
class FenxiaoProductsGetRequest(RestApi):
	def __init__(self,domain='gw.api.taobao.com',port=80):
		RestApi.__init__(self,domain, port)
		self.end_modified = None
		self.fields = None
		self.is_authz = None
		self.item_ids = None
		self.outer_id = None
		self.page_no = None
		self.page_size = None
		self.pids = None
		self.productcat_id = None
		self.sku_number = None
		self.start_modified = None
		self.status = None

	def getapiname(self):
		return 'taobao.fenxiao.products.get'
