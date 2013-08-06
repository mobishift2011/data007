'''
Created by auto_sdk on 2013-04-01 16:44:41
'''
from top.api.base import RestApi
class FenxiaoProductMapAddRequest(RestApi):
	def __init__(self,domain='gw.api.taobao.com',port=80):
		RestApi.__init__(self,domain, port)
		self.not_check_outer_code = None
		self.product_id = None
		self.sc_item_id = None
		self.sc_item_ids = None
		self.sku_ids = None

	def getapiname(self):
		return 'taobao.fenxiao.product.map.add'
