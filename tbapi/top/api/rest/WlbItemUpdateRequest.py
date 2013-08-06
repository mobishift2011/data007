'''
Created by auto_sdk on 2013-04-01 16:44:41
'''
from top.api.base import RestApi
class WlbItemUpdateRequest(RestApi):
	def __init__(self,domain='gw.api.taobao.com',port=80):
		RestApi.__init__(self,domain, port)
		self.color = None
		self.delete_property_key_list = None
		self.goods_cat = None
		self.height = None
		self.id = None
		self.is_dangerous = None
		self.is_friable = None
		self.length = None
		self.name = None
		self.package_material = None
		self.pricing_cat = None
		self.remark = None
		self.title = None
		self.update_property_key_list = None
		self.update_property_value_list = None
		self.volume = None
		self.weight = None
		self.width = None

	def getapiname(self):
		return 'taobao.wlb.item.update'
