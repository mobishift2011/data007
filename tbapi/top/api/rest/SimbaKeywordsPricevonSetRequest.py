'''
Created by auto_sdk on 2013-04-01 16:44:41
'''
from top.api.base import RestApi
class SimbaKeywordsPricevonSetRequest(RestApi):
	def __init__(self,domain='gw.api.taobao.com',port=80):
		RestApi.__init__(self,domain, port)
		self.keywordid_prices = None
		self.nick = None

	def getapiname(self):
		return 'taobao.simba.keywords.pricevon.set'
