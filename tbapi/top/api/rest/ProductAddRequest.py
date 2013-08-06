'''
Created by auto_sdk on 2013-04-01 16:44:41
'''
from top.api.base import RestApi
class ProductAddRequest(RestApi):
	def __init__(self,domain='gw.api.taobao.com',port=80):
		RestApi.__init__(self,domain, port)
		self.binds = None
		self.cid = None
		self.customer_props = None
		self.desc = None
		self.image = None
		self.major = None
		self.market_time = None
		self.name = None
		self.outer_id = None
		self.packing_list = None
		self.price = None
		self.property_alias = None
		self.props = None
		self.sale_props = None

	def getapiname(self):
		return 'taobao.product.add'

	def getMultipartParas(self):
		return ['image']
