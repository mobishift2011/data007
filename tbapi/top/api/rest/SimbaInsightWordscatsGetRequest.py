'''
Created by auto_sdk on 2013-04-01 16:44:41
'''
from top.api.base import RestApi
class SimbaInsightWordscatsGetRequest(RestApi):
	def __init__(self,domain='gw.api.taobao.com',port=80):
		RestApi.__init__(self,domain, port)
		self.filter = None
		self.nick = None
		self.word_categories = None

	def getapiname(self):
		return 'taobao.simba.insight.wordscats.get'
