'''
Created by auto_sdk on 2013-04-01 16:44:41
'''
from top.api.base import RestApi
class HotelUpdateRequest(RestApi):
	def __init__(self,domain='gw.api.taobao.com',port=80):
		RestApi.__init__(self,domain, port)
		self.address = None
		self.city = None
		self.country = None
		self.decorate_time = None
		self.desc = None
		self.district = None
		self.domestic = None
		self.hid = None
		self.level = None
		self.name = None
		self.opening_time = None
		self.orientation = None
		self.pic = None
		self.province = None
		self.rooms = None
		self.service = None
		self.storeys = None
		self.tel = None

	def getapiname(self):
		return 'taobao.hotel.update'

	def getMultipartParas(self):
		return ['pic']
