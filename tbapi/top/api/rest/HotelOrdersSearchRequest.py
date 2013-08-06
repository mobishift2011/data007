'''
Created by auto_sdk on 2013-04-01 16:44:41
'''
from top.api.base import RestApi
class HotelOrdersSearchRequest(RestApi):
	def __init__(self,domain='gw.api.taobao.com',port=80):
		RestApi.__init__(self,domain, port)
		self.checkin_date_end = None
		self.checkin_date_start = None
		self.checkout_date_end = None
		self.checkout_date_start = None
		self.created_end = None
		self.created_start = None
		self.gids = None
		self.hids = None
		self.need_guest = None
		self.need_message = None
		self.oids = None
		self.page_no = None
		self.rids = None
		self.status = None
		self.tids = None

	def getapiname(self):
		return 'taobao.hotel.orders.search'
