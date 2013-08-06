'''
Created by auto_sdk on 2013-04-01 16:44:41
'''
from top.api.base import RestApi
class SimbaToolsItemsTopGetRequest(RestApi):
	def __init__(self,domain='gw.api.taobao.com',port=80):
		RestApi.__init__(self,domain, port)
		self.ip = None
		self.keyword = None
		self.nick = None

	def getapiname(self):
		return 'taobao.simba.tools.items.top.get'
