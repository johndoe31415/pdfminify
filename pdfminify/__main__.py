#!/usr/bin/env python3
#	pdfminify - Tool to minify PDF files.
#	Copyright (C) 2016-2020 Johannes Bauer
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

import sys
import os
import logging
import argparse
import llpdf
import llpdf.tests
import pdfminify
from pdfminify.FriendlyArgumentParser import FriendlyArgumentParser
from pdfminify.FilesizeFormatter import FilesizeFormatter

python_version = sys.version_info[:3]
min_python_version = (3, 5, 0)
if python_version < min_python_version:
	print("Error: You need at least Python %s to run pdfminify, but you're using Python %s." % ( ".".join(str(x) for x in min_python_version), ".".join(str(x) for x in python_version)), file = sys.stderr)
	sys.exit(1)

if (len(sys.argv) >= 2) and (sys.argv[1] == "--test"):
	llpdf.tests.run(terminate_after = True)

def _offset(text):
	text = text.split(",")
	if len(text) != 2:
		raise argparse.ArgumentTypeError("expected two comma-separated values, but %d given." % (len(text)))
	return [ float(value) for value in text ]

def _cropbox(text):
	text = text.split(",")
	if len(text) != 4:
		raise argparse.ArgumentTypeError("expected four comma-separated values, but %d given." % (len(text)))
	return [ float(value) for value in text ]

def _intrange(minvalue, maxvalue):
	def convert(text):
		value = int(text)
		if (minvalue is not None) and (value < minvalue):
			raise argparse.ArgumentTypeError("value must be at least %d." % (minvalue))
		if (maxvalue is not None) and (value > maxvalue):
			raise argparse.ArgumentTypeError("value may be at most %d." % (maxvalue))
		return value
	return convert

epilog = "pdfminify version %s; llpdf version: %s" % (pdfminify.VERSION, llpdf.VERSION)

parser = FriendlyArgumentParser(prog = "pdfminify", description = "Minifies PDF files, can crop them, convert them to PDF/A-1b and sign them cryptographically.", epilog = epilog)
parser.add_argument("-d", "--target-dpi", metavar = "dpi", type = int, default = 150, help = "Default resoulution to which images will be resampled at. Defaults to %(default)s dots per inch (dpi).")
parser.add_argument("-j", "--jpeg-images", action = "store_true", help = "Convert images to JPEG format. This means that lossy compression is used that however often yields a much higher compression ratio.")
parser.add_argument("--jpeg-quality", metavar = "percent", type = _intrange(0, 100), default = 85, help = "When converting images to JPEG format, the parameter gives the compression quality. It is an integer from 0-100 (higher is better, but creates also larger output files).")
parser.add_argument("--no-downscaling", action = "store_true", help = "Do not apply downscaling filter on the PDF, take all images as they are.")

parser.add_argument("--cropbox", metavar = "x,y,w,h", type = _cropbox, help = "Crop pages by additionally adding a /CropBox to all pages of the PDF file. Pages will be cropped at offset (x, y) to a width (w, h). The unit in which offset, width and height are given can be specified using the --unit parameter.")
parser.add_argument("--unit", choices = llpdf.Measurements.list_units(), default = "native", help = "Specify the unit of measurement that is used for input and output. Can be any of %(choices)s, defaults to %(default)s. One native PDF unit equals 1/72th of an inch.")

parser.add_argument("--one-bit-alpha", action = "store_true", help = "Force all alpha channels in images to use a color depth of one bit. This will make transparent images have rougher edges, but saves additional space.")
parser.add_argument("--remove-alpha", action = "store_true", help = "Entirely remove the alpha channel (i.e., transparency) of all images. The color which with transparent areas are replaced with can be specified using the --background-color command line option.")
parser.add_argument("--background-color", metavar = "color", type = str, default = "white", help = "When removing alpha channels, specifies the color that should be used as background. Defaults to %(default)s. Hexadecimal values can be specified as well in the format '#rrggbb'.")

parser.add_argument("--strip-metadata", action = "store_true", help = "Strip metadata inside PDF objects that is not strictly required, such as /PTEX.* entries inside object content.")

