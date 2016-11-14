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

import logging

class PDFFilter(object):
	def __init__(self, pdf, args):
		self._log = logging.getLogger("llpdf.filters." + self.__class__.__name__)
		self._pdf = pdf
		self._args = args
		self._bytes_saved = 0

	@property
	def bytes_saved(self):
		return self._bytes_saved

	def _optimized(self, old_byte_cnt, new_byte_cnt):
		self._bytes_saved += (old_byte_cnt - new_byte_cnt)

	def run(self):
		raise Exception(NotImplemented)
