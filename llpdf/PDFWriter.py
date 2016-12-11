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
from llpdf.repr.PDFSerializer import PDFSerializer
from llpdf.types.CompressedObjectContainer import CompressedObjectContainer
from llpdf.types.XRefTable import XRefTable, UncompressedXRefEntry, ReservedXRefEntry
from llpdf.FileRepr import FileWriterDecorator

class PDFWriter(object):
	_log = logging.getLogger("llpdf.PDFWriter")

	# Maximum number of objects to keep inside one compressed object
	_COMPRESS_OBJECT_CNT = 100

	def __init__(self, pdf, f, pretty = False, use_object_streams = True, use_xref_stream = True):
		self._pdf = pdf
		self._f = FileWriterDecorator.wrap(f)
		self._pretty = pretty
		self._use_object_streams = use_object_streams and use_xref_stream
		self._use_xref_stream = use_xref_stream
		self._compress_objects = [ ]
		self._compression_containers = [ ]
		self._xref = XRefTable()
		self._serializer = PDFSerializer(pretty = self._pretty)

	@property
	def outfile(self):
		return self._f

	@property
	def serializer(self):
		return self._serializer

	def _write_header(self):
		if (not self._use_object_streams) and (not self._use_xref_stream):
			self._f.writeline("%PDF-1.4")
		else:
			self._f.writeline("%PDF-1.5")
		self._f.write(b"%\xb5\xed\xae\xfb\n")

	def _write_uncompressed_object(self, obj):
		offset = self._f.tell()
		self._f.writeline("%d %d obj" % (obj.objid, obj.gennum))
		self._f.write(self._serializer.serialize(obj.content, start_offset = self._f.tell()))
		if obj.has_stream:
			self._f.writeline("stream")
			self._f.write(obj.raw_stream)
			self._f.write(b"\n")
			self._f.writeline("endstream")
		self._f.writeline("endobj")
		self._xref.add_entry(UncompressedXRefEntry(objid = obj.objid, gennum = obj.gennum, offset = offset))

	def _containerize_compressed_object(self, obj):
		self._log.trace("Compressing %s", obj)
		if (len(self._compression_containers) == 0) or (self._compression_containers[-1].objects_inside_count >= self._COMPRESS_OBJECT_CNT):
			# Get a reservation for a ObjId for the compressed container
			compressed_objid = self._xref.reserve_free_objid()
			self._log.debug("New compression container allocated with ObjId %d", compressed_objid)

			# Create a new compressed object container
			container = CompressedObjectContainer(compressed_objid)
			self._compression_containers.append(container)
		else:
			# Add to the last container
			container = self._compression_containers[-1]

		# Now we have the container, just add the new object to it and get the
		# CompressedXRefEntry out
		compressed_xref_entry = container.add(obj)

		# Add the compressed XRefEntry to the XRef table
		self._xref.add_entry(compressed_xref_entry)

	def _write_objs(self):
		for obj in sorted(self._pdf):
			object_compressible = not obj.has_stream
			if object_compressible and self._use_object_streams:
				self._compress_objects.append(obj)
			else:
				self._write_uncompressed_object(obj)

	def _write_compressed_objs(self):
		# Reserve objects in XRef table so their ObjId doesn't get assigned to
		# containers later
		for obj in self._compress_objects:
			self._xref.add_entry(ReservedXRefEntry(objid = obj.objid, gennum = obj.gennum))

		# Then place them inside their compression containers
		for obj in self._compress_objects:
			self._containerize_compressed_object(obj)

		# Afterwards write containers to file
		for container in self._compression_containers:
			self._log.debug("Writing compressed object %s", container)
			self._serializer.offset = self._f.tell()
			container_obj = container.serialize(self._serializer)
			self._write_uncompressed_object(container_obj)

	def _write_xrefs(self):
		if not self._use_xref_stream:
			self._xref.write_xref_table(self._f)
			self._write_trailer()
		else:
			xref_object = self._xref.serialize_xref_object(self._pdf.trailer, self._xref.get_free_objid())
			self._xref.xref_offset = self._f.tell()
			self._write_uncompressed_object(xref_object)

	def _write_trailer(self):
		self._f.writeline("trailer")
		self._f.write(self._serializer.serialize(self._pdf.trailer, start_offset = self._f.tell()))

	def _write_finish(self):
		self._f.writeline("startxref")
		self._f.writeline(str(self._xref.xref_offset))
		self._f.writeline("%%EOF")

	def write(self):
		self._write_header()
		self._write_objs()
		self._write_compressed_objs()
		self._write_xrefs()
		self._write_finish()
