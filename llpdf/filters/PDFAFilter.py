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
import zlib
import uuid
from .PDFFilter import PDFFilter
from llpdf.types.PDFName import PDFName
from llpdf.types.PDFObject import PDFObject
from llpdf.types.Timestamp import Timestamp
from llpdf.types.T1Font import T1Font

_xpacket_template = """\
<?xpacket begin="﻿" id="W5M0MpCehiHzreSzNTczkc9d"?>
<x:xmpmeta xmlns:x="adobe:ns:meta/" x:xmptk="Adobe XMP Core 5.4-c005 78.147326, 2012/08/23-13:03:03        ">
   <rdf:RDF xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#">
      <rdf:Description rdf:about=""
            xmlns:xmp="http://ns.adobe.com/xap/1.0/"
            xmlns:pdf="http://ns.adobe.com/pdf/1.3/"
            xmlns:dc="http://purl.org/dc/elements/1.1/"
            xmlns:xmpMM="http://ns.adobe.com/xap/1.0/mm/"
            xmlns:stEvt="http://ns.adobe.com/xap/1.0/sType/ResourceEvent#"
            xmlns:pdfaid="http://www.aiim.org/pdfa/ns/id/"
            xmlns:pdfaExtension="http://www.aiim.org/pdfa/ns/extension/"
            xmlns:pdfaSchema="http://www.aiim.org/pdfa/ns/schema#"
            xmlns:pdfaProperty="http://www.aiim.org/pdfa/ns/property#">
         <dc:format>application/pdf</dc:format>
		<dc:description>
            <rdf:Alt>
			   <rdf:li xml:lang="x-default">%(description)s</rdf:li>
            </rdf:Alt>
         </dc:description>
         <dc:title>
            <rdf:Alt>
               <rdf:li xml:lang="x-default">%(title)s</rdf:li>
            </rdf:Alt>
         </dc:title>
         <dc:creator>
            <rdf:Seq>
               <rdf:li>%(creator)s</rdf:li>
            </rdf:Seq>
         </dc:creator>
         <xmp:CreateDate>%(create_date)s</xmp:CreateDate>
         <xmp:CreatorTool>%(creator_tool)s</xmp:CreatorTool>
         <xmp:ModifyDate>%(modify_date)s</xmp:ModifyDate>
         <xmp:MetadataDate>%(metadata_date)s</xmp:MetadataDate>
         <pdf:Keywords>%(keywords)s</pdf:Keywords>
         <pdf:Producer>%(producer)s</pdf:Producer>
         <xmpMM:DocumentID>uuid:%(document_uuid)s</xmpMM:DocumentID>
         <xmpMM:InstanceID>uuid:%(instance_uuid)s</xmpMM:InstanceID>
         <xmpMM:RenditionClass>default</xmpMM:RenditionClass>
         <xmpMM:VersionID>1</xmpMM:VersionID>
         <xmpMM:History>
            <rdf:Seq>
               <rdf:li rdf:parseType="Resource">
                  <stEvt:action>converted</stEvt:action>
                  <stEvt:instanceID>uuid:%(document_uuid)s</stEvt:instanceID>
                  <stEvt:parameters>converted to PDF/A-1b</stEvt:parameters>
                  <stEvt:softwareAgent>pdfminify</stEvt:softwareAgent>
                  <stEvt:when>%(metadata_date)s</stEvt:when>
               </rdf:li>
            </rdf:Seq>
         </xmpMM:History>
         <pdfaid:part>1</pdfaid:part>
         <pdfaid:conformance>B</pdfaid:conformance>
         <pdfaExtension:schemas>
            <rdf:Bag>
               <rdf:li rdf:parseType="Resource">
                  <pdfaSchema:namespaceURI>http://ns.adobe.com/pdf/1.3/</pdfaSchema:namespaceURI>
                  <pdfaSchema:prefix>pdf</pdfaSchema:prefix>
                  <pdfaSchema:schema>Adobe PDF Schema</pdfaSchema:schema>
                  <pdfaSchema:property>
                     <rdf:Seq>
                        <rdf:li rdf:parseType="Resource">
                           <pdfaProperty:category>internal</pdfaProperty:category>
                           <pdfaProperty:description>A name object indicating whether the document has been modified to include trapping information</pdfaProperty:description>
                           <pdfaProperty:name>Trapped</pdfaProperty:name>
                           <pdfaProperty:valueType>Text</pdfaProperty:valueType>
                        </rdf:li>
                     </rdf:Seq>
                  </pdfaSchema:property>
               </rdf:li>
               <rdf:li rdf:parseType="Resource">
                  <pdfaSchema:namespaceURI>http://ns.adobe.com/xap/1.0/mm/</pdfaSchema:namespaceURI>
                  <pdfaSchema:prefix>xmpMM</pdfaSchema:prefix>
                  <pdfaSchema:schema>XMP Media Management Schema</pdfaSchema:schema>
                  <pdfaSchema:property>
                     <rdf:Seq>
                        <rdf:li rdf:parseType="Resource">
                           <pdfaProperty:category>internal</pdfaProperty:category>
                           <pdfaProperty:description>UUID based identifier for specific incarnation of a document</pdfaProperty:description>
                           <pdfaProperty:name>InstanceID</pdfaProperty:name>
                           <pdfaProperty:valueType>URI</pdfaProperty:valueType>
                        </rdf:li>
                        <rdf:li rdf:parseType="Resource">
                           <pdfaProperty:category>internal</pdfaProperty:category>
                           <pdfaProperty:description>The common identifier for all versions and renditions of a document.</pdfaProperty:description>
                           <pdfaProperty:name>OriginalDocumentID</pdfaProperty:name>
                           <pdfaProperty:valueType>URI</pdfaProperty:valueType>
                        </rdf:li>
                     </rdf:Seq>
                  </pdfaSchema:property>
               </rdf:li>
               <rdf:li rdf:parseType="Resource">
                  <pdfaSchema:namespaceURI>http://www.aiim.org/pdfa/ns/id/</pdfaSchema:namespaceURI>
                  <pdfaSchema:prefix>pdfaid</pdfaSchema:prefix>
                  <pdfaSchema:schema>PDF/A ID Schema</pdfaSchema:schema>
                  <pdfaSchema:property>
                     <rdf:Seq>
                        <rdf:li rdf:parseType="Resource">
                           <pdfaProperty:category>internal</pdfaProperty:category>
                           <pdfaProperty:description>Part of PDF/A standard</pdfaProperty:description>
                           <pdfaProperty:name>part</pdfaProperty:name>
                           <pdfaProperty:valueType>Integer</pdfaProperty:valueType>
                        </rdf:li>
                        <rdf:li rdf:parseType="Resource">
                           <pdfaProperty:category>internal</pdfaProperty:category>
                           <pdfaProperty:description>Amendment of PDF/A standard</pdfaProperty:description>
                           <pdfaProperty:name>amd</pdfaProperty:name>
                           <pdfaProperty:valueType>Text</pdfaProperty:valueType>
                        </rdf:li>
                        <rdf:li rdf:parseType="Resource">
                           <pdfaProperty:category>internal</pdfaProperty:category>
                           <pdfaProperty:description>Conformance level of PDF/A standard</pdfaProperty:description>
                           <pdfaProperty:name>conformance</pdfaProperty:name>
                           <pdfaProperty:valueType>Text</pdfaProperty:valueType>
                        </rdf:li>
                     </rdf:Seq>
                  </pdfaSchema:property>
               </rdf:li>
            </rdf:Bag>
         </pdfaExtension:schemas>
      </rdf:Description>
   </rdf:RDF>
</x:xmpmeta>
<?xpacket end="w"?>
"""

