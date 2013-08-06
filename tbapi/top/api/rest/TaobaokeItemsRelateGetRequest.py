'''
Created by auto_sdk on 2013-04-01 16:44:41
'''
from top.api.base import RestApi
class TaobaokeItemsRelateGetRequest(RestApi):
	def __init__(self,domain='gw.api.taobao.com',port=80):
		RestApi.__init__(self,domain, port)
		self.cid = None
		self.fields = None
		self.is_mobile = None
		self.max_count = None
		self.nick = None
		self.num_iid = None
		self.outer_code = None
		self.pid = None
		self.relate_type = None
		self.seller_id = None
		self.shop_type = None
		self.sort = None
		self.track_iid = None

	def getapiname(self):
		return 'taobao.taobaoke.items.relate.get'
