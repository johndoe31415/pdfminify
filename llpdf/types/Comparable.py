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

class Comparable(object):
	def _compare(self, other, method):
		try:
			return method(self.cmpkey(), other.cmpkey())
		except (AttributeError, TypeError):
			# cmpkey not implemented, or return different type,
			# so I can't compare with "other".
			return NotImplemented

	def __lt__(self, other):
		return self._compare(other, lambda s, o: s < o)

	def __le__(self, other):
		return self._compare(other, lambda s, o: s <= o)

	def __eq__(self, other):
		return self._compare(other, lambda s, o: s == o)

	def __ge__(self, other):
		return self._compare(other, lambda s, o: s >= o)

	def __gt__(self, other):
		return self._compare(other, lambda s, o: s > o)

	def __ne__(self, other):
		return self._compare(other, lambda s, o: s != o)

	def __hash__(self):
		return hash(self.cmpkey())
