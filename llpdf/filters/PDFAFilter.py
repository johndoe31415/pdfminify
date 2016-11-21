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
from .PDFFilter import PDFFilter
from llpdf.types.PDFName import PDFName
from llpdf.types.PDFObject import PDFObject

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
         <xmp:CreatorTool>cairo 1.14.6 (http://cairographics.org)</xmp:CreatorTool>
         <xmp:ModifyDate>2016-11-21T12:02:03-08:00</xmp:ModifyDate>
         <xmp:CreateDate>2016-11-21T12:02:03-08:00</xmp:CreateDate>
         <xmp:MetadataDate>2016-11-21T12:02:03-08:00</xmp:MetadataDate>
         <pdf:Producer>cairo 1.14.6 (http://cairographics.org)</pdf:Producer>
         <dc:format>application/pdf</dc:format>
         <xmpMM:DocumentID>uuid:acc9d5ca-05a3-4df7-b9b4-2a284089bae3</xmpMM:DocumentID>
         <xmpMM:InstanceID>uuid:3316c452-5ba5-4d57-8ebf-1f2cd7c4bcea</xmpMM:InstanceID>
         <xmpMM:RenditionClass>default</xmpMM:RenditionClass>
         <xmpMM:VersionID>1</xmpMM:VersionID>
         <xmpMM:History>
            <rdf:Seq>
               <rdf:li rdf:parseType="Resource">
                  <stEvt:action>converted</stEvt:action>
                  <stEvt:instanceID>uuid:acc9d5ca-05a3-4df7-b9b4-2a284089bae3</stEvt:instanceID>
                  <stEvt:parameters>converted to PDF/A-1b</stEvt:parameters>
                  <stEvt:softwareAgent>Preflight</stEvt:softwareAgent>
                  <stEvt:when>2016-11-21T12:02:03-08:00</stEvt:when>
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
	def _strip_key(self, key):
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

	def _add_xmp_metadata(self):
		stream = _xpacket_template.encode("utf-8")
		content = {
			PDFName("/Type"):			PDFName("/Metadata"),
			PDFName("/Subtype"):		PDFName("/XML"),
			PDFName("/Length"):			len(stream),
		}
		objid = self._pdf.crappy_workaround_get_free_objid()
		pdf_object = PDFObject.create(objid, gennum = 0, content = content, stream = stream)
		self._pdf.replace_object(pdf_object)
		return pdf_object.xref

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

		# Add color profile data
		color_profile_xref = self._add_color_profile()

		# Add color intent object
		color_intent_xref = self._add_color_intent(color_profile_xref)

		# Add XMP metadata
		metadata_xref = self._add_xmp_metadata()

		# Set output intent and metadata reference for all catalogs
		for obj in self._pdf:
			if isinstance(obj.content, dict) and (PDFName("/Type") in obj.content) and (obj.content[PDFName("/Type")] == PDFName("/Catalog")):
				obj.content[PDFName("/OutputIntents")] = color_intent_xref
				obj.content[PDFName("/Metadata")] = metadata_xref

		# Set all annotations with annotation flag "printable" (4)
		for obj in self._pdf:
			if isinstance(obj.content, dict) and (PDFName("/Type") in obj.content) and (obj.content[PDFName("/Type")] == PDFName("/Annot")):
				obj.content[PDFName("/F")] = 4
