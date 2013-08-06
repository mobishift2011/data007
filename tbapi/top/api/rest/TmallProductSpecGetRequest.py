'''
Created by auto_sdk on 2013-04-01 16:44:41
'''
from top.api.base import RestApi
class TmallProductSpecGetRequest(RestApi):
	def __init__(self,domain='gw.api.taobao.com',port=80):
		RestApi.__init__(self,domain, port)
		self.spec_id = None

	def getapiname(self):
		return 'tmall.product.spec.get'
