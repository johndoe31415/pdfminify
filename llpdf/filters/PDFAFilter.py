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
import uuid
import pkgutil

import llpdf
from .PDFFilter import PDFFilter
from llpdf.types.PDFName import PDFName
from llpdf.types.PDFObject import PDFObject
from llpdf.types.Timestamp import Timestamp
from llpdf.font.T1Font import T1Font
from llpdf.EncodeDecode import EncodedObject

class PDFAFilter(PDFFilter):
	def _add_color_profile(self):
		if self._args.color_profile is None:
			profile_data = pkgutil.get_data("llpdf.resources", "sRGB_IEC61966-2-1_black_scaled.icc")
		else:
			with open(self._args.color_profile, "rb") as f:
				profile_data = f.read()

		content = {
			PDFName("/N"):			3,
			PDFName("/Range"):		[ 0, 1, 0, 1, 0, 1 ],
		}
		objid = self._pdf.get_free_objid()
		pdf_object = PDFObject.create(objid, gennum = 0, content = content, stream = EncodedObject.create(profile_data))
		self._pdf.replace_object(pdf_object)
		return pdf_object.xref

	def _add_color_intent(self, color_profile_xref):
		content = [ {
			PDFName("/Type"):						PDFName("/OutputIntent"),
			PDFName("/DestOutputProfile"):			color_profile_xref,
			PDFName("/Info"):						b"sRGB IEC61966-2.1",
			PDFName("/OutputCondition"):			b"sRGB",
			PDFName("/OutputConditionIdentifier"):	b"Custom",
			PDFName("/RegistryName"):				b"",
			PDFName("/S"):							PDFName("/GTS_PDFA1"),
		} ]
		objid = self._pdf.get_free_objid()
		pdf_object = PDFObject.create(objid, gennum = 0, content = content)
		self._pdf.replace_object(pdf_object)
		return pdf_object.xref

	def _add_xmp_metadata(self):
		info_node_xref = self._pdf.trailer[PDFName("/Info")]
		info_node = self._pdf.lookup(info_node_xref)

		metadata_date = Timestamp.localnow()
		modify_date = Timestamp.frompdf(info_node.content[PDFName("/ModDate")].decode("ascii")) if (PDFName("/ModDate") in info_node.content) else metadata_date
		create_date = Timestamp.frompdf(info_node.content[PDFName("/CreationDate")].decode("ascii")) if (PDFName("/CreationDate") in info_node.content) else metadata_date
		xmp_metadata = {
			"creator_tool":			self._pdf.get_info("Creator"),
			"producer":				self._pdf.get_info("Producer"),
			"modify_date":			modify_date.format_xml(),
			"create_date":			create_date.format_xml(),
			"metadata_date":		metadata_date.format_xml(),
			"description":			self._pdf.get_info("Subject"),
			"title":				self._pdf.get_info("Title"),
			"creator":				self._pdf.get_info("Author"),
			"keywords":				self._pdf.get_info("Keywords"),
			"document_uuid":		str(uuid.uuid4()),
			"instance_uuid":		str(uuid.uuid4()),
			"pdfminify_version":	"pdfminify " + llpdf.VERSION,
		}

		xmp_metadata_template = pkgutil.get_data("llpdf.resources", "xmp_metadata.xml").decode("utf-8")
		stream = (xmp_metadata_template % xmp_metadata).encode("utf-8")
		content = {
			PDFName("/Type"):			PDFName("/Metadata"),
			PDFName("/Subtype"):		PDFName("/XML"),
		}
		objid = self._pdf.get_free_objid()
		pdf_object = PDFObject.create(objid, gennum = 0, content = content, stream = EncodedObject.create(stream, compress = False))
		self._pdf.replace_object(pdf_object)
		return pdf_object.xref

	@staticmethod
	def type2_font_glyph_count(glyph_widths):
		index = 0
		glyph_count = 0
		while index < len(glyph_widths):
			if isinstance(glyph_widths[index + 1], list):
				glyph_count += len(glyph_widths[index + 1])
				index += 2
			else:
				glyph_count += (glyph_widths[index + 1] - glyph_widths[index + 0] + 1)
				index += 3
		return glyph_count

	def run(self):
		# Put an ID into the PDF
		self._pdf.trailer[PDFName("/ID")] = [ os.urandom(16), os.urandom(16) ]

		# Do not interpolate any image objects
		for image_obj in self._pdf.image_objects:
			image_obj.content[PDFName("/Interpolate")] = False

		# No pages may be transparency groups
		for page in self._pdf.pages:
			if PDFName("/Group") in page.content:
				del page.content[PDFName("/Group")]

		# No transparency groups in Form XObjects
		for obj in self._pdf:
			if (obj.getattr(PDFName("/Type")) == PDFName("/XObject")) and (obj.getattr(PDFName("/Subtype")) == PDFName("/Form")) and (obj.getattr(PDFName("/Group")) is not None):
				del obj.content[PDFName("/Group")]

		# Add color profile data
		color_profile_xref = self._add_color_profile()

		# Add color intent object
		color_intent_xref = self._add_color_intent(color_profile_xref)

		# Add XMP metadata
		metadata_xref = self._add_xmp_metadata()

		# Set output intent and metadata reference for all catalogs
		for obj in self._pdf:
			if obj.getattr(PDFName("/Type")) == PDFName("/Catalog"):
				obj.content[PDFName("/OutputIntents")] = color_intent_xref
				obj.content[PDFName("/Metadata")] = metadata_xref

		# Set all annotations with annotation flag "printable" (4)
		for obj in self._pdf:
			if obj.getattr(PDFName("/Type")) == PDFName("/Annot"):
				obj.content[PDFName("/F")] = 4

		fixed_descriptors = set()
		for obj in list(self._pdf):
			if obj.getattr(PDFName("/Type")) == PDFName("/Font"):
				font_obj = obj

				if font_obj.getattr(PDFName("/Subtype")) == PDFName("/CIDFontType2"):
					# Type2 fonts need to have a CIDtoGIDMap
					font_obj.content[PDFName("/CIDToGIDMap")] = PDFName("/Identity")

				if PDFName("/FontDescriptor") in font_obj.content:
					font_descriptor_xref = font_obj.content[PDFName("/FontDescriptor")]
					if font_descriptor_xref in fixed_descriptors:
						continue
					fixed_descriptors.add(font_descriptor_xref)

					font_descriptor_obj = self._pdf.lookup(font_descriptor_xref)
					if font_obj.getattr(PDFName("/Subtype")) == PDFName("/Type1"):
						# Update Type1 font descriptors with missing CharSet entries
						font_file_obj = self._pdf.lookup(font_descriptor_obj.content[PDFName("/FontFile")])
						t1_font = T1Font.from_fontfile_obj(font_file_obj)
						font_descriptor_obj.content[PDFName("/CharSet")] = t1_font.charset_string
					elif font_obj.getattr(PDFName("/Subtype")) == PDFName("/CIDFontType2"):
						# Type2 font descriptors need to have a CIDSet
						glyph_count = self.type2_font_glyph_count(font_obj.content[PDFName("/W")])

						full_bytes = glyph_count // 8
						set_bits = glyph_count % 8
						last_byte = ((1 << set_bits) - 1) << (8 - set_bits)
						self._log.debug("Assuming CIDSet for %d glyphs of %d full 0xff bytes and a final value of 0x%x.", glyph_count, full_bytes, last_byte)

						cidset_objid = self._pdf.get_free_objid()
						stream = (bytes([ 0xff ]) * full_bytes) + bytes([ last_byte ])
						pdf_object = PDFObject.create(cidset_objid, gennum = 0, content = { }, stream = EncodedObject.create(stream))
						self._pdf.replace_object(pdf_object)

						font_descriptor_obj.content[PDFName("/CIDSet")] = pdf_object.xref