parser.add_argument("--saveimgdir", metavar = "path", type = str, help = "When specified, save all handled images as individual files into the specified directory. Useful for image extraction from a PDF as well as debugging.")
parser.add_argument("--raw-output", action = "store_true", help = "When saving images externally, save them in exactly the format in which they're also present inside the PDF. Note that this will produce raw image files in some cases which won't have any header (but just contain pixel data). Less useful for image extraction, but can make sense for debugging.")
parser.add_argument("--pretty-pdf", action = "store_true", help = "Write pretty PDF files, i.e., format all dictionaries so they're well-readable regarding indentation. Increases required file size a tiny bit and increases generation time of the PDF a little, but produces easily debuggable PDFs.")

parser.add_argument("--no-xref-stream", action = "store_true", help = "Do not write the XRef table as a XRef stream, but instead write a classical PDF XRef table and trailer. This will increase the file size a bit, but might improve compatibility with old PDF readers (XRef streams are supported only starting with PDF 1.5). XRef-streams are a prerequisite to object stream compression, so if XRef-streams are disabled, so will also be object streams (e.g, --no-object-streams is implied).")
parser.add_argument("--no-object-streams", action = "store_true", help = "Do not compress objects into object-streams. Object stream compression is introduced with PDF 1.5 and means that multiple simple objects (without any stream data) are concatenated together and compressed together into one large stream object.")
parser.add_argument("--pdfa-1b", action = "store_true", help = "Try to create a PDF/A-1b compliant PDF document. Implies --no-xref-stream, --no-object-streams, --remove-alpha, removes transpacency groups and adds a PDF/A entry into XMP metadata.")
parser.add_argument("--color-profile", metavar = "iccfile", help = "When creating a PDF/A-1b PDF, gives the Internal Color Consortium (ICC) color profile that should be embedded into the PDF as part of the output intent. When omitted, it defaults to the sRGB IEC61966 v2 \"black scaled\" profile which is included within pdfminify.")

parser.add_argument("--sign-cert", metavar = "certfile", help = "pdfminify can additionally cryptographically sign your result PDF file with an X.509 certificate and corresponding key. This parameter specifies the certificate filename.")
parser.add_argument("--sign-key", metavar = "keyfile", help = "This parameter specifies the key filename, also in PEM format.")
parser.add_argument("--sign-chain", metavar = "pemfile", help = "When signing a PDF, this gives the PEM-formatted certificate chain file. Can be omitted if this should not be included in the PKCS#7 signature.")
parser.add_argument("--signer", metavar = "name", help = "The name of the person responsible for signing the document.")
parser.add_argument("--sign-location", metavar = "hostname", help = "The location of the signing; usually this is the hostname of the computer that the signature is generated on.")
parser.add_argument("--sign-contact-info", metavar = "infotext", help = "A contact information field under which the signer can be reached. Usually a phone number of email address.")
parser.add_argument("--sign-reason", metavar = "reason", help = "The reason why the document was signed.")
parser.add_argument("--sign-page", metavar = "pageno", type = int, default = 1, help = "Page number on which the signature should be displayed. Defaults to %(default)d.")
parser.add_argument("--sign-font", metavar = "pfbfile", type = str, help = "To be able to include metadata text in the signature form, a T1 font must be included into the PDF. This gives the filename of the font that is to be used for that purpose. Must be in PFB (PostScript Font Binary) file format and will be included in the result PDF in full (i.e., not reduced to the glyphs that are actually needed). Defaults to the Bitstream Charter Serif font that is included within pdfminify.")
parser.add_argument("--sign-pos", metavar = "x,y", type = _offset,  help = "Determines where the signature will be placed on the page. Units are determined by the --unit variable and the position is relative to lower left corner.")

parser.add_argument("--embed-payload", metavar = "path", type = str, help = "Embed an opaque file as a payload into the PDF as a valid PDF object. This is useful only if you want to place an easter egg inside your PDF file.")
parser.add_argument("--no-pdf-tagging", action = "store_true", help = "Omit tagging the PDF file with a reference to pdfminify and the used version.")
parser.add_argument("--decompress-data", action = "store_true", help = "Decompress all FlateDecode compressed data in the file. Useful only for debugging.")
parser.add_argument("--analyze", action = "store_true", help = "Perform an analysis of the read PDF file and dump out useful information about it.")
parser.add_argument("--dump-xref-table", action = "store_true", help = "Dump out the XRef table that was read from the input PDF file. Mainly useful for debugging.")
parser.add_argument("--no-filters", action = "store_true", help = "Do not apply any filters on the source PDF whatsoever, just read it in and write it back out. This is useful to reformat a PDF and/or debug the PDF reader/writer facilities without introducing other sources of malformed PDF generation.")
parser.add_argument("-v", "--verbose", action = "count", default = 0, help = "Show verbose messages during conversation. Can be specified multiple times to increase log level.")
parser.add_argument("infile", metavar = "pdf_in", type = str, help = "Input PDF file.")
parser.add_argument("outfile", metavar = "pdf_out", type = str, help = "Output PDF file.")
args = parser.parse_args(sys.argv[1:])

