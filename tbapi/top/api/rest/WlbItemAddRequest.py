'''
Created by auto_sdk on 2013-04-01 16:44:41
'''
from top.api.base import RestApi
class WlbItemAddRequest(RestApi):
	def __init__(self,domain='gw.api.taobao.com',port=80):
		RestApi.__init__(self,domain, port)
		self.color = None
		self.goods_cat = None
		self.height = None
		self.is_dangerous = None
		self.is_friable = None
		self.is_sku = None
		self.item_code = None
		self.length = None
		self.name = None
		self.package_material = None
		self.price = None
		self.pricing_cat = None
		self.pro_name_list = None
		self.pro_value_list = None
		self.remark = None
		self.support_batch = None
		self.title = None
		self.type = None
		self.volume = None
		self.weight = None
		self.width = None

	def getapiname(self):
		return 'taobao.wlb.item.add'
