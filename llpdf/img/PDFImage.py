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
from .PnmPicture import PnmPicture
from llpdf.types.PDFName import PDFName

class PDFImageType(enum.IntEnum):
	FlateDecode = 1
	DCTDecode = 2

class PDFImage(object):
	def __init__(self, width, height, imgdata, imgtype):
		self._width = width
		self._height = height
		self._imgdata = imgdata
		self._imgtype = imgtype
		assert(isinstance(self._imgtype, PDFImageType))

	@classmethod
	def create_from_object(cls, xobj):
		width = xobj.content[PDFName("/Width")]
		height = xobj.content[PDFName("/Height")]
		imgtype = {
			PDFName("/FlateDecode"):	PDFImageType.FlateDecode,
			PDFName("/DCTDecode"):		PDFImageType.DCTDecode,
		}.get(xobj.content[PDFName("/Filter")])
		if imgtype is None:
			raise Exception("Cannot create image from unknown type '%s'." % (xobj.content[PDFName("/Filter")]))
		return cls(width = width, height = height, imgdata = xobj.stream, imgtype = imgtype)

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
	def extension(self):
		return {
			PDFImageType.FlateDecode:	"pnm",
			PDFImageType.DCTDecode:		"jpg",
		}[self.imgtype]

	def get_pixeldata(self):
		if self.imgtype == PDFImageType.FlateDecode:
			return zlib.decompress(self._imgdata)
		else:
			raise Exception(NotImplemented)

	def pixel_hash(self):
		return hashlib.md5(self.get_pixeldata()).hexdigest()

	def get_pnm(self):
		img = PnmPicture.fromdata(self.width, self.height, self.get_pixeldata())
		return img

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

	def reformat(self, new_img_type, scale_factor = 1, quality = None):
		if (self.imgtype == new_img_type) and (scale_factor == 1):
			return self
		pnm_image = self.get_pnm()

		out_extension = {
			PDFImageType.FlateDecode:	".pnm",
			PDFImageType.DCTDecode:		".jpg",
		}[new_img_type]
		with NamedTemporaryFile(suffix = ".pnm") as orig_file, NamedTemporaryFile(suffix = out_extension) as resampled_file:
			pnm_image.writefile(orig_file.name)

			cmd = [ "convert" ]
			if scale_factor != 1:
				cmd += [ "-scale", "%f%%" % (scale_factor * 100) ]
			if new_img_type == PDFImageType.DCTDecode:
				cmd += [ "-quality", str(quality) if (quality is not None) else "85" ]
			cmd += [ "+repage", orig_file.name, resampled_file.name ]
			subprocess.check_call(cmd)
			if new_img_type == PDFImageType.FlateDecode:
				img = PnmPicture().readfile(resampled_file.name)
				imgdata = zlib.compress(img.data)
			else:
				with open(resampled_file.name, "rb") as f:
					imgdata = f.read()
			(new_width, new_height) = self._get_image_width_height(resampled_file.name)
			image = PDFImage(new_width, new_height, imgdata, new_img_type)
			return image

	def writefile(self, filename):
		if self.imgtype == PDFImageType.FlateDecode:
			pnm_image = self.get_pnm()
			pnm_image.writefile(filename)
		else:
			with open(filename, "wb") as f:
				f.write(self._imgdata)

	def __len__(self):
		return len(self._imgdata)

	def __str__(self):
		return "%sImg<%d x %d>" % (self.imgtype.name, self.width, self.height)

