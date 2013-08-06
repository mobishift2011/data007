'''
Created by auto_sdk on 2013-04-01 16:44:41
'''
from top.api.base import RestApi
class FenxiaoProductSkuUpdateRequest(RestApi):
	def __init__(self,domain='gw.api.taobao.com',port=80):
		RestApi.__init__(self,domain, port)
		self.agent_cost_price = None
		self.dealer_cost_price = None
		self.product_id = None
		self.properties = None
		self.quantity = None
		self.sku_number = None
		self.standard_price = None

	def getapiname(self):
		return 'taobao.fenxiao.product.sku.update'
