'''
Created by auto_sdk on 2013-04-01 16:44:41
'''
from top.api.base import RestApi
class FenxiaoProductUpdateRequest(RestApi):
	def __init__(self,domain='gw.api.taobao.com',port=80):
		RestApi.__init__(self,domain, port)
		self.alarm_number = None
		self.category_id = None
		self.city = None
		self.cost_price = None
		self.dealer_cost_price = None
		self.desc = None
		self.discount_id = None
		self.have_guarantee = None
		self.have_invoice = None
		self.image = None
		self.input_properties = None
		self.is_authz = None
		self.name = None
		self.outer_id = None
		self.pic_path = None
		self.pid = None
		self.postage_ems = None
		self.postage_fast = None
		self.postage_id = None
		self.postage_ordinary = None
		self.postage_type = None
		self.properties = None
		self.property_alias = None
		self.prov = None
		self.quantity = None
		self.retail_price_high = None
		self.retail_price_low = None
		self.sku_cost_prices = None
		self.sku_dealer_cost_prices = None
		self.sku_ids = None
		self.sku_outer_ids = None
		self.sku_properties = None
		self.sku_properties_del = None
		self.sku_quantitys = None
		self.sku_standard_prices = None
		self.standard_price = None
		self.status = None

	def getapiname(self):
		return 'taobao.fenxiao.product.update'

	def getMultipartParas(self):
		return ['image']
