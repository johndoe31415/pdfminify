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

from .PDFFilter import PDFFilter
from llpdf.types.PDFXRef import PDFXRef
from llpdf.types.PDFName import PDFName

class ExplicitLengthFilter(PDFFilter):
	def run(self):
		for obj in self._pdf:
			if isinstance(obj.content, dict) and (PDFName("/Length") in obj.content) and isinstance(obj.content[PDFName("/Length")], PDFXRef) and (obj.stream is not None):
				obj.content[PDFName("/Length")] = len(obj.stream)
