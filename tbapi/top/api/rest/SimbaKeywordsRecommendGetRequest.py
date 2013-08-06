'''
Created by auto_sdk on 2013-04-01 16:44:41
'''
from top.api.base import RestApi
class SimbaKeywordsRecommendGetRequest(RestApi):
	def __init__(self,domain='gw.api.taobao.com',port=80):
		RestApi.__init__(self,domain, port)
		self.adgroup_id = None
		self.nick = None
		self.order_by = None
		self.page_no = None
		self.page_size = None
		self.pertinence = None
		self.search = None

	def getapiname(self):
		return 'taobao.simba.keywords.recommend.get'
