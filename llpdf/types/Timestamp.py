#	pdfminify - Tool to minify PDF files.
#	Copyright (C) 2016-2016 Johannes Bauer
#
#	This file is part of pdfminify.
#
#	pdfminify is free software; you can redistribute it and/or modify
#	it under the terms of the GNU General Public License as published by
#	the Free Software Foundation; this program is ONLY licensed under
#	version 3 of the License, later versions are explicitly excluded.
#
#	pdfminify is distributed in the hope that it will be useful,
#	but WITHOUT ANY WARRANTY; without even the implied warranty of
#	MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#	GNU General Public License for more details.
#
#	You should have received a copy of the GNU General Public License
#	along with pdfminify; if not, write to the Free Software
#	Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA
#
#	Johannes Bauer <JohannesBauer@gmx.de>
#

import time
import datetime
import re

class Timestamp(object):
	_PDF_FORMAT_RE = re.compile(r"D:(?P<year>\d{4})(?P<month>\d{2})(?P<day>\d{2})(?P<hour>\d{2})(?P<minute>\d{2})(?P<second>\d{2})(?P<tzhrs>[+-]\d{2})'(?P<tzmins>\d{2})'")

	def __init__(self, ts_datetime, offset_mins):
		assert(isinstance(ts_datetime, datetime.datetime))
		assert(isinstance(offset_mins, int))
		assert(-1439 <= offset_mins <= 1439)
		self._ts = ts_datetime
		self._offset_mins = offset_mins

	@classmethod
	def utcnow(cls):
		return cls(datetime.datetime.utcnow(), 0)

	@classmethod
	def localnow(cls):
		return cls(datetime.datetime.now(), -time.timezone // 60)

	@classmethod
	def frompdf(cls, pdfts):
		result = cls._PDF_FORMAT_RE.fullmatch(pdfts)
		if not result:
			raise Exception("Invalid timestamp: %s" % (pdfts))
		result = result.groupdict()
		result = { key: int(value) for (key, value) in result.items() }
		dt = datetime.datetime(result["year"], result["month"], result["day"], result["hour"], result["minute"], result["second"])
		tz_neg = result["tzhrs"] < 0
		tz_offset = (abs(result["tzhrs"]) * 60) + result["tzmins"]
		if tz_neg:
			tz_offset = -tz_offset
		return cls(dt, tz_offset)

	def format_human_readable(self):
		result = self._ts.strftime("%Y-%m-%d %H:%M:%S ")
		result += "%+03d:%02d" % (self._offset_mins // 60, abs(self._offset_mins) % 60)
		return result

	def format_xml(self):
		result = self._ts.strftime("%Y-%m-%dT%H:%M:%S")
		result += "%+03d:%02d" % (self._offset_mins // 60, abs(self._offset_mins) % 60)
		return result

	def format_pdf(self):
		result = self._ts.strftime("D:%Y%m%d%H%M%S")
		result += "%+03d'%02d'" % (self._offset_mins // 60, abs(self._offset_mins) % 60)
		return result

	def __repr__(self):
		return str(self)

	def __str__(self):
		return "Timestamp<%s>" % (self.format_xml())

if __name__ == "__main__":
	print(Timestamp.utcnow())
	print(Timestamp.localnow())
	print(Timestamp.frompdf("D:20160829121904+02'00'"))
