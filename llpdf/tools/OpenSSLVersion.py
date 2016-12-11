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

import subprocess
import re
import string

class OpenSSLVersion(object):
	_OPENSSL_VERSION_REGEX = re.compile(r"OpenSSL (?P<major>\d+)\.(?P<minor>\d+)\.(?P<fixlevel>\d+)(?P<patch>[a-z])?(-fips)?\s+(?P<date>\d+ [A-Za-z]{3} \d{4})")
	def __init__(self, text_string):
		self._text = text_string

		result = self._OPENSSL_VERSION_REGEX.match(self._text)
		if result is None:
			raise Exception("Unable to parse OpenSSL version: %s" % (self._text))
		result = result.groupdict()
		self._intvalue = self._parse_to_intvalue(result)
		self._date = result["date"]

	@staticmethod
	def _parse_to_intvalue(result):
		major = int(result["major"])
		minor = int(result["minor"])
		fixlevel = int(result["fixlevel"])
		patch = 0 if (result["patch"] is None) else (string.ascii_lowercase.index(result["patch"]) + 1)
		status = 0xf		# We assume release
		return (status << 0) | (patch << 4) | (fixlevel << 12) | (minor << 20) | (major << 28)

	@property
	def text(self):
		return self._text

	@property
	def date(self):
		return self._date

	def __int__(self):
		return self._intvalue

	@classmethod
	def _get_openssl_version(cls):
		version = subprocess.check_output([ "openssl", "version" ])
		version = version.decode().rstrip("\r\n")
		return version

	@classmethod
	def get(cls):
		return cls(cls._get_openssl_version())
