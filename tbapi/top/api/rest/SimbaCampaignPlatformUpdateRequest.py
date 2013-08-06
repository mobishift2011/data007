'''
Created by auto_sdk on 2013-04-01 16:44:41
'''
from top.api.base import RestApi
class SimbaCampaignPlatformUpdateRequest(RestApi):
	def __init__(self,domain='gw.api.taobao.com',port=80):
		RestApi.__init__(self,domain, port)
		self.campaign_id = None
		self.nick = None
		self.nonsearch_channels = None
		self.outside_discount = None
		self.search_channels = None

	def getapiname(self):
		return 'taobao.simba.campaign.platform.update'
