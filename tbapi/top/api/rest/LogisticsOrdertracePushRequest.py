'''
Created by auto_sdk on 2013-04-01 16:44:41
'''
from top.api.base import RestApi
class LogisticsOrdertracePushRequest(RestApi):
	def __init__(self,domain='gw.api.taobao.com',port=80):
		RestApi.__init__(self,domain, port)
		self.company_name = None
		self.current_city = None
		self.facility_name = None
		self.mail_no = None
		self.next_city = None
		self.node_description = None
		self.occure_time = None
		self.operate_detail = None
		self.operator_contact = None
		self.operator_name = None

	def getapiname(self):
		return 'taobao.logistics.ordertrace.push'
