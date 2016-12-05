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

class T1PRNG(object):
	_C1 = 52845
	_C2 = 22719

	def __init__(self, r):
		self._r = r & 0xffff

	def decrypt_byte(self, cipher):
		plain = (cipher ^ (self._r >> 8)) & 0xff
		self._r = (((cipher + self._r) & 0xffff) * self._C1 + self._C2) & 0xffff
		return plain

	def decrypt_bytes(self, data):
		return bytes(self.decrypt_byte(cipher) for cipher in data)[4:]
