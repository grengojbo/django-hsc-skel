#coding=utf8
from functools import wraps
import logging
log = logging.getLogger(__name__)

import django
from django.db import models


def save_if_commit(func):
	'''Декоратор для сохраненения, что бы не писать в методе модели что-то вроде
	if commit: self.save()
	else: return
	'''
	@wraps(func)
	def wrapper(inst, *args, **kwargs):
		commit = kwargs.pop('commit', True)
		using = kwargs.pop('using', None)
		result = func(inst, *args, **kwargs)
		if commit:
			inst.save(using)
		return result

	return wrapper


def save_as_update(func):
	'''Декоратор для метода модели, сохраняющий ее методом update
	(save не вызывается, сигналы не срабатывают)
	'''
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


class lazy(object):
	'''lazy - decorator changes class method to lazy cached property
	'''
	def __init__(self, function):
		self._function = function

	def __get__(self, instance, owner=None):
		if instance is None:
			return self
		val = self._function(instance)
		setattr(instance, self._function.func_name, val)
		return val

	
class Changes(object):
	
	def __init__(self, old, new):
		self.old = old
		self.new = new
		super(Changes, self).__init__()

	def __iter__(self):
		yield self.old
		yield self.new

	def __repr__(self):
		return u'(%s, %s)' % (self.old, self.new)

	__str__ = __repr__

	
class RelatedChanges(Changes):
	
	def __init__(self, old_id, new_id, old_instance, new_instance, field):
		self.old_id = old_id
		self.new_id = new_id
		self._old_instance = old_instance
		self._new_instance = new_instance
		self._field = field

	@lazy
	def old(self):
		return getattr(self._old_instance, self._field.name)

	@lazy
	def new(self):
		return getattr(self._new_instance, self._field.name)

	def __repr__(self):
		return '(%s, %s)' % (self.old_id, self.new_id)

	__str__ = __repr__


class StateSavingModel(models.Model):
	"""A model which can track it's changes.

	A dict of changed fields is available via `changes` property.
	"""
	# Note: unfortunately Django doesn't allow extending the Meta
	# class, so we're forced to define this on the model level.
	state_ignore_fields = ()  # Fields to ignore when comparing state.
	state_store_fields = ()  # Fields

	class Meta:
		abstract = True

	@classmethod
	def state_tracked_fields(cls):
		for field in cls._meta.local_fields:
			if cls.state_store_fields and field.name not in cls.state_store_fields:
				continue
			if cls.state_ignore_fields and field.name in cls.state_ignore_fields:
				continue
			yield field

	def _as_dict(self):
		# http://stackoverflow.com/questions/110803/dirty-fields-in-django
		return dict((field.attname, getattr(self, field.attname)) for field in self.state_tracked_fields())

	def save_state(self):
		self._initial_state = self._as_dict()

	def reset_state(self, keep_fields=None):
		"""Resets instance to initial state
		@param keep_fields - list of field names whitch must be keeped in current state
		"""
		if not self._initial_state:
			return
		keep_fields = keep_fields or []
		for field in (field for field in self.state_tracked_fields() if field.name not in keep_fields):
			setattr(self, field.attname, self._initial_state.get(field.attname))
			if field.rel and hasattr(self, field.get_cache_name()):
				#clear cached value of related fields
				delattr(self, field.get_cache_name())

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

		for field in self.state_tracked_fields():
			new = field.get_prep_value(getattr(self, field.attname))
			old = field.get_prep_value(self._initial_state.get(field.attname))
			if old != new:
				if field.rel:
					# generate pseudo instance for old value
					old_instance = self.__class__()
					setattr(old_instance, field.attname, old)
					changes[field.name] = RelatedChanges(old, new, old_instance, self, field)
				else:
					changes[field.name] = Changes(old, new)
		return changes

	@classmethod
	def sender_field(cls, field_name):
		for field in cls.state_tracked_fields():
			if field.name == field_name:
				return field
		raise Exception('Field "%s" state not treacked or not exist' % field_name)

	def __init__(self, *args, **kwargs):
		"""Constructor.

		Saves a copy of the original model, to check an instance for
		differences later on.
		"""
		super(StateSavingModel, self).__init__(*args, **kwargs)
		self.save_state()

	def save(self, force_insert=False, force_update=False, using=None):
		super(StateSavingModel, self).save(force_insert, force_update, using)
		changes = self.changes
		if changes:			
			for field_name, (old_value, new_value) in changes.items():
				sender = self.sender_field(field_name)
				field_changed.send(sender, instance=self, field_name=field_name,
								   old_value=old_value, new_value=new_value, created=not self.pk)
			changed.send(self.__class__, instance=self, changes=changes, created=not self.pk)
			log.debug('model %s has changes %s, saved', self.changes, self.__class__.__name__)
		else:
			log.debug('model %s has no changes, wasnt saved', self.__class__.__name__)
		self.save_state()

	def save_changes(self, using=None):
		self.save_base(using=using, force_insert=False, force_update=True)
