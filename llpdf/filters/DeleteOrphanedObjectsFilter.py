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

class DeleteOrphanedObjectsFilter(PDFFilter):
	def _traverse(self, data_structure):
		if isinstance(data_structure, dict):
			for (key, value) in data_structure.items():
				self._traverse(key)
				self._traverse(value)
		elif isinstance(data_structure, list):
			for element in data_structure:
				self._traverse(element)
		elif isinstance(data_structure, PDFXRef):
			self._referenced_objects.add(data_structure)

	def run(self):
		self._referenced_objects = set()
		all_objects = set()
		for obj in self._pdf:
			all_objects.add(obj.xref)
			self._traverse(obj.content)
		self._traverse(self._pdf.trailer)

		unused_objects = all_objects - self._referenced_objects
		self._log.debug("%d objects total, %d referenced (i.e., %d objects unused): %s", len(all_objects), len(self._referenced_objects), len(unused_objects), unused_objects)
		for obj_xref in unused_objects:
			self._optimized(len(self._pdf.lookup(obj_xref)), 0)
			self._pdf.delete_object(obj_xref.objid, obj_xref.gennum)
