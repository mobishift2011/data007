'''
Created by auto_sdk on 2013-04-01 16:44:41
'''
from top.api.base import RestApi
class TaobaokeListurlGetRequest(RestApi):
	def __init__(self,domain='gw.api.taobao.com',port=80):
		RestApi.__init__(self,domain, port)
		self.nick = None
		self.outer_code = None
		self.pid = None
		self.q = None

	def getapiname(self):
		return 'taobao.taobaoke.listurl.get'
