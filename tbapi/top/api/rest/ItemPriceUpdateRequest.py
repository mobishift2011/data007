'''
Created by auto_sdk on 2013-04-01 16:44:41
'''
from top.api.base import RestApi
class ItemPriceUpdateRequest(RestApi):
	def __init__(self,domain='gw.api.taobao.com',port=80):
		RestApi.__init__(self,domain, port)
		self.after_sale_id = None
		self.approve_status = None
		self.auction_point = None
		self.auto_fill = None
		self.cid = None
		self.cod_postage_id = None
		self.desc = None
		self.ems_fee = None
		self.express_fee = None
		self.freight_payer = None
		self.has_discount = None
		self.has_invoice = None
		self.has_showcase = None
		self.has_warranty = None
		self.image = None
		self.increment = None
		self.input_pids = None
		self.input_str = None
		self.is_3D = None
		self.is_ex = None
		self.is_lightning_consignment = None
		self.is_replace_sku = None
		self.is_taobao = None
		self.is_xinpin = None
		self.lang = None
		self.list_time = None
		self.location.city = None
		self.location.state = None
		self.num = None
		self.num_iid = None
		self.outer_id = None
		self.pic_path = None
		self.post_fee = None
		self.postage_id = None
		self.price = None
		self.product_id = None
		self.property_alias = None
		self.props = None
		self.sell_promise = None
		self.seller_cids = None
		self.sku_outer_ids = None
		self.sku_prices = None
		self.sku_properties = None
		self.sku_quantities = None
		self.stuff_status = None
		self.sub_stock = None
		self.title = None
		self.valid_thru = None
		self.weight = None

	def getapiname(self):
		return 'taobao.item.price.update'

	def getMultipartParas(self):
		return ['image']
