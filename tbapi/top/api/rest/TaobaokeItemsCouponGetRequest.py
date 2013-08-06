'''
Created by auto_sdk on 2013-04-01 16:44:41
'''
from top.api.base import RestApi
class TaobaokeItemsCouponGetRequest(RestApi):
	def __init__(self,domain='gw.api.taobao.com',port=80):
		RestApi.__init__(self,domain, port)
		self.area = None
		self.cid = None
		self.coupon_type = None
		self.end_commission_num = None
		self.end_commission_rate = None
		self.end_commission_volume = None
		self.end_coupon_rate = None
		self.end_credit = None
		self.end_volume = None
		self.fields = None
		self.is_mobile = None
		self.keyword = None
		self.nick = None
		self.outer_code = None
		self.page_no = None
		self.page_size = None
		self.pid = None
		self.shop_type = None
		self.sort = None
		self.start_commission_num = None
		self.start_commission_rate = None
		self.start_commission_volume = None
		self.start_coupon_rate = None
		self.start_credit = None
		self.start_volume = None

	def getapiname(self):
		return 'taobao.taobaoke.items.coupon.get'
