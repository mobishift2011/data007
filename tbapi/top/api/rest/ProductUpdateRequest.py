'''
Created by auto_sdk on 2013-04-01 16:44:41
'''
from top.api.base import RestApi
class ProductUpdateRequest(RestApi):
	def __init__(self,domain='gw.api.taobao.com',port=80):
		RestApi.__init__(self,domain, port)
		self.binds = None
		self.desc = None
		self.image = None
		self.major = None
		self.name = None
		self.native_unkeyprops = None
		self.outer_id = None
		self.packing_list = None
		self.price = None
		self.product_id = None
		self.sale_props = None

	def getapiname(self):
		return 'taobao.product.update'

	def getMultipartParas(self):
		return ['image']
