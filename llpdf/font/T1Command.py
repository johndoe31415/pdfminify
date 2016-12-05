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

import enum

class T1CommandCode(enum.IntEnum):
	hstem = 1
	vstem = 3
	vmoveto = 4
	rlineto = 5
	hlineto = 6
	vlineto = 7
	rrcurveto = 8
	closepath = 9
	callsubr = 10
	retrn = 11
	escape = 12
	hsbw = 13
	endchar = 14
	rmoveto = 21
	hmoveto = 22
	vhcurveto = 30
	hvcurveto = 31

	dotsection = (escape << 8) | 0
	vstem3 = (escape << 8) | 1
	hstem3 = (escape << 8) | 2
	seac = (escape << 8) | 6
	sbw = (escape << 8) | 7
	div = (escape << 8) | 12
	callothersubr = (escape << 8) | 16
	pop = (escape << 8) | 17
	setcurrentpoint = (escape << 8) | 33

class T1Command(object):
	def __init__(self, cmdcode, *args):
		self._cmdcode = cmdcode
		self._args = args

	@property
	def cmdcode(self):
		return self._cmdcode

	@property
	def args(self):
		return self._args

	def __getitem__(self, index):
		return self._args[index]

	def __iter__(self):
		return iter(self._args)

	def __repr__(self):
		return str(self)

	def __str__(self):
		if len(self._args) == 0:
			return str(self._cmdcode.name)
		else:
			return "%s(%s)" % (self._cmdcode.name, ", ".join(str(arg) for arg in self._args))
