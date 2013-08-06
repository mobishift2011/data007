'''
Created by auto_sdk on 2013-04-01 16:44:41
'''
from top.api.base import RestApi
class ItemQuantityUpdateRequest(RestApi):
	def __init__(self,domain='gw.api.taobao.com',port=80):
		RestApi.__init__(self,domain, port)
		self.num_iid = None
		self.outer_id = None
		self.quantity = None
		self.sku_id = None
		self.type = None

	def getapiname(self):
		return 'taobao.item.quantity.update'
