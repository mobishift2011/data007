'''
Created by auto_sdk on 2013-04-01 16:44:41
'''
from top.api.base import RestApi
class SimbaRptAdgroupnonsearcheffectGetRequest(RestApi):
	def __init__(self,domain='gw.api.taobao.com',port=80):
		RestApi.__init__(self,domain, port)
		self.adgroup_id = None
		self.campaign_id = None
		self.end_time = None
		self.nick = None
		self.page_no = None
		self.page_size = None
		self.start_time = None
		self.subway_token = None

	def getapiname(self):
		return 'taobao.simba.rpt.adgroupnonsearcheffect.get'
