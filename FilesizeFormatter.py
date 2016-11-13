#!/usr/bin/python3
#
#	FilesizeFormatter - Displaying file size in native units.
#	Copyright (C) 2011-2013 Johannes Bauer
#
#	This file is part of jpycommon.
#
#	jpycommon is free software; you can redistribute it and/or modify
#	it under the terms of the GNU General Public License as published by
#	the Free Software Foundation; this program is ONLY licensed under
#	version 3 of the License, later versions are explicitly excluded.
#
#	jpycommon is distributed in the hope that it will be useful,
#	but WITHOUT ANY WARRANTY; without even the implied warranty of
#	MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#	GNU General Public License for more details.
#
#	You should have received a copy of the GNU General Public License
#	along with jpycommon; if not, write to the Free Software
#	Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA
#
#	Johannes Bauer <JohannesBauer@gmx.de>
#
#	File UUID 25a847c5-fa2a-4055-878a-e7b2b3ac3875

class FilesizeFormatter():
	_units = [
		("k", 1),
		("M", 2),
		("G", 3),
		("T", 4),
		("P", 5),
	]
	_unitsdict = { unit.lower(): pwr for (unit, pwr) in _units }

	def __init__(self, base1000 = True):
		self._base = [ 1024, 1000 ][ base1000 ]
		self._basechar = [ "i", "" ][ base1000 ]

	def _pwr(self, of):
		return self._base ** of

	def __call__(self, size):
		assert(isinstance(size, int))
		if size < 0:
			return "-" + self(-size)

		if size < self._pwr(1):
			if size == 1:
				return "%d byte" % (size)
			else:
				return "%d bytes" % (size)
		else:
			for (unit, power) in FilesizeFormatter._units:
				if size < self._pwr(power + 1):
					value = size / self._pwr(power)
					if value < 10:
						return "%.2f %s%sB" % (value, unit, self._basechar)
					elif value < 100:
						return "%.1f %s%sB" % (value, unit, self._basechar)
					else:
						return "%.0f %s%sB" % (value, unit, self._basechar)

	def decode(self, value):
		suffix = value[-1].lower()
		if suffix in "kmgtp":
			multiplier = self._pwr(FilesizeFormatter._unitsdict[suffix])
			convert = value[:-1]
		else:
			multiplier = 1
			convert = value
		value = float(convert) * multiplier
		return round(value)

if __name__ == "__main__":
	for fsfmtter in [ FilesizeFormatter(), FilesizeFormatter(True) ]:
		for pot in range(15):
			q = round(3.141592653589793 * (10 ** pot))
			print("%20d %s" % (q, fsfmtter(q)))
		print(fsfmtter.decode("123"))
		print(fsfmtter.decode("123.45k"))
		print(fsfmtter.decode("123.45m"))
		print(fsfmtter.decode("123.45g"))
		print("-" * 80)

