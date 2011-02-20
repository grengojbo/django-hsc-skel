#coding=utf-8
#--- Author: Dmitri Patrakov <traditio@gmail.com>
# http://djangosnippets.org/snippets/1647/

class Enumeration(object):
	"""
	A small helper class for more readable enumerations,
	and compatible with Django's choice convention.
	You may just pass the instance of this class as the choices
	argument of model/form fields.

	Example:
			MY_ENUM = Enumeration([
				(100, 'MY_NAME', 'My verbose name'),
				(200, 'MY_AGE', 'My verbose age'),
			])
		assert MY_ENUM.MY_AGE == 100
		assert MY_ENUM[1] == (200, 'My verbose age')
	"""

	def __init__(self, enum_list):
		self.enum_list = [(item[0], item[2]) for item in enum_list]
		self.enum_dict = {}
		for item in enum_list:
			self.enum_dict[item[1]] = item[0]

	def __contains__(self, v):
		return v in self.enum_list

	def __len__(self):
		return len(self.enum_list)

	def __getitem__(self, v):
		if isinstance(v, basestring):
			return self.enum_dict[v]
		elif isinstance(v, int):
			return self.enum_list[v]

	def __getattr__(self, name):
		return self.enum_dict[name]

	def __iter__(self):
		return self.enum_list.__iter__()
		
	def get_text_by_id(self, id):
		k,v = zip(*self.enum_dict.items())
		return dict(zip(v,k)).get(id, None)	