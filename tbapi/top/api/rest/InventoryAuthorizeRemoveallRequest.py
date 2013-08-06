'''
Created by auto_sdk on 2013-04-01 16:44:41
'''
from top.api.base import RestApi
class InventoryAuthorizeRemoveallRequest(RestApi):
	def __init__(self,domain='gw.api.taobao.com',port=80):
		RestApi.__init__(self,domain, port)
		self.sc_item_id_list = None
		self.user_nick_list = None

	def getapiname(self):
		return 'taobao.inventory.authorize.removeall'
