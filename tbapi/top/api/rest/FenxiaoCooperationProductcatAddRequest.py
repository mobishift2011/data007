'''
Created by auto_sdk on 2013-04-01 16:44:41
'''
from top.api.base import RestApi
class FenxiaoCooperationProductcatAddRequest(RestApi):
	def __init__(self,domain='gw.api.taobao.com',port=80):
		RestApi.__init__(self,domain, port)
		self.cooperate_id = None
		self.grade_id = None
		self.product_line_list = None

	def getapiname(self):
		return 'taobao.fenxiao.cooperation.productcat.add'
