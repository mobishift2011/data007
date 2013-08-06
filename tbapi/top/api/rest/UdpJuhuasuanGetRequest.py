'''
Created by auto_sdk on 2013-04-01 16:44:41
'''
from top.api.base import RestApi
class UdpJuhuasuanGetRequest(RestApi):
	def __init__(self,domain='gw.api.taobao.com',port=80):
		RestApi.__init__(self,domain, port)
		self.begin_time = None
		self.catid = None
		self.end_time = None
		self.fields = None
		self.itemid = None
		self.parameters = None

	def getapiname(self):
		return 'taobao.udp.juhuasuan.get'
