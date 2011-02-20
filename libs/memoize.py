#coding=utf-8
#--- Author: Dmitri Patrakov <traditio@gmail.com>
from functools import partial

class memoize_instance_method(object):
	"""cache the return value of a method

	This class is meant to be used as a decorator of methods. The return value
	from a given method invocation will be cached on the instance whose method
	was invoked. All arguments passed to a method decorated with memoize must
	be hashable.
	"""

	def __init__(self, func):
		self.func = func

	def __get__(self, obj, objtype=None):
		if bool(obj) is False:
			raise Exception, 'Cannot memoize non-instance method'
		return partial(self, obj)

	def __call__(self, *args, **kw):
		obj = args[0]
		try:
			cache = obj.__cache
		except AttributeError:
			cache = obj.__cache = {}
		key = (self.func, args[1:], frozenset(kw.items()))
		try:
			res = cache[key]
		except KeyError:
			res = cache[key] = self.func(*args, **kw)
		return res


if __name__ == "__main__":
	# example usage
	class Test(object):
		v = 0

		@memoize_instance_method
		def inc_add(self, arg):
			self.v += 1
			return self.v + arg

	t = Test()
	assert t.inc_add(2) == t.inc_add(2)