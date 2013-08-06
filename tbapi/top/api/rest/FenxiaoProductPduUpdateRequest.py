'''
Created by auto_sdk on 2013-04-01 16:44:41
'''
from top.api.base import RestApi
class FenxiaoProductPduUpdateRequest(RestApi):
	def __init__(self,domain='gw.api.taobao.com',port=80):
		RestApi.__init__(self,domain, port)
		self.distributor_id = None
		self.is_delete = None
		self.product_id = None
		self.quantity_type = None
		self.quantitys = None
		self.sku_properties = None

	def getapiname(self):
		return 'taobao.fenxiao.product.pdu.update'
