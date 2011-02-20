#coding=utf8

import logging
from django.db import models
from django.core.cache import cache

log = logging.getLogger(__name__)


def cached_property(f):
	"""Кешированный property для класса
	"""
	def get(self):
		try:
			return self._property_cache[f]
		except AttributeError:
			self._property_cache = {}
			x = self._property_cache[f] = f(self)
			return x
		except KeyError:
			x = self._property_cache[f] = f(self)
			return x

	return property(get)


class CachedQuerySet(models.query.QuerySet):
	'''Кешированный QuerySet который берет объекты из кеша
	(если они там имеются). Для его использования надо в кешируемой модели
	в аттрибуте 'cached_attrs' указать какие поля кешируется.
	Если cached_attrs не указан, то модель кешируется только по id.
	
	Позволяется добавить '__iexact' к названию поля что бы указать, что оно регистронезависимо.	
	Тут есть побочный эффект:
		если в базе есть две записи в одной модели name='Петя' и name='петя', и в самой модели
		указано свойство cached_attrs=['name__iexact'] то будет возвращаться тот объект,
		который первым был занесен в кеш.	
	'''	
	def __init__(self, model=None, query=None, using=None):
		super(CachedQuerySet, self).__init__(model, query, using)
		self.cached_attrs = getattr(self.model, 'cached_attrs', []) 
		if 'id' not in self.cached_attrs:
			self.cached_attrs.append('id')
		self.cached_attrs = [self._normalize_attr(attr) for attr in self.cached_attrs]

	def _normalize_attr(self, attr):
		return attr if '__' in attr else '%s__exact' % attr

	def _gen_cache_key(self, attr, value):
		if attr.endswith('__iexact'):
			value = value.lower()
		return '%s.%s.%s.%s' % (self.model.__module__, self.model.__name__, attr, value)

	def insert_to_cache(self, obj):
		for attr in self.cached_attrs:
			field, _filter = attr.split('__')
			value = getattr(obj, field)
			key = self._gen_cache_key(attr, value)
			if attr == 'id__exact':
				log.debug('Set to cache: %s', key)
			cache.set(key, obj)

	def delete_from_cache(self, obj):
		for attr in self.cached_attrs:
			field, _filter = attr.split('__')
			value = getattr(obj, field)
			key = self._gen_cache_key(attr, value)
			if attr == 'id__exact':
				log.debug('Delete from cache: %s', key)
			cache.delete(key)

	def get(self, *args, **kwargs):
		if len(kwargs) == 1:
			attr, value = kwargs.items()[0]
			attr = self._normalize_attr(attr)
			if attr in self.cached_attrs:
				key = self._gen_cache_key(attr, value)
				try:
					log.debug('Get from cache: %s', key)
					cached_result = cache.get(key)
					if not cached_result: raise KeyError
				except KeyError:
					log.debug('\tNot found!')
					obj = super(CachedQuerySet, self).get(*args, **kwargs)
					self.insert_to_cache(obj)
					return obj

		return super(CachedQuerySet, self).get(*args, **kwargs)

	
class CachedManager(models.Manager):
	'''Добавьте к своей модели аттрибуты
	cached_attrs = ['some_field_1', 'some_field_2__iexact', ...]
	objects = CachedManager()
	и ваша модель будет кешироваться по этим полям.
	
	Не забудьте выполнять
	self.__class__.objects.all().insert_to_cache(self)
	и
	self.__class__.objects.all().delete_from_cache(self)
	что бы занести модель и в кеш и удалить ее из кеша.
	'''	
	use_for_related_fields = True

	def get_query_set(self):
		return CachedQuerySet(self.model, using=self._db)
	

class CachedModel(models.Model):
	'''Наследуйтесь от этой модели, определите аттрибут cached_attrs
	и ваша модель станет кешируемой.
	'''
	objects = CachedManager()

	def save(self, force_insert=False, force_update=False, using=None):
		super(CachedModel, self).save(force_insert, force_update, using)
		self.__class__.objects.all().insert_to_cache(self)

	def delete(self, using=None):
		self.__class__.objects.all().delete_from_cache(self)
		super(CachedModel, self).delete(using)

	class Meta:
		abstract = True