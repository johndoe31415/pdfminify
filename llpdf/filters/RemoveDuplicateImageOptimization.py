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

import hashlib
import collections
from .PDFFilter import PDFFilter
from .Relinker import Relinker

class RemoveDuplicateImageOptimization(PDFFilter):
	def run(self):
		objs_by_hash = collections.defaultdict(list)
		for obj in self._pdf.image_objects:
			hashval = hashlib.md5(obj.raw_stream).hexdigest()
			objs_by_hash[hashval].append(obj.xref)

		relinker = Relinker(self._pdf)
		for (hashval, objects) in objs_by_hash.items():
			if len(objects) == 1:
				# Unique object
				continue
			reference_object = objects[0]
			delete_objects = objects[1:]
			object_size = len(self._pdf.lookup(reference_object))
			self._log.debug("Relinking %d duplicate objects with %d bytes each %s to %s", len(delete_objects), object_size, delete_objects, reference_object)
			for delete_object in delete_objects:
				relinker.relink(delete_object, reference_object)

			self._optimized(len(objects) * object_size, object_size)
		relinker.run()
