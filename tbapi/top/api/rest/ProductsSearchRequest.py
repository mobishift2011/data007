'''
Created by auto_sdk on 2013-04-01 16:44:41
'''
from top.api.base import RestApi
class ProductsSearchRequest(RestApi):
	def __init__(self,domain='gw.api.taobao.com',port=80):
		RestApi.__init__(self,domain, port)
		self.cid = None
		self.fields = None
		self.page_no = None
		self.page_size = None
		self.props = None
		self.q = None
		self.status = None
		self.vertical_market = None

	def getapiname(self):
		return 'taobao.products.search'
