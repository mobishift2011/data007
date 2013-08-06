'''
Created by auto_sdk on 2013-04-01 16:44:41
'''
from top.api.base import RestApi
class WlbOrderScheduleRuleUpdateRequest(RestApi):
	def __init__(self,domain='gw.api.taobao.com',port=80):
		RestApi.__init__(self,domain, port)
		self.backup_store_id = None
		self.default_store_id = None
		self.option = None
		self.prov_area_ids = None
		self.schedule_rule_id = None

	def getapiname(self):
		return 'taobao.wlb.order.schedule.rule.update'
