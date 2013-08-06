'''
Created by auto_sdk on 2013-04-01 16:44:41
'''
from top.api.base import RestApi
class WlbItemAuthorizationAddRequest(RestApi):
	def __init__(self,domain='gw.api.taobao.com',port=80):
		RestApi.__init__(self,domain, port)
		self.auth_type = None
		self.authorize_end_time = None
		self.authorize_start_time = None
		self.consign_user_nick = None
		self.item_id_list = None
		self.name = None
		self.quantity = None
		self.rule_code = None

	def getapiname(self):
		return 'taobao.wlb.item.authorization.add'
