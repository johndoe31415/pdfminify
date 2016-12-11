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

from llpdf.types.PDFXRef import PDFXRef
from llpdf.types.PDFObject import PDFObject

class Relinker(object):
	def __init__(self, pdf):
		self._pdf = pdf
		self._old_to_new = { }
		self._references = set()

	@property
	def references(self):
		return self._references

	@property
	def unresolved_references(self):
		return self._references - set(self._old_to_new.keys())

	def relink(self, pattern, replace_by):
		assert(isinstance(pattern, PDFXRef))
		assert(isinstance(replace_by, PDFXRef))
		self._old_to_new[pattern] = replace_by

	def _relink(self, data_structure):
		if isinstance(data_structure, dict):
			return { key: self._relink(value) for (key, value) in data_structure.items() }
		elif isinstance(data_structure, list):
			return [ self._relink(value) for value in data_structure ]
		elif isinstance(data_structure, PDFXRef):
			self._references.add(data_structure)
			return self._old_to_new.get(data_structure, data_structure)
		else:
			return data_structure

	def __getitem__(self, xref):
		return self._old_to_new[xref]

	def run(self):
		# Relink the content dictionaries
		relinked_objects = [ ]
		for obj in self._pdf:
			relinked_content = self._relink(obj.content)
			relinked_xref = self._old_to_new.get(obj.xref, obj.xref)
			relinked_object = PDFObject.create(relinked_xref.objid, relinked_xref.gennum, relinked_content, obj.stream)
			relinked_objects.append(relinked_object)

		# Then delete all old objects
		for delete_obj_xref in self._old_to_new:
			self._pdf.delete_object(delete_obj_xref.objid, delete_obj_xref.gennum)

		# And insert the relinked ones
		for relinked_object in relinked_objects:
			self._pdf.replace_object(relinked_object)
