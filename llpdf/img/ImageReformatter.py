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

import subprocess
import logging
from tempfile import NamedTemporaryFile
from llpdf.img.PDFImage import PDFImage, PDFImageColorSpace
from llpdf.img.PnmPicture import PnmPicture, PnmPictureFormat
from llpdf.EncodeDecode import EncodedObject, Filter

class ImageReformatter(object):
	_log = logging.getLogger("llpdf.img.ImageReformatter")

	def __init__(self, lossless, scale_factor = 1, jpeg_quality = 85, force_one_bit_alpha = False):
		assert(isinstance(lossless, bool))
		self._lossless = lossless
		self._scale_factor = scale_factor
		self._jpeg_quality = jpeg_quality
		self._force_one_bit_alpha = force_one_bit_alpha

	@classmethod
	def _get_image_geometry(cls, image_filename):
		identify_cmd = [ "identify", "-format", "%w %h %[colorspace] %[depth]\n", image_filename ]
		cls._log.debug("Running command: %s", " ".join(identify_cmd))
		output = subprocess.check_output(identify_cmd)
		output = output.decode("ascii")
		(width, height, colorspace, depth) = output.rstrip("\r\n").split()
		(width, height, depth) = (int(width), int(height), int(depth))
		return (width, height, colorspace, depth)

	@classmethod
	def _encode_image(cls, image_filename, lossless):
		if lossless:
			img = PnmPicture.read_file(image_filename)
			if img.img_format == PnmPictureFormat.Bitmap:
				# PDFs use exactly inverted syntax for 1-bit images
				img.invert()
			imgdata = EncodedObject.create(img.data)
			(colorspace, bits_per_component) = {
				PnmPictureFormat.Bitmap:		(PDFImageColorSpace.DeviceGray, 1),
				PnmPictureFormat.Graymap:		(PDFImageColorSpace.DeviceGray, 8),
				PnmPictureFormat.Pixmap:		(PDFImageColorSpace.DeviceRGB, 8),
			}[img.img_format]
			width = img.width
			height = img.height
		else:
			with open(image_filename, "rb") as f:
				imgdata = EncodedObject(encoded_data = f.read(), filtering = Filter.DCTDecode)
			(width, height, colorspace, bits_per_component) = cls._get_image_geometry(image_filename)
			colorspace = {
					"Gray":	PDFImageColorSpace.DeviceGray,
					"sRGB":	PDFImageColorSpace.DeviceRGB,
			}[colorspace]
		return PDFImage(width = width, height = height, colorspace = colorspace, bits_per_component = bits_per_component, imgdata = imgdata, inverted = False)


	def _reformat_channel(self, image, lossless, grayscale = False):
		target_extension = ".pnm" if lossless else ".jpg"
		with NamedTemporaryFile(prefix = "src_img_", suffix = "." + image.extension) as src_img_file, NamedTemporaryFile(prefix = "result_img_", suffix = target_extension) as dst_img_file:
			image.writefile(src_img_file.name)

			conversion_cmd = [ "convert" ]
			if self._scale_factor != 1:
				conversion_cmd += [ "-scale", "%f%%" % (self._scale_factor * 100) ]

			if not lossless:
				conversion_cmd += [ "-quality", str(self._jpeg_quality) ]

			if grayscale:
				conversion_cmd += [ "-colorspace", "Gray" ]
				if self._force_one_bit_alpha:
					conversion_cmd += [ "-depth", "1" ]
				else:
					conversion_cmd += [ "-depth", "8" ]

			if image.inverted:
				conversion_cmd += [ "-negate" ]
			conversion_cmd += [ "+repage" ]
			conversion_cmd += [ "-strip" ]
			conversion_cmd += [ src_img_file.name, dst_img_file.name ]

			self._log.debug("Running command: %s", " ".join(conversion_cmd))
			subprocess.check_call(conversion_cmd)

			return self._encode_image(dst_img_file.name, lossless)

	def reformat(self, image):
		if (image.imgdata.lossless == self._lossless) and (self._scale_factor == 1):
			return image

		# Rescale raw image first
		lossless = image.imgdata.lossless and (not self._lossless)
		reformatted_image = self._reformat_channel(image, lossless)

		# Then rescale alpha channel as well
		if image.alpha:
			reformatted_alpha = self._reformat_channel(image.alpha, lossless = True, grayscale = True)
			reformatted_image.set_alpha(reformatted_alpha)

		return reformatted_image

	def flatten(self, image, background_color):
		if image.alpha is None:
			return image

		with NamedTemporaryFile(prefix = "src_img_", suffix = "." + image.extension) as src_img_file,\
				NamedTemporaryFile(prefix = "src_alpha_", suffix = "." + image.extension) as src_alpha_file,\
				NamedTemporaryFile(prefix = "result_img_", suffix = ".pnm") as dst_img_file:
			image.writefile(src_img_file.name)
			image.alpha.writefile(src_alpha_file.name)
			conversion_cmd = [ "convert" ]
			conversion_cmd += [ src_img_file.name ]
			conversion_cmd += [ "(" ]
			conversion_cmd += [ src_alpha_file.name ]
			conversion_cmd += [ "-colorspace", "gray", "-alpha", "off" ]
			if image.alpha.inverted:
				conversion_cmd += [ "-negate" ]
			conversion_cmd += [ ")" ]

			conversion_cmd += [ "-compose", "copy-opacity" ]
			conversion_cmd += [ "-composite" ]
			conversion_cmd += [ "-background", background_color, "-compose" ,"over", "-flatten" ]
			conversion_cmd += [ dst_img_file.name ]
			subprocess.check_call(conversion_cmd)

			flattened_image = self._encode_image(dst_img_file.name, lossless = True)
		return flattened_image
