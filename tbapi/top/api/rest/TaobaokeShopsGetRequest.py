'''
Created by auto_sdk on 2013-04-01 16:44:41
'''
from top.api.base import RestApi
class TaobaokeShopsGetRequest(RestApi):
	def __init__(self,domain='gw.api.taobao.com',port=80):
		RestApi.__init__(self,domain, port)
		self.cid = None
		self.end_auctioncount = None
		self.end_commissionrate = None
		self.end_credit = None
		self.end_totalaction = None
		self.fields = None
		self.is_mobile = None
		self.keyword = None
		self.nick = None
		self.only_mall = None
		self.outer_code = None
		self.page_no = None
		self.page_size = None
		self.pid = None
		self.sort_field = None
		self.sort_type = None
		self.start_auctioncount = None
		self.start_commissionrate = None
		self.start_credit = None
		self.start_totalaction = None

	def getapiname(self):
		return 'taobao.taobaoke.shops.get'
