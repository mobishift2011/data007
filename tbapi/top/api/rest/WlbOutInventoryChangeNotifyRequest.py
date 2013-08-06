'''
Created by auto_sdk on 2013-04-01 16:44:41
'''
from top.api.base import RestApi
class WlbOutInventoryChangeNotifyRequest(RestApi):
	def __init__(self,domain='gw.api.taobao.com',port=80):
		RestApi.__init__(self,domain, port)
		self.change_count = None
		self.item_id = None
		self.op_type = None
		self.order_source_code = None
		self.out_biz_code = None
		self.result_count = None
		self.source = None
		self.store_code = None
		self.type = None

	def getapiname(self):
		return 'taobao.wlb.out.inventory.change.notify'
