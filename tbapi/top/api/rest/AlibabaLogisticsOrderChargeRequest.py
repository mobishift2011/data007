'''
Created by auto_sdk on 2013-04-01 16:44:41
'''
from top.api.base import RestApi
class AlibabaLogisticsOrderChargeRequest(RestApi):
	def __init__(self,domain='gw.api.taobao.com',port=80):
		RestApi.__init__(self,domain, port)
		self.cargo_description = None
		self.cargo_name = None
		self.pay_type = None
		self.route_code = None
		self.total_number = None
		self.total_volume = None
		self.total_weight = None
		self.vas_list = None

	def getapiname(self):
		return 'alibaba.logistics.order.charge'
