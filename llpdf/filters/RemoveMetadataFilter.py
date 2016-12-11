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

class RemoveMetadataFilter(PDFFilter):
	@staticmethod
	def _strip_key(key):
		if key.value.startswith("/PTEX"):
			return True
		return False

	def _traverse(self, data_structure):
		if isinstance(data_structure, dict):
			return { key: self._traverse(value) for (key, value) in data_structure.items() if not self._strip_key(key) }
		elif isinstance(data_structure, list):
			return [ self._traverse(value) for value in data_structure ]
		else:
			return data_structure

	def run(self):
		for obj in self._pdf:
			content = self._traverse(obj.content)
			obj.set_content(content)
