'''
Created by auto_sdk on 2013-04-01 16:44:41
'''
from top.api.base import RestApi
class PictureCategoryGetRequest(RestApi):
	def __init__(self,domain='gw.api.taobao.com',port=80):
		RestApi.__init__(self,domain, port)
		self.modified_time = None
		self.parent_id = None
		self.picture_category_id = None
		self.picture_category_name = None
		self.type = None

	def getapiname(self):
		return 'taobao.picture.category.get'
