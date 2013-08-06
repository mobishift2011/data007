'''
Created by auto_sdk on 2013-04-01 16:44:41
'''
from top.api.base import RestApi
class CaipiaoShopInfoInputRequest(RestApi):
	def __init__(self,domain='gw.api.taobao.com',port=80):
		RestApi.__init__(self,domain, port)
		self.act_end_date = None
		self.act_start_date = None
		self.present_type = None
		self.shop_desc = None
		self.shop_name = None
		self.shop_type = None

	def getapiname(self):
		return 'taobao.caipiao.shop.info.input'
