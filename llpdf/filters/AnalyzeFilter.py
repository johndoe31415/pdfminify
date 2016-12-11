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
from llpdf.types.PDFName import PDFName
from llpdf.types.PDFXRef import PDFXRef

class AnalyzeFilter(PDFFilter):
	@staticmethod
	def _indent(lvl):
		return "    " * lvl

	def _pretty_print(self, element, indent = 0):
		if isinstance(element, PDFName):
			yield element.display_name
		elif isinstance(element, dict):
			yield "{"
			for (key, value) in sorted(element.items()):
				yield "\n"
				yield self._indent(indent + 1)
				yield from self._pretty_print(key, indent + 1)
				yield ": "
				yield from self._pretty_print(value, indent + 1)
			yield "\n"
			yield self._indent(indent)
			yield "}"
		elif isinstance(element, PDFXRef):
			element = self._pdf.lookup(element)
			if element is None:
				yield "null"
			else:
				yield "-> "
				if len(element) > 0:
					yield "<%d> " % (len(element))
				yield from self._pretty_print(element.content, indent)
		elif isinstance(element, list):
			max_list_elements = 5
			yield "["
			for (number, item) in enumerate(element):
				if number > 0:
					yield ", "
				if number == max_list_elements:
					yield "... (%d more)" % (len(element) - max_list_elements)
					break
				yield from self._pretty_print(item)

			yield "]"
		else:
			yield str(element)

	def _dump_object(self, pdf_object):
		print("".join(self._pretty_print(pdf_object.content)))

	def _print_font(self, font_obj):
		if font_obj.getattr(PDFName("/Subtype")) == PDFName("/Type0"):
			ftype = "T0"
		elif font_obj.getattr(PDFName("/Subtype")) == PDFName("/Type1"):
			ftype = "T1"

		elif font_obj.getattr(PDFName("/Subtype")) == PDFName("/CIDFontType2"):
			ftype = "T2"
		else:
			print("Unknown Font subtype: %s (%s)" % (font_obj, font_obj.content))
			return

		basefont = font_obj.getattr(PDFName("/BaseFont"))
		if isinstance(basefont, PDFXRef):
			basefont = self._pdf.lookup(basefont).content

		info = [ ]

		if PDFName("/Encoding") in font_obj.content:
			encoding_xref = font_obj.content[PDFName("/Encoding")]
			if isinstance(encoding_xref, PDFName):
				info.append("encoding %s" % (encoding_xref.display_name))
			else:
				info.append("encoding %s" % (encoding_xref))

		if PDFName("/FirstChar") in font_obj.content:
			(firstchar, lastchar) = (font_obj.content[PDFName("/FirstChar")], font_obj.content[PDFName("/LastChar")])
			info.append("chars %d - %d" % (firstchar, lastchar))

		if PDFName("/FontDescriptor") in font_obj.content:
			descriptor_xref = font_obj.content[PDFName("/FontDescriptor")]
			descriptor = self._pdf.lookup(descriptor_xref)
			info.append("descriptor %s" % (descriptor_xref))

			if PDFName("/FontFile") in descriptor.content:
				fontfile_obj = self._pdf.lookup(descriptor.content[PDFName("/FontFile")])
				l1 = fontfile_obj.content[PDFName("/Length1")]
				l2 = fontfile_obj.content[PDFName("/Length2")]
				l3 = fontfile_obj.content[PDFName("/Length3")]
				font = fontfile_obj.stream.decode()
				p1 = font[ 0 : l1 ]
				p2 = font[ l1 : l1 + l2 ]
				with open("ff1", "wb") as f:
					f.write(p1)
				with open("ff2", "wb") as f:
					f.write(p2)

			if PDFName("/CharSet") in descriptor.content:
				descriptor_charset = descriptor.content.get(PDFName("/CharSet"))
				descriptor_charset = descriptor_charset.decode("ascii").strip("/").split("/")
				descriptor_charset = [ char for char in descriptor_charset if char != "" ]
				info.append("CharSet length %d" % (len(descriptor_charset)))

		print("Font object (%s font) ObjId=%d: %s" % (ftype, font_obj.objid, ", ".join(info)))
		self._dump_object(font_obj)
		print("-" * 120)

	def _print_sig(self, sig_obj):
		info = [ ]
		print("Signature object ObjId=%d: %s" % (sig_obj.objid, ", ".join(info)))
		self._dump_object(sig_obj)
		print("-" * 120)

	def run(self):
		for obj in self._pdf:
			objtype = obj.getattr(PDFName("/Type"))
			if objtype == PDFName("/Font"):
				self._print_font(obj)

		for obj in self._pdf:
			objtype = obj.getattr(PDFName("/Type"))
			if objtype == PDFName("/Sig"):
				self._print_sig(obj)