if (args.sign_cert is None) ^ (args.sign_key is None):
	print("Specifying only a key or only a certificate does not make sense; you need to specify either both or none.", file = sys.stderr)
	sys.exit(1)

llpdf.configure_logging(args.verbose)
llpdf.Measurements.set_default_unit(args.unit)

pdf_filter_classes = [ filter_class for filter_class in [
	llpdf.filters.AnalyzeFilter if args.analyze else None,
	llpdf.filters.RemoveDuplicateImageOptimization if (not args.no_filters) else None,
	llpdf.filters.RemoveMetadataFilter if (args.strip_metadata and (not args.no_filters)) else None,
	llpdf.filters.FlattenImageOptimization if ((args.remove_alpha or args.pdfa_1b) and (not args.no_filters)) else None,
	llpdf.filters.DownscaleImageOptimization if ((args.saveimgdir is not None) or ((not args.no_downscaling) and (not args.no_filters))) else None,
	llpdf.filters.AddCropBoxFilter if (args.cropbox and (not args.no_filters)) else None,
	llpdf.filters.ExplicitLengthFilter if (not args.no_filters) else None,
	llpdf.filters.DeleteOrphanedObjectsFilter if (not args.no_filters) else None,
	llpdf.filters.TagFilter if (not (args.no_filters or args.no_pdf_tagging)) else None,
	llpdf.filters.EmbedPayloadFilter if (args.embed_payload is not None) else None,
	llpdf.filters.PDFAFilter if (args.pdfa_1b and (not args.no_filters)) else None,
	llpdf.filters.DecompressFilter if args.decompress_data else None,
	llpdf.filters.SignFilter if args.sign_cert else None,
] if filter_class is not None ]
log = logging.getLogger("llpdf")

fsf = FilesizeFormatter()
old_size = os.stat(args.infile).st_size
pdf = llpdf.PDFReader().read(args.infile)

if args.dump_xref_table:
	pdf.xref_table.dump()

pdf_fixup_classes = [ ]
for (filter_no, pdf_filter_class) in enumerate(pdf_filter_classes, 1):
	log.debug("Running filter %d/%d: %s", filter_no, len(pdf_filter_classes), pdf_filter_class.__name__)
	pdf_filter = pdf_filter_class(pdf, args)
	pdf_filter.run()
	if args.verbose:
		log.debug("%s saved %s." % (pdf_filter_class.__name__, fsf(pdf_filter.bytes_saved)))
	if getattr(pdf_filter, "fixup", None) is not None:
		pdf_fixup_classes.append(pdf_filter)

use_xref_stream = not (args.no_xref_stream or args.pdfa_1b)
use_object_streams = not (args.no_object_streams or args.pdfa_1b)
writer = llpdf.PDFWriter(pretty = args.pretty_pdf, use_xref_stream = use_xref_stream, use_object_streams = use_object_streams)
writer.write(pdf, args.outfile)

if len(pdf_fixup_classes) > 0:
	for (filter_no, pdf_filter) in enumerate(pdf_fixup_classes, 1):
		log.debug("Running fixup %d/%d: %s", filter_no, len(pdf_fixup_classes), pdf_filter.__class__.__name__)
		pdf_filter.fixup(writer)

new_size = os.stat(args.outfile).st_size
if args.verbose:
	percent = 100 * new_size / old_size
	saved = old_size - new_size

	details = [ ]
	details.append("%.0f%% of original" % (percent))
	if saved > 0:
		details.append("%s saved" % (fsf(saved)))
	else:
		details.append("%s growth" % (fsf(-saved)))

	if saved > 0:
		details.append("ratio %.1f : 1" % (old_size / new_size))
	else:
		details.append("ratio 1 : %.1f" % (new_size / old_size))

	log.info("File size %s -> %s (%s)" % (fsf(old_size), fsf(new_size), ", ".join(details)))

