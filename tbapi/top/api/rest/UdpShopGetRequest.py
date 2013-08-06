'''
Created by auto_sdk on 2013-04-01 16:44:41
'''
from top.api.base import RestApi
class UdpShopGetRequest(RestApi):
	def __init__(self,domain='gw.api.taobao.com',port=80):
		RestApi.__init__(self,domain, port)
		self.area = None
		self.begin_time = None
		self.end_time = None
		self.fields = None
		self.parameters = None

	def getapiname(self):
		return 'taobao.udp.shop.get'
