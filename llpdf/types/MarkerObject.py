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

class MarkerObject(object):
	def __init__(self, name, raw = None, child = None):
		if not ((raw is None) ^ (child is None)):
			raise Exception("Either one of 'raw' or 'child' must be set, but not both.")
		if raw is not None:
			assert(isinstance(raw, str))
		self._name = name
		self._raw = raw
		self._child = child

	@property
	def name(self):
		return self._name

	@property
	def is_raw(self):
		return self._raw is not None

	@property
	def raw(self):
		return self._raw

	@property
	def child(self):
		return self._child

	def __repr__(self):
		return str(self)

	def __str__(self):
		if self._raw:
			return "RawMarkerObject<%s: %s>" % (self.name, self.raw)
		else:
			return "ChildMarkerObject<%s: %s>" % (self.name, str(self.child))
