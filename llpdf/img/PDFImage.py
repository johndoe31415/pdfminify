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

import time
import hashlib
import re
import zlib
import enum
import subprocess
from tempfile import NamedTemporaryFile
from .PnmPicture import PnmPictureFormat, PnmPicture
from llpdf.types.PDFName import PDFName

class PDFImageType(enum.IntEnum):
	FlateDecode = 1
	DCTDecode = 2
	RunLengthDecode = 3

class PDFImageColorSpace(enum.IntEnum):
	DeviceRGB = 1
	DeviceGray = 2

class PDFImage(object):
	def __init__(self, width, height, colorspace, bits_per_component, imgdata, imgtype):
		self._width = width
		self._height = height
		self._colorspace = colorspace
		self._bits_per_component = bits_per_component
		self._imgdata = imgdata
		self._imgtype = imgtype
		self._alpha = None
		assert(isinstance(self._imgtype, PDFImageType))

	def set_alpha(self, alpha_image):
		assert(self.width == alpha_image.width)
		assert(self.height == alpha_image.height)
		self._alpha = alpha_image

	@classmethod
	def create_raw_from_object(cls, xobj):
		width = xobj.content[PDFName("/Width")]
		height = xobj.content[PDFName("/Height")]
		colorspace_info = xobj.content[PDFName("/ColorSpace")]
		bits_per_component = xobj.content[PDFName("/BitsPerComponent")]
		filter_info = xobj.content[PDFName("/Filter")]
		if isinstance(filter_info, list):
			if len(filter_info) != 1:
				raise Exception("Multi-filter application is unsupported as of now: %s." % (filter_info))
			filter_info = filter_info[0]
		imgtype = {
			PDFName("/FlateDecode"):		PDFImageType.FlateDecode,
			PDFName("/DCTDecode"):			PDFImageType.DCTDecode,
			PDFName("/RunLengthDecode"):	PDFImageType.RunLengthDecode,
		}.get(filter_info)
		if imgtype is None:
			raise Exception("Cannot create image from unknown type '%s'." % (filter_info))
		colorspace = {
			PDFName("/DeviceRGB"):			PDFImageColorSpace.DeviceRGB,
			PDFName("/DeviceGray"):			PDFImageColorSpace.DeviceGray,
		}.get(colorspace_info)
		if colorspace is None:
			raise Exception("Unsupported image color space '%s'." % (colorspace_info))
		return cls(width = width, height = height, colorspace = colorspace, bits_per_component = bits_per_component, imgdata = xobj.stream, imgtype = imgtype)

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
	def imgtype(self):
		return self._imgtype

	@property
	def colorspace(self):
		return self._colorspace

	@property
	def bits_per_component(self):
		return self._bits_per_component

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
		return self.extension_for_imgtype(self.imgtype)

	@classmethod
	def extension_for_imgtype(cls, imgtype):
		return {
			PDFImageType.FlateDecode:		"pnm",
			PDFImageType.RunLengthDecode:	"pnm",
			PDFImageType.DCTDecode:			"jpg",
		}[imgtype]

	@staticmethod
	def _rle_decode(rle_data):
		result = bytearray()
		index = 0
		while index < len(rle_data):
			length = rle_data[index]
			index += 1
			if 0 <= length <= 127:
				bytecnt = 1 + length
				result += rle_data[index : index + bytecnt]
				index += bytecnt
			elif length == 128:
				# EOD
				break
			else:
				bytecnt = 257 - length
				value = rle_data[index]
				result += bytecnt * bytes([ value ])
				index += 1
		return result

	def get_pixeldata(self):
		if self.imgtype == PDFImageType.FlateDecode:
			return zlib.decompress(self._imgdata)
		elif self.imgtype == PDFImageType.RunLengthDecode:
			return self._rle_decode(self._imgdata)
		else:
			raise Exception(NotImplemented)

	def pixel_hash(self):
		return hashlib.md5(self.get_pixeldata()).hexdigest()

	def get_pnm(self):
		pixeldata = self.get_pixeldata()
		if (self.colorspace == PDFImageColorSpace.DeviceRGB) and (self.bits_per_component == 8):
			image = PnmPicture(width = self.width, height = self.height, data = pixeldata, img_format = PnmPictureFormat.Pixmap)
		elif (self.colorspace == PDFImageColorSpace.DeviceGray) and (self.bits_per_component == 8):
			image = PnmPicture(width = self.width, height = self.height, data = pixeldata, img_format = PnmPictureFormat.Graymap)
		elif (self.colorspace == PDFImageColorSpace.DeviceGray) and (self.bits_per_component == 1):
			image = PnmPicture(width = self.width, height = self.height, data = pixeldata, img_format = PnmPictureFormat.Bitmap)
		else:
			raise Exception("Creating PNM from this ColorSpace/BitsPerComponent combination is unsupported (%s/%d)." % (self.colorspace, self.bits_per_component))
		return image

	@staticmethod
	def _get_image_width_height(filename):
		output = subprocess.check_output([ "file", filename ])
		output = output.decode("utf-8")
		regex = re.compile("[,=] (?P<width>\d+)(x| x )(?P<height>\d+),")
		result = regex.search(output)
		if result is None:
			raise Exception("Cannot determine size from image.")
		result = result.groupdict()
		return (int(result["width"]), int(result["height"]))

	def writefile(self, filename):
		if self.imgtype in [ PDFImageType.FlateDecode, PDFImageType.RunLengthDecode ]:
			pnm_image = self.get_pnm()
			pnm_image.write_file(filename)
		else:
			with open(filename, "wb") as f:
				f.write(self._imgdata)

	def __len__(self):
		return len(self._imgdata)

	def _raw_str(self):
		return "%sImg<%d x %d, %s-%d>" % (self.imgtype.name, self.width, self.height, self.colorspace.name, self.bits_per_component)

	def __str__(self):
		if self.alpha is None:
			return self._raw_str()
		else:
			return "%s with alpha %s" % (self._raw_str(), self.alpha._raw_str())

