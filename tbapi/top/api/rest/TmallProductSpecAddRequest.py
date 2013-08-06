'''
Created by auto_sdk on 2013-04-01 16:44:41
'''
from top.api.base import RestApi
class TmallProductSpecAddRequest(RestApi):
	def __init__(self,domain='gw.api.taobao.com',port=80):
		RestApi.__init__(self,domain, port)
		self.barcode = None
		self.certified_pic_str = None
		self.image = None
		self.market_time = None
		self.product_code = None
		self.product_id = None
		self.spec_props = None
		self.spec_props_alias = None

	def getapiname(self):
		return 'tmall.product.spec.add'

	def getMultipartParas(self):
		return ['image']
