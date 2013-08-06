'''
Created by auto_sdk on 2013-04-01 16:44:41
'''
from top.api.base import RestApi
class SubuserDepartmentUpdateRequest(RestApi):
	def __init__(self,domain='gw.api.taobao.com',port=80):
		RestApi.__init__(self,domain, port)
		self.department_id = None
		self.department_name = None
		self.parent_id = None
		self.user_nick = None

	def getapiname(self):
		return 'taobao.subuser.department.update'
