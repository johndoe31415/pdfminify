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

import os
import datetime
import llpdf
from llpdf.types.PDFObject import PDFObject
from llpdf.types.PDFName import PDFName
from llpdf.EncodeDecode import EncodedObject
from .PDFFilter import PDFFilter

class EmbedPayloadFilter(PDFFilter):
	def run(self):
		with open(self._args.embed_payload, "rb") as f:
			payload = f.read()

		objid = self._pdf.get_free_objid()
		self._log.debug("Embedding %d bytes payload from file \"%s\" into PDF file as objid %d", len(payload), self._args.embed_payload, objid)

		mtime = os.stat(self._args.embed_payload).st_mtime
		mtime_str = datetime.datetime.utcfromtimestamp(mtime).strftime("%Y-%m-%dT%H:%M:%SZ")
		content = {
			PDFName("/PDFMinify.OriginalFilename"):		os.path.basename(self._args.embed_payload).encode(),
			PDFName("/PDFMinify.MTime"):				mtime_str.encode(),
			PDFName("/PDFMinify.Version"):				llpdf.VERSION.encode(),
		}
		obj = PDFObject.create(objid = objid, gennum = 0, content = content)
		obj.set_stream(EncodedObject.create(payload, compress = False))
		self._pdf.replace_object(obj)
