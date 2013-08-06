'''
Created by auto_sdk on 2013-04-01 16:44:41
'''
from top.api.base import RestApi
class FenxiaoProductGradepriceUpdateRequest(RestApi):
	def __init__(self,domain='gw.api.taobao.com',port=80):
		RestApi.__init__(self,domain, port)
		self.ids = None
		self.prices = None
		self.product_id = None
		self.sku_id = None
		self.target_type = None
		self.trade_type = None

	def getapiname(self):
		return 'taobao.fenxiao.product.gradeprice.update'
