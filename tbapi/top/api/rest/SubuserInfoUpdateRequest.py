'''
Created by auto_sdk on 2013-04-01 16:44:41
'''
from top.api.base import RestApi
class SubuserInfoUpdateRequest(RestApi):
	def __init__(self,domain='gw.api.taobao.com',port=80):
		RestApi.__init__(self,domain, port)
		self.is_disable_subaccount = None
		self.is_dispatch = None
		self.sub_id = None

	def getapiname(self):
		return 'taobao.subuser.info.update'
