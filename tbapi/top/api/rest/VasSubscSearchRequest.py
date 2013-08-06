'''
Created by auto_sdk on 2013-04-01 16:44:41
'''
from top.api.base import RestApi
class VasSubscSearchRequest(RestApi):
	def __init__(self,domain='gw.api.taobao.com',port=80):
		RestApi.__init__(self,domain, port)
		self.article_code = None
		self.autosub = None
		self.end_deadline = None
		self.expire_notice = None
		self.item_code = None
		self.nick = None
		self.page_no = None
		self.page_size = None
		self.start_deadline = None
		self.status = None

	def getapiname(self):
		return 'taobao.vas.subsc.search'
