'''
Created by auto_sdk on 2013-04-01 16:44:41
'''
from top.api.base import RestApi
class FenxiaoCooperationGetRequest(RestApi):
	def __init__(self,domain='gw.api.taobao.com',port=80):
		RestApi.__init__(self,domain, port)
		self.end_date = None
		self.page_no = None
		self.page_size = None
		self.start_date = None
		self.status = None
		self.trade_type = None

	def getapiname(self):
		return 'taobao.fenxiao.cooperation.get'
