'''
Created by auto_sdk on 2013-04-01 16:44:41
'''
from top.api.base import RestApi
class WlbOrderCreateRequest(RestApi):
	def __init__(self,domain='gw.api.taobao.com',port=80):
		RestApi.__init__(self,domain, port)
		self.alipay_no = None
		self.attributes = None
		self.buyer_nick = None
		self.expect_end_time = None
		self.expect_start_time = None
		self.invoince_info = None
		self.is_finished = None
		self.order_code = None
		self.order_flag = None
		self.order_item_list = None
		self.order_sub_type = None
		self.order_type = None
		self.out_biz_code = None
		self.package_count = None
		self.payable_amount = None
		self.prev_order_code = None
		self.receiver_info = None
		self.remark = None
		self.schedule_end = None
		self.schedule_start = None
		self.schedule_type = None
		self.sender_info = None
		self.service_fee = None
		self.store_code = None
		self.tms_info = None
		self.tms_order_code = None
		self.tms_service_code = None
		self.total_amount = None

	def getapiname(self):
		return 'taobao.wlb.order.create'
