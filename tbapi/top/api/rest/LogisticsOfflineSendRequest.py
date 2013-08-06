'''
Created by auto_sdk on 2013-04-01 16:44:41
'''
from top.api.base import RestApi
class LogisticsOfflineSendRequest(RestApi):
	def __init__(self,domain='gw.api.taobao.com',port=80):
		RestApi.__init__(self,domain, port)
		self.cancel_id = None
		self.company_code = None
		self.feature = None
		self.out_sid = None
		self.seller_ip = None
		self.sender_id = None
		self.tid = None

	def getapiname(self):
		return 'taobao.logistics.offline.send'
