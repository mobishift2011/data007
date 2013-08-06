'''
Created by auto_sdk on 2013-04-01 16:44:41
'''
from top.api.base import RestApi
class InventoryStoreManageRequest(RestApi):
	def __init__(self,domain='gw.api.taobao.com',port=80):
		RestApi.__init__(self,domain, port)
		self.address = None
		self.address_area_name = None
		self.alias_name = None
		self.contact = None
		self.operate_type = None
		self.phone = None
		self.postcode = None
		self.store_code = None
		self.store_name = None
		self.store_type = None

	def getapiname(self):
		return 'taobao.inventory.store.manage'