class PDFAFilter(PDFFilter):
	def _add_color_profile(self):
		profile_data = open("sRGB_IEC61966-2-1_black_scaled.icc", "rb").read()
		stream = zlib.compress(profile_data)
		content = {
			PDFName("/Filter"):		PDFName("/FlateDecode"),
			PDFName("/N"):			3,
			PDFName("/Range"):		[ 0, 1, 0, 1, 0, 1 ],
			PDFName("/Length"):		len(stream),
		}
		objid = self._pdf.crappy_workaround_get_free_objid()
		pdf_object = PDFObject.create(objid, gennum = 0, content = content, stream = stream)
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
		objid = self._pdf.crappy_workaround_get_free_objid()
		pdf_object = PDFObject.create(objid, gennum = 0, content = content, stream = None)
		self._pdf.replace_object(pdf_object)
		return pdf_object.xref

	def _get_info(self, key):
		info_node_xref = self._pdf.trailer[PDFName("/Info")]
		info_node = self._pdf.lookup(info_node_xref)
		key = PDFName("/" + key)
		if key not in info_node.content:
			return ""
		else:
			return info_node.content[key].decode("utf-8")

	def _add_xmp_metadata(self):
		info_node_xref = self._pdf.trailer[PDFName("/Info")]
		info_node = self._pdf.lookup(info_node_xref)

		metadata_date = Timestamp.localnow()
		modify_date = Timestamp.frompdf(info_node.content[PDFName("/ModDate")].decode("ascii")) if (PDFName("/ModDate") in info_node.content) else metadata_date
		create_date = Timestamp.frompdf(info_node.content[PDFName("/CreationDate")].decode("ascii")) if (PDFName("/CreationDate") in info_node.content) else metadata_date
		xmp_metadata = {
			"creator_tool":		self._get_info("Creator"),
			"producer":			info_node.content[PDFName("/Producer")].decode("utf-8"),
			"modify_date":		modify_date.format_xml(),
			"create_date":		create_date.format_xml(),
			"metadata_date":	metadata_date.format_xml(),
			"description":		self._get_info("Subject"),
			"title":			self._get_info("Title"),
			"creator":			self._get_info("Author"),
			"keywords":			self._get_info("Keywords"),
			"document_uuid":	str(uuid.uuid4()),
			"instance_uuid":	str(uuid.uuid4()),
		}

		stream = (_xpacket_template % xmp_metadata).encode("utf-8")
		content = {
			PDFName("/Type"):			PDFName("/Metadata"),
			PDFName("/Subtype"):		PDFName("/XML"),
			PDFName("/Length"):			len(stream),
		}
		objid = self._pdf.crappy_workaround_get_free_objid()
		pdf_object = PDFObject.create(objid, gennum = 0, content = content, stream = stream)
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
						charset = t1_font.get_charset()
						font_descriptor_obj.content[PDFName("/CharSet")] = charset
					elif font_obj.getattr(PDFName("/Subtype")) == PDFName("/CIDFontType2"):
						# Type2 font descriptors need to have a CIDSet
						glyph_count = self.type2_font_glyph_count(font_obj.content[PDFName("/W")])

						full_bytes = glyph_count // 8
						set_bits = glyph_count % 8
						last_byte = ((1 << set_bits) - 1) << (8 - set_bits)
						self._log.debug("Assuming CIDSet for %d glyphs of %d full 0xff bytes and a final value of 0x%x.", glyph_count, full_bytes, last_byte)

						cidset_objid = self._pdf.crappy_workaround_get_free_objid()
						stream = zlib.compress((bytes([ 0xff ]) * full_bytes) + bytes([ last_byte ]))
						pdf_object = PDFObject.create(cidset_objid, gennum = 0, content = {
							PDFName("/Length"):		len(stream),
							PDFName("/Filter"):		PDFName("/FlateDecode"),
						}, stream = stream)
						self._pdf.replace_object(pdf_object)

						font_descriptor_obj.content[PDFName("/CIDSet")] = pdf_object.xref


