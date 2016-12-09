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

import collections


class Measurements(object):
	_UnitDefinition = collections.namedtuple("UnitDefinition", [ "name", "factor", "format", "abbreviation" ])

	_UNITS = {
		"mm":		_UnitDefinition(name = "mm", factor = 1, format = "%.1f", abbreviation = " mm"),
		"cm":		_UnitDefinition(name = "cm", factor = 10, format = "%.2f", abbreviation = " cm"),
		"native":	_UnitDefinition(name = "native", factor = 1 / 72 * 25.4, format = "%.0f", abbreviation = " u"),
		"inch":		_UnitDefinition(name = "inch", factor = 25.4, format = "%.2f", abbreviation = "\""),
	}
	_DEFAULT_UNIT = "native"

	@classmethod
	def convert(cls, value, from_unit = None, to_unit = None):
		if from_unit is None:
			from_unit = cls._DEFAULT_UNIT
		if to_unit is None:
			to_unit = cls._DEFAULT_UNIT
		from_scalar = cls._UNITS[from_unit].factor
		to_scalar = cls._UNITS[to_unit].factor
		return value / to_scalar * from_scalar

	@classmethod
	def list_units(cls):
		return sorted(cls._UNITS.keys())

	@classmethod
	def set_default_unit(cls, unit):
		assert(unit in cls._UNITS)
		cls._DEFAULT_UNIT = unit

	@classmethod
	def format(cls, value, unit = None, to_unit = None, suffix = True):
		if to_unit is None:
			to_unit = cls._DEFAULT_UNIT
		from_unit = cls._UNITS[unit]
		to_unit = cls._UNITS[to_unit]
		scaled_value = value / to_unit.factor * from_unit.factor
		result = to_unit.format % scaled_value
		if suffix:
			result += to_unit.abbreviation
		return result

if __name__ == "__main__":
	for unit in Measurements.list_units():
		print("1 cm = %s" % (Measurements.format(1, "cm", unit)))
	print()

	Measurements.set_default_unit("cm")
	for unit in Measurements.list_units():
		print("1 %s = %s" % (unit, Measurements.format(1, unit)))

	print()
	Measurements.set_default_unit("mm")
	print(Measurements.format(0.1, "mm"))
	print(Measurements.format(0.01, "cm"))
	print(Measurements.format(1, "native"))
	print(Measurements.format(0.01, "inch"))
