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

import re
import logging

from .types.PDFObject import PDFObject
from .types.PDFXRef import PDFXRef
from .FileRepr import StreamRepr
from .filters.Relinker import Relinker

class PDFTemplate(object):
	_log = logging.getLogger("llpdf.PDFTemplate")
	_OBJECT_NAME_RE = re.compile(r"^(?P<inout>[<>])\s*(?P<xref>\d+)\s*=\s*(?P<name>.*)$")

	def __init__(self, resource_data):
		self._objs = { }
		self._inputs = { }
		self._outputs = { }
		self._input_values = { }
		self._f = StreamRepr(resource_data)
		self._read_header()
		self._read_objects()


	def _read_header_line(self):
		line = self._f.readline().decode("ascii")
		result = self._OBJECT_NAME_RE.match(line)
		if result is None:
			return False
		result = result.groupdict()
		is_input = (result["inout"] == "<")
		xref = int(result["xref"])
		name = result["name"]
		if is_input:
			self._inputs[name] = xref
		else:
			self._outputs[name] = xref
		return True

	def _read_header_line_if_exists(self):
		pos = self._f.tell()
		success = self._read_header_line()
		if not success:
			self._f.seek(pos)
		return success

	def _read_header(self):
		while True:
			if not self._read_header_line_if_exists():
				break

	def _read_objects(self):
		while True:
			obj = PDFObject.parse(self._f)
			if obj is None:
				break
			self._objs[(obj.objid, obj.gennum)] = obj

	def __setitem__(self, name, value):
		if name not in self._inputs:
			raise Exception("Tried to set input '%s', but this is not a known input for this template." % (name))
		self._input_values[name] = value

	def replace_object(self, obj):
		self._objs[(obj.objid, obj.gennum)] = obj

	def delete_object(self, objid, gennum):
		if (objid, gennum) in self._objs:
			del self._objs[(objid, gennum)]

	def merge_into_pdf(self, pdf):
		if len(self._inputs) != len(self._input_values):
			raise Exception("Not all inputs where set for this template before merging into the PDF.")

		# Allocate object IDs in PDF to input this into
		relinker = Relinker(self)
		objids = list(pdf.get_free_objids(len(self)))

		for (resource_object, new_objid) in zip(self, objids):
			old_xref = resource_object.xref
			new_xref = PDFXRef(new_objid, 0)
			relinker.relink(old_xref, new_xref)

		internal_references = set(PDFXRef(objid, gennum) for (objid, gennum) in self._objs.keys())

		for name in self._inputs:
			old_xref = PDFXRef(self._inputs[name], 0)
			new_xref = self._input_values[name]
			relinker.relink(old_xref, new_xref)
		relinker.run()

		referenced = set(relinker.references)
		for objid in self._outputs.values():
			referenced.add(PDFXRef(objid, 0))
		dangling_references = internal_references - referenced
		if len(dangling_references) > 0:
			raise Exception("PDFTemplate contains dangling objects which are never referenced nor exported: %s" % (dangling_references))

		unresolved = relinker.unresolved_references
		if len(unresolved) > 0:
			raise Exception("Coalescing PDFTemplate with unresolved cross references %s." % (unresolved))
		for obj in self:
			pdf.replace_object(obj)

		outputs = { name: relinker[PDFXRef(internal_objid, 0)] for (name, internal_objid) in self._outputs.items() }
		return outputs

	def __iter__(self):
		return iter(self._objs.values())

	def __len__(self):
		return len(self._objs)

	def __str__(self):
		return "PDFTemplate<%d objects, %d inputs: {%s}, %d outputs: {%s}>" % (len(self), len(self._inputs), ", ".join(sorted(self._inputs.keys())), len(self._outputs), ", ".join(sorted(self._outputs.keys())))
