'''
Created by auto_sdk on 2013-04-01 16:44:41
'''
from top.api.base import RestApi
class SubuserEmployeeUpdateRequest(RestApi):
	def __init__(self,domain='gw.api.taobao.com',port=80):
		RestApi.__init__(self,domain, port)
		self.department_id = None
		self.duty_id = None
		self.employee_name = None
		self.employee_nickname = None
		self.employee_num = None
		self.employee_turnover = None
		self.entry_date = None
		self.id_card_num = None
		self.leader_id = None
		self.office_phone = None
		self.personal_email = None
		self.personal_mobile = None
		self.sex = None
		self.sub_id = None
		self.work_location = None

	def getapiname(self):
		return 'taobao.subuser.employee.update'
