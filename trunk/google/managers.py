from django.db.models import Manager
import re
import time
import datetime

class CalendarManager(Manager):
	def get_or_create(self, account, data):
		uri = data.id.text
		try:
			result = self.get(uri = uri)
		except self.model.DoesNotExist:
			result = self.model(account = account)
		result.uri = uri
		for prop in ['color', 'summary', 'timezone', 'title', 'where']:
			attr = getattr(data, prop)
			if hasattr(attr, 'text'):
				setattr(result, prop, attr.text or '')
		for link in data.link:
			if link.rel == 'alternate':
				result.feed_uri = link.href
		return result


def parse_date_w3dtf(dateString):
	def __extract_date(m):
		year = int(m.group('year'))
		if year < 100:
			year = 100 * int(time.gmtime()[0] / 100) + int(year)
		if year < 1000:
			return 0, 0, 0
		julian = m.group('julian')
		if julian:
			julian = int(julian)
			month = julian / 30 + 1
			day = julian % 30 + 1
			jday = None
			while jday != julian:
				t = time.mktime((year, month, day, 0, 0, 0, 0, 0, 0))
				jday = time.gmtime(t)[-2]
				diff = abs(jday - julian)
				if jday > julian:
					if diff < day:
						day = day - diff
					else:
						month = month - 1
						day = 31
				elif jday < julian:
					if day + diff < 28:
					   day = day + diff
					else:
						month = month + 1
			return year, month, day
		month = m.group('month')
		day = 1
		if month is None:
			month = 1
		else:
			month = int(month)
			day = m.group('day')
			if day:
				day = int(day)
			else:
				day = 1
		return year, month, day
	def __extract_time(m):
		if not m:
			return 0, 0, 0
		hours = m.group('hours')
		if not hours:
			return 0, 0, 0
		hours = int(hours)
		minutes = int(m.group('minutes'))
		seconds = m.group('seconds')
		if seconds:
			seconds = int(float(seconds))
		else:
			seconds = 0
		return hours, minutes, seconds
	def __extract_tzd(m):
		'''Return the Time Zone Designator as an offset in seconds from UTC.'''
		if not m:
			return 0
		tzd = m.group('tzd')
		if not tzd:
			return 0
		if tzd == 'Z':
			return 0
		hours = int(m.group('tzdhours'))
		minutes = m.group('tzdminutes')
		if minutes:
			minutes = int(minutes)
		else:
			minutes = 0
		offset = (hours*60 + minutes)
		if tzd[0] == '+':
			return -offset
		return offset
	__date_re = ('(?P<year>\d\d\d\d)'
				 '(?:(?P<dsep>-|)'
				 '(?:(?P<julian>\d\d\d)'
				 '|(?P<month>\d\d)(?:(?P=dsep)(?P<day>\d\d))?))?')
	__tzd_re = '(?P<tzd>[-+](?P<tzdhours>\d\d)(?::?(?P<tzdminutes>\d\d))|Z)'
	__tzd_rx = re.compile(__tzd_re)
	__time_re = ('(?P<hours>\d\d)(?P<tsep>:|)(?P<minutes>\d\d)'
				 '(?:(?P=tsep)(?P<seconds>\d\d(?:[.,]\d+)?))?'
				 + __tzd_re)
	__datetime_re = '%s(?:T%s)?' % (__date_re, __time_re)
	__datetime_rx = re.compile(__datetime_re)
	m = __datetime_rx.match(dateString)
	if (m is None) or (m.group() != dateString): return
	gmt = __extract_date(m) + __extract_time(m)
	if gmt[0] == 0: return
	return datetime.datetime(tzinfo = None, *gmt) + datetime.timedelta(minutes = __extract_tzd(m))

class EventManager(Manager):
	def get_or_create(self, calendar, data):
		uri = data.id.text
		try:
			result = self.get(uri = uri)
		except self.model.DoesNotExist:
			result = self.model(calendar = calendar)
		result.title = data.title.text
		result.content = data.content.text
		result.start_time = parse_date_w3dtf(data.when[0].start_time)
		result.end_time = parse_date_w3dtf(data.when[0].end_time)
		result.edit_uri = data.GetEditLink().href
		result.view_uri = data.GetHtmlLink().href
		return result

