'''
Created by auto_sdk on 2013-04-01 16:44:41
'''
from top.api.base import RestApi
class WlbInventoryDetailGetRequest(RestApi):
	def __init__(self,domain='gw.api.taobao.com',port=80):
		RestApi.__init__(self,domain, port)
		self.inventory_type_list = None
		self.item_id = None
		self.store_code = None

	def getapiname(self):
		return 'taobao.wlb.inventory.detail.get'
