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
import re
import enum
import subprocess
import logging
from .PnmPicture import PnmPictureFormat, PnmPicture
from llpdf.types.PDFName import PDFName
from llpdf.Exceptions import UnsupportedImageException
from llpdf.EncodeDecode import Filter

class PDFImageColorSpace(enum.IntEnum):
	DeviceRGB = 1
	DeviceGray = 2

class PDFImage(object):
	_log = logging.getLogger("llpdf.img.PDFImage")

	def __init__(self, width, height, colorspace, bits_per_component, imgdata, inverted):
		self._width = width
		self._height = height
		self._colorspace = colorspace
		self._bits_per_component = bits_per_component
		self._imgdata = imgdata
		self._inverted = inverted
		self._alpha = None

	def set_alpha(self, alpha_image):
		assert(self.width == alpha_image.width)
		assert(self.height == alpha_image.height)
		self._alpha = alpha_image

	@classmethod
	def create_raw_from_object(cls, xobj):
		if (PDFName("/Width") not in xobj.content):
			raise UnsupportedImageException("Unsupported image without width: %s" % (xobj))

		width = xobj.content[PDFName("/Width")]
		height = xobj.content[PDFName("/Height")]
		colorspace_info = xobj.content[PDFName("/ColorSpace")]
		bits_per_component = xobj.content[PDFName("/BitsPerComponent")]
		filter_info = xobj.content[PDFName("/Filter")]
		decode = xobj.content.get(PDFName("/Decode"))
		if (decode is None) or (decode == [ 0, 1 ]):
			inverted = False
		elif decode == [ 1, 0 ]:
			inverted = True
		else:
			raise UnsupportedImageException("Cannot generate PDFImage object with non-trivial value decode array: %s" % (decode))
		if isinstance(filter_info, list):
			if len(filter_info) != 1:
				raise UnsupportedImageException("Multi-filter application is unsupported as of now: %s." % (filter_info))
			filter_info = filter_info[0]
		if isinstance(colorspace_info, list):
			raise UnsupportedImageException("Indexed images are currently unsupported: %s" % (colorspace_info))
		colorspace = {
			PDFName("/DeviceRGB"):			PDFImageColorSpace.DeviceRGB,
			PDFName("/DeviceGray"):			PDFImageColorSpace.DeviceGray,
		}.get(colorspace_info)
		if colorspace is None:
			raise UnsupportedImageException("Unsupported image color space '%s'." % (colorspace_info))
		return cls(width = width, height = height, colorspace = colorspace, bits_per_component = bits_per_component, imgdata = xobj.stream, inverted = inverted)

	@classmethod
	def create_from_object(cls, xobj, alpha_xobj = None):
		image = cls.create_raw_from_object(xobj)
		if alpha_xobj is not None:
			alpha_channel = cls.create_raw_from_object(alpha_xobj)
			image._alpha = alpha_channel
		return image

	@property
	def width(self):
		return self._width

	@property
	def height(self):
		return self._height

	@property
	def imgdata(self):
		return self._imgdata

	@property
	def colorspace(self):
		return self._colorspace

	@property
	def bits_per_component(self):
		return self._bits_per_component

	@property
	def inverted(self):
		return self._inverted

	@property
	def alpha(self):
		return self._alpha

	@property
	def total_size(self):
		size = len(self)
		if self.alpha is not None:
			size += len(self.alpha)
		return size

	@property
	def extension(self):
		return self.extension_for_filter(self.imgdata.filtering)

	@property
	def raw_extension(self):
		return self.raw_extension_for_filter(self.imgdata.filtering)

	@classmethod
	def extension_for_filter(cls, filtering):
		return {
			Filter.FlateDecode:		"pnm",
			Filter.RunLengthDecode:	"pnm",
			Filter.DCTDecode:		"jpg",
		}[filtering]

	@classmethod
	def raw_extension_for_filter(cls, filtering):
		return {
			Filter.FlateDecode:		"z",
			Filter.RunLengthDecode:	"rle",
			Filter.DCTDecode:		"jpg",
		}[filtering]

	def get_pixeldata(self):
		return self._imgdata.decode()

	def pixel_hash(self):
		return hashlib.md5(self.get_pixeldata()).hexdigest()

	def get_pnm(self):
		pixeldata = self.get_pixeldata()
		if (self.colorspace == PDFImageColorSpace.DeviceRGB) and (self.bits_per_component == 8):
			image = PnmPicture(width = self.width, height = self.height, data = pixeldata, img_format = PnmPictureFormat.Pixmap)
		elif (self.colorspace == PDFImageColorSpace.DeviceGray) and (self.bits_per_component == 8):
			if len(pixeldata) == 2 * self.width * self.height:
				# This is odd. On some LaTeX documents, the alpha channel image
				# is double of what the actual metadata indicates. Truncate
				self._log.warning("Warning: Duplicate image size of %s truncated from %d to %d bytes.", str(self), len(pixeldata), len(pixeldata) // 2)
				pixeldata = pixeldata[ : len(pixeldata) // 2]
			image = PnmPicture(width = self.width, height = self.height, data = pixeldata, img_format = PnmPictureFormat.Graymap)
		elif (self.colorspace == PDFImageColorSpace.DeviceGray) and (self.bits_per_component == 1):
			image = PnmPicture(width = self.width, height = self.height, data = pixeldata, img_format = PnmPictureFormat.Bitmap)
			image.invert()
		else:
			raise Exception("Creating PNM from this ColorSpace/BitsPerComponent combination is unsupported (%s/%d)." % (self.colorspace, self.bits_per_component))
		return image

	@staticmethod
	def _get_image_width_height(filename):
		output = subprocess.check_output([ "file", filename ])
		output = output.decode("utf-8")
		regex = re.compile(r"[,=] (?P<width>\d+)(x| x )(?P<height>\d+),")
		result = regex.search(output)
		if result is None:
			raise Exception("Cannot determine size from image.")
		result = result.groupdict()
		return (int(result["width"]), int(result["height"]))

	def writefile(self, filename, write_raw_data = False):
		if self.imgdata.lossless and (not write_raw_data):
			pnm_image = self.get_pnm()
			pnm_image.write_file(filename)
		else:
			with open(filename, "wb") as f:
				f.write(self._imgdata.encoded_data)

	def __len__(self):
		return len(self._imgdata)

	def _raw_str(self):
		return "Img<%d x %d, %s-%d, %s>" % (self.width, self.height, self.colorspace.name, self.bits_per_component, self.imgdata.filtering.name)

	def __str__(self):
		if self.alpha is None:
			return self._raw_str()
		else:
			return "%s with alpha %s" % (self._raw_str(), self.alpha._raw_str())
