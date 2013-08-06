'''
Created by auto_sdk on 2013-04-01 16:44:41
'''
from top.api.base import RestApi
class TradeConfirmfeeGetRequest(RestApi):
	def __init__(self,domain='gw.api.taobao.com',port=80):
		RestApi.__init__(self,domain, port)
		self.is_detail = None
		self.tid = None

	def getapiname(self):
		return 'taobao.trade.confirmfee.get'
