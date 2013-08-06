'''
Created by auto_sdk on 2013-04-01 16:44:41
'''
from top.api.base import RestApi
class InventoryOccupyCancelRequest(RestApi):
	def __init__(self,domain='gw.api.taobao.com',port=80):
		RestApi.__init__(self,domain, port)
		self.biz_unique_code = None
		self.operate_code = None
		self.store_code = None

	def getapiname(self):
		return 'taobao.inventory.occupy.cancel'
