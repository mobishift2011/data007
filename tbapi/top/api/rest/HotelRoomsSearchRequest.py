'''
Created by auto_sdk on 2013-04-01 16:44:41
'''
from top.api.base import RestApi
class HotelRoomsSearchRequest(RestApi):
	def __init__(self,domain='gw.api.taobao.com',port=80):
		RestApi.__init__(self,domain, port)
		self.gids = None
		self.hids = None
		self.item_ids = None
		self.need_hotel = None
		self.need_room_desc = None
		self.need_room_quotas = None
		self.need_room_type = None
		self.page_no = None
		self.rids = None

	def getapiname(self):
		return 'taobao.hotel.rooms.search'
