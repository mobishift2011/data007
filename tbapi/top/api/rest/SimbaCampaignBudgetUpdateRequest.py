'''
Created by auto_sdk on 2013-04-01 16:44:41
'''
from top.api.base import RestApi
class SimbaCampaignBudgetUpdateRequest(RestApi):
	def __init__(self,domain='gw.api.taobao.com',port=80):
		RestApi.__init__(self,domain, port)
		self.budget = None
		self.campaign_id = None
		self.nick = None
		self.use_smooth = None

	def getapiname(self):
		return 'taobao.simba.campaign.budget.update'
