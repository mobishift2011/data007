'''
Created by auto_sdk on 2013-04-01 16:44:41
'''
from top.api.base import RestApi
class CaipiaoGoodsInfoInputRequest(RestApi):
	def __init__(self,domain='gw.api.taobao.com',port=80):
		RestApi.__init__(self,domain, port)
		self.act_end_date = None
		self.act_start_date = None
		self.goods_desc = None
		self.goods_id = None
		self.goods_image = None
		self.goods_price = None
		self.goods_title = None
		self.goods_type = None
		self.lottery_type_id = None
		self.present_type = None

	def getapiname(self):
		return 'taobao.caipiao.goods.info.input'
