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

class Measurements(object):
	_UNITS = {
		"mm":			1,
		"cm":			10,
		"native":		1 / 72 * 25.4,
		"inch":			25.4,
	}

	@classmethod
	def convert(cls, value, from_unit, to_unit):
		from_scalar = cls._UNITS[from_unit]
		to_scalar = cls._UNITS[to_unit]
		return value / to_scalar * from_scalar

	@classmethod
	def list_units(cls):
		return sorted(cls._UNITS.keys())

if __name__ == "__main__":
	for unit in Measurements.list_units():
		value = Measurements.convert(1, "cm", unit)
		print("1 cm = %.1f %s" % (value, unit))
	print()
	for unit in Measurements.list_units():
		value = Measurements.convert(1, unit, "cm")
		print("1 %s = %.1f cm" % (unit, value))

#	for unit in Measurements.list_units():
#		value = Measurements.convert(10, "mm", unit)
#		print("1 %s = %.1f cm" % (value, unit))
