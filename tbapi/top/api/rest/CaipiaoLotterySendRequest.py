'''
Created by auto_sdk on 2013-04-01 16:44:41
'''
from top.api.base import RestApi
class CaipiaoLotterySendRequest(RestApi):
	def __init__(self,domain='gw.api.taobao.com',port=80):
		RestApi.__init__(self,domain, port)
		self.buyer_num_id = None
		self.lottery_type_id = None
		self.seller_num_id = None
		self.stake_count = None
		self.sweety_words = None

	def getapiname(self):
		return 'taobao.caipiao.lottery.send'
