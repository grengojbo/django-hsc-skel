#coding=utf-8
#--- Author: Dmitri Patrakov <traditio@gmail.com>
import logging
log = logging.getLogger(__name__)

from django.db import models
from django.core.cache import cache

from libs.shared.contracts import takes, optional, returns, list_of


def check_field_name_for_autocomplete(field_name):
	if len(field_name.split('__'))>1:
		filter = field_name.split('__')[1]
		if not(filter=='startswith' or filter=='istartswith'):
			log.error('field_name')
			return False
			
	return True


@takes(basestring, optional(int), lim=optional(int))
def continuate_string_iterator(s, lim=None):
	'''for x in continuate_string_iterator(u'Олеся', lim=4) ->
	О
	Ол
	Оле
	Олес
	'''
	for i in xrange(1, len(s) + 1):
		if lim and i > lim: raise StopIteration
		yield s[:i]


class AutocompleteManager(models.Manager):	
	'''Менеджер для моделей с автокомплитом.
	Хранит в кеше сразу массив строк, который возвращается по запросу
	
	В модели вы обязательно должны укзаать аттрибут autocomplete_fields,
	который является списком из строк FIELD_NAME или FIELD_NAME__istartswith (регистронезависимый вариант).
	
	Опционально можете создать аттрибут autocomplete_limit который говорит о том, сколько строковых значений хранить в 
	кеше для каждого поля моделя.	
	'''
	@takes("AutocompleteManager", basestring)
	def _normalize_attr(self, attr):
		return attr if '__' in attr else '%s__startswith' % attr

	@takes("AutocompleteManager", basestring, basestring)
	def _gen_cache_key(self, attr, value):
		if attr.endswith('__istartswith'):
			value = value.lower()
		return '%s.%s.%s.%s' % (self.model.__module__, self.model.__name__, attr, value)

	@takes("AutocompleteManager", models.Model)
	def update(self, obj):
		'''Очистить кеш для данного объекта
		'''
		assert self.model
		autocomplete_fields = [self._normalize_attr(attr) for attr in getattr(self.model, 'autocomplete_fields')]
		assert autocomplete_fields 
		for field in autocomplete_fields:
			val = getattr(obj, field.split('__')[0])
			assert val, '{0} has no attr {1}'.format(obj.__class__, val)
			for value in continuate_string_iterator(val):
				key = self._gen_cache_key(field, value)
				cache.delete(key)

	@takes("AutocompleteManager",
		   (basestring, check_field_name_for_autocomplete),
		   basestring,
		   optional(int),
		   limit=optional(int))
	@returns(list_of(basestring))
	def find(self, field_name, q, limit=None):
		'''Для данной модели вернуть значения дла автокомплита из кеша
		для поля field_name

		Args:	
			field_name - строка FIELD_NAME (регистрозависимое) или FIELD_NAME__istartswith - регистронезависимая)
			q - одна или несколько первых букв, с которых должно начинаться слово для автокомплита 
		'''
		autocomplete_fields = getattr(self.model, 'autocomplete_fields')
		autocomplete_limit = getattr(self.model, 'autocomplete_limit', 150)
		autocomplete_fields = [self._normalize_attr(attr) for attr in autocomplete_fields]
		# если лимит > указанного в настройках модели, то вызываем Exception
		if limit and limit > autocomplete_limit: raise ValueError(
				'Указанный limit=%s > limit=%s из настроек модели', limit, autocomplete_limit)
		# если вообще limit не указан, то берем из настроек модели
		if not limit:
			limit = autocomplete_limit
		# строим ключ для field_name и q (query search)
		key = self._gen_cache_key(field_name, q)
		# ищем в кеше
		cached_result = cache.get(key)
		# если найдено, возвращаем массив строк с указанным лимитом
		if cached_result:
			log.debug('Get from cache key %s', key)
			return cached_result[:limit]
		# иначе
		else:
			# если field_name кончается на iexact то запрос будет field_name__istartswith
			# иначе запрос будет field_name___startswith
			query_filter = field_name.replace('exact', 'startswith')
			# делаем запрос в базу с указанным в настройках модели лимитом
			db_result = self.get_query_set().filter(**{query_filter: q}).all()
			assert field_name in autocomplete_fields
			result = []
			# проходимся по каждому autocomplete_fields
			for field in autocomplete_fields:				
				# заносим в кеш
				cached_result = [unicode(getattr(obj, field.split('__')[0])) for obj in db_result]				
				if cached_result:
					key = self._gen_cache_key(field, q)
					cache.set(key, cached_result)	
					log.debug('Set to cache key %s', key)
				# если оно наше (то есть запрошенное, то записываем как результат)
				if field==field_name:
					result=cached_result
			assert result
			# возвращаем массив строк с указанным лимитом
			return result[:limit]

		
class AutocompleteModel(models.Model):
	'''Наследуйтесь от этой модели, определите аттрибут autocomplete_fields и autocomplete_limit
	и ваша модель станет поддерживать кешируемый автокомплит по строковым полям
	'''
	autocomplete = AutocompleteManager()
	autocomplete_limit = 150

	def save(self, force_insert=False, force_update=False, using=None):
		super(AutocompleteModel, self).save(force_insert, force_update, using)
		self.__class__.autocomplete.update(self)

	def delete(self, using=None):
		self.__class__.autocomplete.update(self)
		super(AutocompleteModel, self).autocomplete.update(self)

	class Meta:
		abstract = True