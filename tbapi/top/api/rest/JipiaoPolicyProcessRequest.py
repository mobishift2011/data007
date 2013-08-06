'''
Created by auto_sdk on 2013-04-01 16:44:41
'''
from top.api.base import RestApi
class JipiaoPolicyProcessRequest(RestApi):
	def __init__(self,domain='gw.api.taobao.com',port=80):
		RestApi.__init__(self,domain, port)
		self.airline = None
		self.arr_airports = None
		self.attributes = None
		self.auto_hk_flag = None
		self.auto_ticket_flag = None
		self.cabin_rules = None
		self.change_rule = None
		self.day_of_weeks = None
		self.dep_airports = None
		self.ei = None
		self.exclude_date = None
		self.first_sale_advance_day = None
		self.flags = None
		self.flight_info = None
		self.last_sale_advance_day = None
		self.memo = None
		self.office_id = None
		self.out_product_id = None
		self.policy_id = None
		self.policy_type = None
		self.refund_rule = None
		self.reissue_rule = None
		self.sale_end_date = None
		self.sale_start_date = None
		self.seat_info = None
		self.share_support = None
		self.special_rule = None
		self.travel_end_date = None
		self.travel_start_date = None
		self.type = None

	def getapiname(self):
		return 'taobao.jipiao.policy.process'
