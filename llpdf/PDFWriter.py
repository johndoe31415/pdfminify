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
from llpdf.types.CompressedObjectContainer import CompressedObjectContainer
from llpdf.types.XRefTable import XRefTable, UncompressedXRefEntry, CompressedXRefEntry
from llpdf.FileRepr import FileWriterDecorator

class PDFWriter(object):
	def __init__(self, pdf, f, pretty = False, use_object_streams = False, use_xref_stream = False):
		self._pdf = pdf
		self._f = FileWriterDecorator.wrap(f)
		self._pretty = pretty
		self._use_object_streams = use_object_streams
		self._use_xref_stream = use_xref_stream
		self._xref = XRefTable()

	def _write_header(self):
		self._f.writeline("%PDF-1.5")
		self._f.write(b"%\xb5\xed\xae\xfb\n")

	def _write_uncompressed_object(self, obj, pretty = False):
		offset = self._f.tell()
		self._f.writeline("%d %d obj" % (obj.objid, obj.gennum))
		serializer = PDFSerializer(pretty = self._pretty)
		self._f.writeline(serializer.serialize(obj.content))
		if obj.stream is not None:
			self._f.writeline("stream")
			self._f.write(obj.stream)
			self._f.write(b"\n")
			self._f.writeline("endstream")
		self._f.writeline("endobj")
		self._xref.add_entry(UncompressedXRefEntry(objid = obj.objid, gennum = obj.gennum, offset = offset))

	def _write_objs(self, pretty = False):
		for obj in sorted(self._pdf):
			self._write_uncompressed_object(obj)

	def _write_xrefs(self):
		if not self._use_xref_stream:
			self._xref.write_xref_table(self._f)
		else:
			raise Exception(NotImplemented)

	def _write_trailer(self):
		self._f.writeline("trailer")
		serializer = PDFSerializer(pretty = self._pretty)
		self._f.writeline(serializer.serialize(self._pdf.trailer))

	def _write_finish(self):
		self._f.writeline("startxref")
		self._f.writeline(str(self._xref.xref_offset))
		self._f.writeline("%%EOF")

	def write(self):
		self._write_header()
		self._write_objs()
		self._write_xrefs()
		self._write_trailer()
		self._write_finish()



