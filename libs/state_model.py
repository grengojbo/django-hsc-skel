#coding=utf8
from functools import wraps
import logging

import django
from django.db import models
from django.db.models.fields import FieldDoesNotExist
from django.db.models.fields.related import ReverseSingleRelatedObjectDescriptor

from django.db import router
from django.db.models.query import QuerySet

log = logging.getLogger(__name__)


def commit_changes(func):
	@wraps(func)
	def wrapper(inst, *args, **kwargs):
		commit = kwargs.pop('commit', True)
		using = kwargs.pop('using', None)
		result = func(inst, *args, **kwargs)
		if commit:
			inst.save(using)
		return result

	return wrapper


def update_changes(func):
	@wraps(func)
	def wrapper(inst, *args, **kwargs):
		commit = kwargs.pop('commit', True)
		using = kwargs.pop('using', None)
		changes = func(inst, *args, **kwargs)
		if commit:
			inst.__class__.objects.filter(pk=inst.pk).update(**changes)
		return changes

	return wrapper


class ImmutableModel(models.Model):
	'''
	Наследники этой модели нельзя сохранять через метод save
	Можно только создавать объекты методом create
	Для обновления используется метод save_changes
	'''
	class Meta:
		abstract = True

	def save_changes(self, using=None):
		self.save_base(using=using, force_insert=False, force_update=True)

	def save(self, force_insert=False, force_update=False, using=None):
		if force_insert and not force_update:
			# Используется для сохранения после create
			return super(ImmutableModel, self).save(force_insert, force_update, using)
		else:
			raise Exception('Don`t use manual saving for %s model instances' % self.__class__.__name__)

changed = django.dispatch.Signal(providing_args=["instance", "changes", "created"])
field_changed = django.dispatch.Signal(providing_args=["instance", "field_name", "old_value", "new_value", "created"])


class InitialValue(object):
	'''Начальное значение
	'''
	

class ReverseSingleRelatedObjectDescriptor(object):
	# This class provides the functionality that makes the related-object
	# managers available as attributes on a model class, for fields that have
	# a single "remote" value, on the class that defines the related field.
	# In the example "choice.poll", the poll attribute is a
	# ReverseSingleRelatedObjectDescriptor instance.
	def __init__(self, is_new=False):
		self._is_new = is_new

	def __get__(self, change_obj_instance, instance_type=None):
		
		if change_obj_instance is None:
			return self
		cache_name = change_obj_instance._field.get_cache_name()			
		if self._is_new:
			self._id = change_obj_instance._new_id
		else:
			self._id = change_obj_instance._old_id
			cache_name += '_old'
					 
		if self._id==InitialValue or not self._id:
			return None
			
		try:
			return getattr(change_obj_instance._instance, cache_name)
		except AttributeError:
			if self._id is None:
				# If NULL is an allowed value, return it.
				if change_obj_instance._field.null:
					return None
				raise change_obj_instance._field.rel.to.DoesNotExist
			other_field = change_obj_instance._field.rel.get_related_field()
			if other_field.rel:
				params = {'%s__pk' % change_obj_instance._field.rel.field_name: self._id}
			else:
				params = {'%s__exact' % change_obj_instance._field.rel.field_name: self._id}

			# If the related manager indicates that it should be used for
			# related fields, respect that.
			rel_mgr = change_obj_instance._field.rel.to._default_manager
			db = router.db_for_read(change_obj_instance._field.rel.to, instance=change_obj_instance._instance)
			if getattr(rel_mgr, 'use_for_related_fields', False):
				rel_obj = rel_mgr.using(db).get(**params)
			else:
				rel_obj = QuerySet(change_obj_instance._field.rel.to).using(db).get(**params)
			setattr(change_obj_instance._instance, cache_name, rel_obj)					
			return rel_obj
	
		
class Changes(object):
	'''Раньше изменения были tuple(old, new),
	теперт это свой объект со своим интерфейсом.
	'''
	def __init__(self, old, new):
		self.old = old
		self.new = new
	
	def __getitem__(self, item):
		if item == 0 or item == 'old':
			return self.old
		elif item == 1 or item == 'new':
			return self.new
		raise KeyError('No key %s', item)

	def __repr__(self):
		return '({0}, {1})'.format(self.old, self.new)
	
	
	
	__str__ = __repr__
	
	
