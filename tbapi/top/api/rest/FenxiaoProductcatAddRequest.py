'''
Created by auto_sdk on 2013-04-01 16:44:41
'''
from top.api.base import RestApi
class FenxiaoProductcatAddRequest(RestApi):
	def __init__(self,domain='gw.api.taobao.com',port=80):
		RestApi.__init__(self,domain, port)
		self.agent_cost_percent = None
		self.dealer_cost_percent = None
		self.name = None
		self.retail_high_percent = None
		self.retail_low_percent = None

	def getapiname(self):
		return 'taobao.fenxiao.productcat.add'
