'''
Created by auto_sdk on 2013-04-01 16:44:41
'''
from top.api.base import RestApi
class UmpActivitiesGetRequest(RestApi):
	def __init__(self,domain='gw.api.taobao.com',port=80):
		RestApi.__init__(self,domain, port)
		self.page_no = None
		self.page_size = None
		self.tool_id = None

	def getapiname(self):
		return 'taobao.ump.activities.get'
