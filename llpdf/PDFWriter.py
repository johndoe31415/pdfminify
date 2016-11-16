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

from llpdf.repr.PDFSerializer import PDFSerializer
from llpdf.types.PDFXRef import PDFXRef

class PDFWriter(object):
	def __init__(self, pdf, f):
		self._pdf = pdf
		self._f = f
		self._xref = { }
		self._max_objid = 0

	def _writeline(self, text):
		self._f.write((text + "\n").encode("utf-8"))

	def _write_header(self):
		self._writeline("%PDF-1.5")
		self._f.write(b"%\xb5\xed\xae\xfb\n")

	def _write_objs(self):
		for obj in sorted(self._pdf):
			self._xref[obj.xref] = self._f.tell()
			self._writeline("%d %d obj" % (obj.objid, obj.gennum))
			serializer = PDFSerializer(obj.content)
			self._writeline(serializer.serialize())
			if obj.stream is not None:
				self._writeline("stream")
				self._f.write(obj.stream)
				self._f.write(b"\n")
				self._writeline("endstream")
			self._writeline("endobj")
		self._max_objid = obj.objid

	def _write_xref_entry(self, offset, gennum, f_or_n):
		assert(f_or_n in [ "f", "n" ])
		self._writeline("%010d %05d %s " % (offset, gennum, f_or_n))

	def _write_xrefs(self):
		self._xref_offset = self._f.tell()

		self._writeline("xref")
		self._writeline("0 %d" % (1 + self._max_objid))
		self._write_xref_entry(0, 65535, "f")
		for objid in range(self._max_objid):
			gennum = 0
			offset = self._xref.get(PDFXRef(objid, gennum))
			if offset is None:
				self._write_xref_entry(0, 0, "f")
			else:
				self._write_xref_entry(offset, gennum, "n")

	def _write_trailer(self):
		self._writeline("trailer")
		serializer = PDFSerializer(self._pdf.trailer)
		self._writeline(serializer.serialize())

	def _write_finish(self):
		self._writeline("startxref")
		self._writeline(str(self._xref_offset))
		self._writeline("%%EOF")

	def write(self):
		self._write_header()
		self._write_objs()
		self._write_xrefs()
		self._write_trailer()
		self._write_finish()



