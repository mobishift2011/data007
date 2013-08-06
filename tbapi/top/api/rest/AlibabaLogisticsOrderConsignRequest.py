'''
Created by auto_sdk on 2013-04-01 16:44:41
'''
from top.api.base import RestApi
class AlibabaLogisticsOrderConsignRequest(RestApi):
	def __init__(self,domain='gw.api.taobao.com',port=80):
		RestApi.__init__(self,domain, port)
		self.cargo_description = None
		self.cargo_name = None
		self.order_id = None
		self.pay_type = None
		self.receiver_address = None
		self.receiver_area_id = None
		self.receiver_city_name = None
		self.receiver_corp_name = None
		self.receiver_county_name = None
		self.receiver_mobile = None
		self.receiver_name = None
		self.receiver_phone_area_code = None
		self.receiver_phone_tel = None
		self.receiver_phone_tel_ext = None
		self.receiver_postcode = None
		self.receiver_province_name = None
		self.receiver_wangwang_no = None
		self.refunder_address = None
		self.refunder_area_id = None
		self.refunder_city_name = None
		self.refunder_corp_name = None
		self.refunder_county_name = None
		self.refunder_mobile = None
		self.refunder_name = None
		self.refunder_phone_area_code = None
		self.refunder_phone_tel = None
		self.refunder_phone_tel_ext = None
		self.refunder_postcode = None
		self.refunder_province_name = None
		self.refunder_wangwang_no = None
		self.remark = None
		self.route_code = None
		self.sender_address = None
		self.sender_area_id = None
		self.sender_city_name = None
		self.sender_corp_name = None
		self.sender_county_name = None
		self.sender_mobile = None
		self.sender_name = None
		self.sender_phone_area_code = None
		self.sender_phone_tel = None
		self.sender_phone_tel_ext = None
		self.sender_postcode = None
		self.sender_province_name = None
		self.sender_wangwang_no = None
		self.source = None
		self.total_number = None
		self.total_volume = None
		self.total_weight = None
		self.vas_list = None

	def getapiname(self):
		return 'alibaba.logistics.order.consign'
