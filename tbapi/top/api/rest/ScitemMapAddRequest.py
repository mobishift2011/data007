'''
Created by auto_sdk on 2013-04-01 16:44:41
'''
from top.api.base import RestApi
class ScitemMapAddRequest(RestApi):
	def __init__(self,domain='gw.api.taobao.com',port=80):
		RestApi.__init__(self,domain, port)
		self.item_id = None
		self.need_check = None
		self.outer_code = None
		self.sc_item_id = None
		self.sku_id = None

	def getapiname(self):
		return 'taobao.scitem.map.add'
