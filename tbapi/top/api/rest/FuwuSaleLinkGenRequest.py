'''
Created by auto_sdk on 2013-04-01 16:44:41
'''
from top.api.base import RestApi
class FuwuSaleLinkGenRequest(RestApi):
	def __init__(self,domain='gw.api.taobao.com',port=80):
		RestApi.__init__(self,domain, port)
		self.nick = None
		self.param_str = None

	def getapiname(self):
		return 'taobao.fuwu.sale.link.gen'
