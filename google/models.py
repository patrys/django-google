from django.db import models
import atom
import gdata.calendar
import gdata.calendar.service
import gdata.service
import datetime
from managers import CalendarManager, EventManager

VERSION = '0.1'

_services = {}

class Account(models.Model):
	class Admin:
		pass
	email = models.CharField(maxlength = 100)
	password = models.CharField(maxlength = 100)
	def __unicode__(self):
		return u'Account for %s' % self.email
	def _get_service(self):
		if not _services.has_key(self.email):
			print 'Logging in...'
			_service = gdata.calendar.service.CalendarService()
			_service.email = self.email
			_service.password = self.password
			_service.source = 'ITSLtd-Django_Google-%s' % VERSION
			_service.ProgrammaticLogin()
			_services[self.email] = _service
		return _services[self.email]
	service = property(_get_service, None)
	def get_own_calendars(self):
		cals = self.service.GetOwnCalendarsFeed()
		result = []
		for i, cal in enumerate(cals.entry):
			result.append(Calendar.objects.get_or_create(self, cal))
		return result

class Calendar(models.Model):
	class Admin:
		pass
	objects = CalendarManager()
	account = models.ForeignKey(Account)
	uri = models.CharField(maxlength = 255, unique = True)
	title = models.CharField(maxlength = 100)
	where = models.CharField(maxlength = 100, blank = True)
	color = models.CharField(maxlength = 10, blank = True)
	timezone = models.CharField(maxlength = 100, blank = True)
	summary = models.TextField()
	feed_uri = models.CharField(maxlength = 255, blank = True)
	def __unicode__(self):
		return self.title
	def get_events(self):
		events = self.account.service.GetCalendarEventFeed(uri = self.feed_uri)
		result = []
		for i, event in enumerate(events.entry):
			result.append(Event.objects.get_or_create(self, event))
		return result

class Event(models.Model):
	class Admin:
		pass
	objects = EventManager()
	calendar = models.ForeignKey(Calendar)
	uri = models.CharField(maxlength = 255, unique = True)
	title = models.CharField(maxlength  =255)
	edit_uri = models.CharField(maxlength = 255)
	view_uri = models.CharField(maxlength = 255)
	content = models.TextField(blank = True)
	start_time = models.DateTimeField()
	end_time = models.DateTimeField()
	def __unicode__(self):
		return u'%s (%s - %s)' % (self.title, self.start_time, self.end_time)
	def save(self):
		if self.uri: # existing event, update
			entry = self.calendar.account.service.GetCalendarEventEntry(uri = self.edit_uri)
			entry.title.text = self.title
			entry.content.text = self.content
			start_time = self.start_time.strftime('%Y-%m-%dT%H:%M:%S.000Z')
			end_time = self.end_time.strftime('%Y-%m-%dT%H:%M:%S.000Z')
			entry.when = []
			entry.when.append(gdata.calendar.When(start_time = start_time, end_time = end_time))
			self.calendar.account.service.UpdateEvent(entry.GetEditLink().href, entry)
		else:
			entry = gdata.calendar.CalendarEventEntry()
			entry.title = atom.Title(text = self.title)
			entry.content = atom.Content(text = self.content)
			if not self.start_time:
				self.start_time = datetime.datetime.utcnow()
			if not self.end_time:
				self.end_time = self.start_time + datetime.timedelta(hours = 1)
			start_time = self.start_time.strftime('%Y-%m-%dT%H:%M:%S.000Z')
			end_time = self.end_time.strftime('%Y-%m-%dT%H:%M:%S.000Z')
			entry.when.append(gdata.calendar.When(start_time = start_time, end_time = end_time))
			new_entry = self.calendar.account.service.InsertEvent(entry, self.calendar.feed_uri)
			self.uri = new_entry.id.text
			self.edit_uri = new_entry.GetEditLink().href
			self.view_uri = new_entry.GetHtmlLink().href
		super(Event, self).save()
	def delete(self):
		if self.uri: # existing event, delete
			self.calendar.account.service.DeleteEvent(self.edit_uri)
		super(Event, self).delete()

def listCals(account):
	cals = account.get_own_calendars()
	for c in cals:
		print c
		print '--- EVENTS:'
		for e in c.get_events():
			print e

