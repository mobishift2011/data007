'''
Created by auto_sdk on 2013-04-01 16:44:41
'''
from top.api.base import RestApi
class RefundRefuseRequest(RestApi):
	def __init__(self,domain='gw.api.taobao.com',port=80):
		RestApi.__init__(self,domain, port)
		self.oid = None
		self.refund_id = None
		self.refuse_message = None
		self.refuse_proof = None
		self.tid = None

	def getapiname(self):
		return 'taobao.refund.refuse'

	def getMultipartParas(self):
		return ['refuse_proof']
