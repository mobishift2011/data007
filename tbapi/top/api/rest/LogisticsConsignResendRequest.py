'''
Created by auto_sdk on 2013-04-01 16:44:41
'''
from top.api.base import RestApi
class LogisticsConsignResendRequest(RestApi):
	def __init__(self,domain='gw.api.taobao.com',port=80):
		RestApi.__init__(self,domain, port)
		self.company_code = None
		self.feature = None
		self.out_sid = None
		self.tid = None

	def getapiname(self):
		return 'taobao.logistics.consign.resend'
