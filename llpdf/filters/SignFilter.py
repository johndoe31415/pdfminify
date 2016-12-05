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
import subprocess
import pkgutil
from llpdf.PDFResources import PDFResources
from llpdf.types.PDFObject import PDFObject
from llpdf.types.PDFName import PDFName
from llpdf.types.PDFXRef import PDFXRef
from llpdf.types.MarkerObject import MarkerObject
from llpdf.EncodeDecode import EncodedObject
from llpdf.font.T1Font import T1Font
from llpdf.types.Flags import AnnotationFlag, FieldFlag, SignatureFlag
from llpdf.types.Timestamp import Timestamp
from llpdf.Measurements import Measurements
from llpdf.tools.OpenSSLVersion import OpenSSLVersion
from .PDFFilter import PDFFilter

class SignFilter(PDFFilter):
	_signature_box_aspect_ratio = 16 / 9

	def _get_signature_extents(self):
		posx = Measurements.convert(25, "mm", "native")
		posy = Measurements.convert(25, "mm", "native")
		width = round(Measurements.convert(50, "mm", "native"))
		height = round(width / self._signature_box_aspect_ratio)
		return [ posx, posy, width, height ]

	def _get_signature_rect(self):
		(posx, posy, width, height) = self._get_signature_extents()
		return [ posx, posy, posx + width, posy + height ]

	def _get_signature_bbox(self):
		(posx, posy, width, height) = self._get_signature_extents()
		return [ 0, 0, width, height ]

	def _get_cert_subject(self, pemcertfile):
		cmd = [ "openssl", "x509", "-in", pemcertfile, "-noout", "-subject" ]
		subject = subprocess.check_output(cmd)
		subject = subject.decode().rstrip("\r\n")
		assert(subject.startswith("subject= "))
		subject = subject[10:]
		return subject

	def _do_sign(self, bin_data):
		cmd = [ "openssl", "cms", "-sign", "-binary" ]
		cmd += [ "-signer", self._args.sign_cert ]
		cmd += [ "-inkey", self._args.sign_key ]
		if self._args.sign_chain:
			cmd += [ "-certfile", self._args.sign_chain ]
		cmd += [ "-outform", "der" ]
		signature = subprocess.check_output(cmd, input = bin_data)
		return signature

	def _create_object(self, content, raw_stream = None):
		objid = self._pdf.get_free_objid()
		obj = PDFObject.create(objid = objid, gennum = 0, content = content)
		if raw_stream is not None:
			obj.set_stream(EncodedObject.create(raw_stream))
		self._pdf.replace_object(obj)
		return PDFXRef(objid, 0)

	def _property_dict(self):
		openssl_version = OpenSSLVersion.get()
		properties = {
			PDFName("/App"): {
				PDFName("/Name"):			PDFName("/PDFMinify"),
				PDFName("/OS"):				[ PDFName("/Linux") ],
				PDFName("/R"):				llpdf.VERSION_INT,
				PDFName("/REx"):			llpdf.VERSION.encode("ascii"),
				PDFName("/TrustedMode"):	False,
			},
			PDFName("/Filter"): {
				PDFName("/Name"):			PDFName("/OpenSSL"),
				PDFName("/Date"):			openssl_version.date.encode("ascii"),
				PDFName("/REx"):			openssl_version.text.encode(),
				PDFName("/R"):				int(openssl_version),
			},
		}
		return properties

	def _sign_pdf(self):
		placeholder_signature = self._do_sign(b"")
		self._sig_length_bytes = len(placeholder_signature)
		content = {
			PDFName("/Type"):			PDFName("/Sig"),
			PDFName("/Filter"):			PDFName("/Adobe.PPKLite"),
			PDFName("/SubFilter"):		PDFName("/adbe.pkcs7.detached"),
			PDFName("/ByteRange"):		MarkerObject("sig_byterange", raw = "[ " + (" " * (4 * 10)) + "  "),
			PDFName("/Contents"):		MarkerObject("sig_contents", child = placeholder_signature),
			PDFName("/M"):				Timestamp.localnow().format_pdf().encode("ascii"),
			PDFName("/Prop_Build"):		self._property_dict(),
		}
		if self._args.signer is not None:
			content[PDFName("/Name")] = self._args.signer.encode("latin1")
		if self._args.sign_location is not None:
			content[PDFName("/Location")] = self._args.sign_location.encode("latin1")
		if self._args.sign_contact_info is not None:
			content[PDFName("/ContactInfo")] = self._args.sign_contact_info.encode("latin1")
		if self._args.sign_reason is not None:
			content[PDFName("/Reason")] = self._args.sign_reason.encode("latin1")
		return self._create_object(content)

	def _get_font_reference(self):
		# Load the T1 font first
		#t1 = T1Font.from_pfb_file("/usr/share/texlive/texmf-dist/fonts/type1/adobe/courier/pcrb8a.pfb")
		t1 = T1Font.from_pfb_file("/usr/share/texlive/texmf-dist/fonts/type1/bitstrea/charter/bchr8a.pfb")

		# Then add the FontFile to the PDF first
		fontfile = t1.get_fontfile_object(self._pdf.get_free_objid())
		self._pdf.replace_object(fontfile)

		# Create a font descriptor for that font
		descriptor = t1.get_font_descriptor_object(self._pdf.get_free_objid(), fontfile.xref)
		self._pdf.replace_object(descriptor)

		# Then create the font object itself
		font = t1.get_font_object(self._pdf.get_free_objid(), descriptor.xref)
		self._pdf.replace_object(font)

		return font.xref

	def _get_signing_text(self):
		t1 = T1Font.from_pfb_file("/usr/share/texlive/texmf-dist/fonts/type1/bitstrea/charter/bchr8a.pfb")
		subject = self._get_cert_subject(self._args.sign_cert)
		line = "Subject: " + subject
		lines = t1.wrap_text(line, 6 * 1000)
		text = [ "(%s) Tj" % (line) for line in lines ]
		text = " T* ".join(text)
		return text.encode("ascii")

	def _generate_form(self):
		form_graphics = PDFResources(pkgutil.get_data("llpdf.resources", "signing_graphics.pdf"))
		mapping = self._pdf.coalesce(form_graphics, additional_cross_references = { PDFXRef(9998, 0): self._get_font_reference() })
		resources_xref = mapping[PDFXRef(9999, 0)]
		form_data = pkgutil.get_data("llpdf.resources", "signing_form.pdf")
		form_data = form_data.replace(b"%${TEXT}", self._get_signing_text())
		return self._create_object({
			PDFName("/Type"):			PDFName("/XObject"),
			PDFName("/Subtype"):		PDFName("/Form"),
			PDFName("/BBox"):			self._get_signature_bbox(),
			PDFName("/Resources"):		resources_xref,
		}, form_data)

	def _generate_lock(self):
		return self._create_object({
			PDFName("/Type"):	PDFName("/SigFieldLock"),
			PDFName("/P"):		1,
			PDFName("/Action"):	PDFName("/All"),
		})

	def _generate_signature_annotation(self, signature_xref, form_xref, lock_obj_xref, annotated_page_xref):
		return self._create_object({
			PDFName("/Type"):			PDFName("/Annot"),
			PDFName("/Subtype"):		PDFName("/Widget"),
			PDFName("/Rect"):			self._get_signature_rect(),
			PDFName("/T"):				b"Digital Signature",							# Text
			PDFName("/P"):				annotated_page_xref,							# Indirect reference to page object
			PDFName("/F"):				AnnotationFlag.Locked | AnnotationFlag.Print,	# Flags as Acrobat sets them ("Locked" is required or annotation won't show up)
			PDFName("/AP"): {															# Appearance dictionary
				PDFName("/N"): form_xref,
			},
			PDFName("/Lock"):			lock_obj_xref,
			PDFName("/FT"):				PDFName("/Sig"),								# Field type
			PDFName("/V"):				signature_xref,									# Field value
			PDFName("/Ff"):				int(FieldFlag.NoExport),						# Field flags as by PDF-XChange (When setting "ReadOnly", it doesn't work in X-Change)
		})

	def run(self):
		self._log.debug("Signing document.")
		for page in self._pdf.pages:
			annotated_page_xref = page.xref
			break
		signature_xref = self._sign_pdf()
		form_xref = self._generate_form()
		lock_xref = self._generate_lock()

		annot_xref = self._generate_signature_annotation(signature_xref, form_xref, lock_xref, annotated_page_xref)
		annots_xref = self._create_object([ annot_xref ])
		page = self._pdf.lookup(annotated_page_xref)

		# TODO: What if there are already annotations? append instead of overwrite
		assert(PDFName("/Annots") not in page.content)
		page.content[PDFName("/Annots")] = annots_xref

		root_xref = self._pdf.trailer[PDFName("/Root")]
		root_obj = self._pdf.lookup(root_xref)

		# Write the interactive form dictionary
		assert(PDFName("/AcroForm") not in page.content)
		root_obj.content[PDFName("/AcroForm")] = self._create_object({
			PDFName("/Fields"):		[ annot_xref ],
			PDFName("/SigFlags"):	SignatureFlag.SignaturesExist | SignatureFlag.AppendOnly,
		})


	def fixup(self, writer):
		filesize = writer.outfile.filesize()
		content_range = [ writer.serializer.get_mark("sig_contents") + 1, writer.serializer.get_mark("sig_contents") + 1 + (self._sig_length_bytes * 2) ]
		self._log.debug("Signature content range offsets: 0x%x to 0x%x (exclusive)", content_range[0], content_range[1])
		byterange = [
			[ 0, content_range[0] - 1 ],
			[ content_range[1] + 1, filesize - content_range[1] - 1 ],
		]
		byterange_str = "[ " + " ".join(str(item) for sublist in byterange for item in sublist) + " ]"

		self._log.debug("Signature byte range: %s: \"%s\"", byterange, byterange_str)
		writer.outfile.seek(writer.serializer.get_mark("sig_byterange"))
		writer.outfile.write(byterange_str.encode("ascii"))

		# Now read back in signed data
		signed_payload = bytearray()
		for (offset, length) in byterange:
			writer.outfile.seek(offset)
			data = writer.outfile.read(length)
			assert(length == len(data))
			signed_payload += data
		signature = self._do_sign(signed_payload)
		hex_signature = signature.hex().encode("ascii")

		# Patch into PDF
		writer.outfile.seek(writer.serializer.get_mark("sig_contents") + 1)
		writer.outfile.write(hex_signature)
