'''
Created by auto_sdk on 2013-04-01 16:44:41
'''
from top.api.base import RestApi
class ItemUpdateRequest(RestApi):
	def __init__(self,domain='gw.api.taobao.com',port=80):
		RestApi.__init__(self,domain, port)
		self.after_sale_id = None
		self.approve_status = None
		self.auction_point = None
		self.auto_fill = None
		self.cid = None
		self.cod_postage_id = None
		self.desc = None
		self.empty_fields = None
		self.ems_fee = None
		self.express_fee = None
		self.food_security.contact = None
		self.food_security.design_code = None
		self.food_security.factory = None
		self.food_security.factory_site = None
		self.food_security.food_additive = None
		self.food_security.mix = None
		self.food_security.period = None
		self.food_security.plan_storage = None
		self.food_security.prd_license_no = None
		self.food_security.product_date_end = None
		self.food_security.product_date_start = None
		self.food_security.stock_date_end = None
		self.food_security.stock_date_start = None
		self.food_security.supplier = None
		self.freight_payer = None
		self.global_stock_type = None
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
		self.item_size = None
		self.item_weight = None
		self.lang = None
		self.list_time = None
		self.locality_life.choose_logis = None
		self.locality_life.expirydate = None
		self.locality_life.merchant = None
		self.locality_life.network_id = None
		self.locality_life.onsale_auto_refund_ratio = None
		self.locality_life.refund_ratio = None
		self.locality_life.verification = None
		self.location.city = None
		self.location.state = None
		self.num = None
		self.num_iid = None
		self.outer_id = None
		self.paimai_info.deposit = None
		self.paimai_info.interval = None
		self.paimai_info.mode = None
		self.paimai_info.reserve = None
		self.paimai_info.valid_hour = None
		self.paimai_info.valid_minute = None
		self.pic_path = None
		self.post_fee = None
		self.postage_id = None
		self.price = None
		self.product_id = None
		self.property_alias = None
		self.props = None
		self.scenic_ticket_book_cost = None
		self.scenic_ticket_pay_way = None
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
		return 'taobao.item.update'

	def getMultipartParas(self):
		return ['image']
