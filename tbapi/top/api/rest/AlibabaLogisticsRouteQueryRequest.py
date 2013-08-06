'''
Created by auto_sdk on 2013-04-01 16:44:41
'''
from top.api.base import RestApi
class AlibabaLogisticsRouteQueryRequest(RestApi):
	def __init__(self,domain='gw.api.taobao.com',port=80):
		RestApi.__init__(self,domain, port)
		self.air_transport = None
		self.corp_list = None
		self.end_area_id = None
		self.merge_route = None
		self.page_index = None
		self.page_size = None
		self.show_cods = None
		self.show_specials = None
		self.show_statistics_info = None
		self.sort_type = None
		self.source = None
		self.start_area_id = None
		self.summary_total_corps = None
		self.summery_by_corp = None
		self.turn_level = None

	def getapiname(self):
		return 'alibaba.logistics.route.query'
