'''
Created by auto_sdk on 2013-04-01 16:44:41
'''
from top.api.base import RestApi
class HotelRoomUpdateRequest(RestApi):
	def __init__(self,domain='gw.api.taobao.com',port=80):
		RestApi.__init__(self,domain, port)
		self.area = None
		self.bbn = None
		self.bed_type = None
		self.breakfast = None
		self.deposit = None
		self.desc = None
		self.fee = None
		self.gid = None
		self.guide = None
		self.has_receipt = None
		self.multi_room_quotas = None
		self.payment_type = None
		self.pic = None
		self.pic_path = None
		self.price_type = None
		self.receipt_info = None
		self.receipt_other_type_desc = None
		self.receipt_type = None
		self.room_quotas = None
		self.service = None
		self.site_param = None
		self.size = None
		self.status = None
		self.storey = None
		self.title = None

	def getapiname(self):
		return 'taobao.hotel.room.update'

	def getMultipartParas(self):
		return ['pic']