class ChnagesFK(Changes):
	'''Запросы будут в базу идти только когда обращаешься к 
	changes['old'] или к changes.new
	'''
	old = ReverseSingleRelatedObjectDescriptor()
	new = ReverseSingleRelatedObjectDescriptor(is_new=True)

	def __init__(self, instance, field, old_id, new_id):
		self._instance = instance
		self._field = field
		self._old_id = old_id 
		self._new_id = new_id
			
	def __repr__(self):
		return 'Lazy({0}, {1})'.format(self._old_id, self._new_id)
	
	__str__ = __repr__


class StateSavingModel(models.Model):
	"""A model which can track it's changes.

	A dict of changed fields is available via `changes` property.
	"""
	# Note: unfortunately Django doesn't allow extending the Meta
	# class, so we're forced to define this on the model level.
	exclude = ()  # exclude these fields when comparing state
	only_fields = ()  # look only at these fields when comparing state, ignore others 
	always_save = False

	class Meta:
		abstract = True

	@classmethod
	def state_tracked_fields(cls):
		for field in cls._meta.fields:
			if cls.only_fields and field.name not in cls.only_fields:
				continue
			if cls.exclude and field.name in cls.exclude:
				continue
			if bool(field.rel):
				yield ''.join((field.name,'_id')), field
			else:
				yield field.name, field

	def save_state(self):
		self._initial_state = {}
		if not self.pk:
			for field_name, field in self.state_tracked_fields():
				self._initial_state[field_name] = InitialValue
		else:
			for field_name, field in self.state_tracked_fields():
				self._initial_state[field_name] = getattr(self, field_name)

	def reset_state(self, keep_fields=None):
		"""Resets instance to initial state
		@param keep_fields - list of field names whitch must be keeped in current state
		
		"""
		if not self._initial_state:
			return
		keep_fields = keep_fields or []
		for field_name in (field_name for field_name, field in self.state_tracked_fields() if field_name not in keep_fields):
			setattr(self, field_name, self._initial_state.get(field_name))

	@property
	def changes(self):
		"""Generates a dict of field changes since loaded from the database.
		
		Returns a mapping of field names to (old, new) value pairs:
		
		>>> profile.changes
		{'user': (<User: boris>, <User: iggy>)}
		"""
		changes = {}
		if not self._initial_state:
			return changes  # No initial instance? Nothing to compare to.

		for field_name, field in self.state_tracked_fields():
			new = self.__dict__.get(field_name) or getattr(self, field_name)
			old = self._initial_state.get(field_name)
			if old != new:
				if bool(field.rel):
					changes[field_name] = Changes(old, new)
					field_without_id = field.name
					changes[field_without_id] = ChnagesFK(self, self._meta.get_field_by_name(field_without_id)[0], old, new)
				else:
					changes[field_name] = Changes(old, new)
		return changes

	@classmethod
	def sender_field(cls, field_name):
		l = list([str(field_name) for field_name, field in cls.state_tracked_fields()]) 
		assert str(field_name) in l, 'Field \'%s\' state not treacked or not exist in %s' % (field_name, str(l))
		return cls._meta.get_field(field_name)

	def __init__(self, *args, **kwargs):
		"""Constructor.
		
		Saves a copy of the original model, to check an instance for
		differences later on.
		"""
		super(StateSavingModel, self).__init__(*args, **kwargs)
		self.save_state()

	def save(self, force_insert=False, force_update=False, using=None):
		changes = self.changes
		if changes and not self.exclude and not self.only_fields:
			super(StateSavingModel, self).save(force_insert, force_update, using)
		elif self.exclude or self.only_fields or self.always_save:
			super(StateSavingModel, self).save(force_insert, force_update, using)
		else:
			log.debug('Nothing changes in %s', self.__class__)
		if changes:
			for field_name, changed_obj in changes.items():
				new_value = changed_obj.new
				old_value = changed_obj.old
				try:
					sender = self.sender_field(field_name)
				except FieldDoesNotExist:
					pass # don't send a signal
				else:
					field_changed.send(sender, instance=self, field_name=field_name,
									   old_value=old_value, new_value=new_value, created=not self.pk)
			changed.send(self.__class__, instance=self, changes=changes, created=not self.pk)
			self.save_state()
			
	def save_changes(self, using=None):
		# TODO: make update query with only changed values
		self.save_base(using=using, force_insert=False, force_update=True)
