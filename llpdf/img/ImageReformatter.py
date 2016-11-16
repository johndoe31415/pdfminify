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
import subprocess
import zlib
from tempfile import NamedTemporaryFile
from llpdf.img.PDFImage import PDFImage, PDFImageType, PDFImageColorSpace
from llpdf.img.PnmPicture import PnmPicture, PnmPictureFormat

class ImageReformatter(object):
	def __init__(self, target_format, scale_factor = 1, jpg_quality = 85):
		self._target_format = target_format
		self._scale_factor = scale_factor
		self._jpg_quality = jpg_quality

	@classmethod
	def _get_image_geometry(cls, image_filename):
		identify_cmd = [ "identify", "-format", "%w %h\n", image_filename ]
		output = subprocess.check_output(identify_cmd)
		output = output.decode("ascii").rstrip("\r\n")
		(width, height) = [ int(x) for x in output.split() ]
		return (width, height)

	@classmethod
	def _encode_image(cls, image_filename, image_format):
		if image_format == PDFImageType.FlateDecode:
			img = PnmPicture.read_file(image_filename)
			imgdata = zlib.compress(img.data)
			(colorspace, bits_per_component) = {
				PnmPictureFormat.Bitmap:		(PDFImageColorSpace.DeviceGray, 1),
				PnmPictureFormat.Graymap:		(PDFImageColorSpace.DeviceGray, 8),
				PnmPictureFormat.Pixmap:		(PDFImageColorSpace.DeviceRGB, 8),
			}[img.img_format]
			width = img.width
			height = img.height
		elif image_format == PDFImageType.RunLengthDecode:
			raise Exception("Encoding in RLE not supported.")
		else:
			with open(image_filename, "rb") as f:
				imgdata = f.read()
			(width, height) = cls._get_image_geometry(image_filename)
			colorspace = PDFImageColorSpace.DeviceRGB
			bits_per_component = 8

		return PDFImage(width = width, height = height, colorspace = colorspace, bits_per_component = bits_per_component, imgdata = imgdata, imgtype = image_format)


	def _reformat_channel(self, image, target_format, grayscale = False):
		target_extension = PDFImage.extension_for_imgtype(target_format)
		with NamedTemporaryFile(prefix = "src_img_", suffix = "." + image.extension) as src_img_file, NamedTemporaryFile(prefix = "result_img_", suffix = "." + target_extension) as dst_img_file:
			image.writefile(src_img_file.name)

			conversion_cmd = [ "convert" ]
			if self._scale_factor != 1:
				conversion_cmd += [ "-scale", "%f%%" % (self._scale_factor * 100) ]

			if target_format == PDFImageType.DCTDecode:
				conversion_cmd += [ "-quality", str(self._jpg_quality) ]

			conversion_cmd += [ "+repage" ]
			if grayscale:
				conversion_cmd += [ "-colorspace", "Gray", "-depth", "1" ]
			conversion_cmd += [ src_img_file.name, dst_img_file.name ]
#			print(" ".join(conversion_cmd))
			subprocess.check_call(conversion_cmd)

			return self._encode_image(dst_img_file.name, target_format)

	def reformat(self, image):
		if (image.imgtype == self._target_format) and (self._scale_factor == 1):
			return image

		# Rescale raw image first
		target_format = image.imgtype
		if (target_format != PDFImageType.DCTDecode) and (self._target_format == PDFImageType.DCTDecode):
			target_format = self._target_format
		reformatted_image = self._reformat_channel(image, target_format)

		# Then rescale alpha channel as well
		if image.alpha:
			reformatted_alpha = self._reformat_channel(image.alpha, PDFImageType.FlateDecode, grayscale = True)
			reformatted_image.set_alpha(reformatted_alpha)

		return reformatted_image

