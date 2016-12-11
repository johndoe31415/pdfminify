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

import collections
from .PDFFilter import PDFFilter
from llpdf.Exceptions import UnsupportedImageException
from llpdf.img.ImageReformatter import ImageReformatter
from llpdf.types.PDFObject import PDFObject
from llpdf.types.PDFName import PDFName
from llpdf.interpreter.GraphicsInterpreter import GraphicsInterpreter

class DownscaleImageOptimization(PDFFilter):
	def _draw_callback(self, draw_cmd):
		if draw_cmd.image_obj.content.get(PDFName("/Subtype")) != PDFName("/Image"):
			# This might be a /Form that is plotted with the Do command or
			# similar. Ignore it.
			return

		image_xref = draw_cmd.image_obj.xref
		self._log.debug("Interpreter found %s image %s at %s", draw_cmd.drawtype, image_xref, draw_cmd.native_extents.format())
		self._draw_cmds[image_xref].append(draw_cmd)

	def _save_image(self, image, image_xref, text):
		if self._args.saveimgdir is not None:
			self._log.debug("Saving %s", str(image))
			filename = "%s/%s_%04d.%s" % (self._args.saveimgdir, text, image_xref.objid, image.raw_extension if self._args.raw_output else image.extension)
			image.writefile(filename, write_raw_data = self._args.raw_output)
			if image.alpha is not None:
				filename = "%s/%s_%04d_alpha.%s" % (self._args.saveimgdir, text, image_xref.objid, image.alpha.raw_extension if self._args.raw_output else image.alpha.extension)
				image.alpha.writefile(filename, write_raw_data = self._args.raw_output)

	def _rescale_image(self, image, scale_factor):
		lossless = not self._args.jpeg_images
		self._log.debug("Resampling %s (%d bytes) to lossless = %s with scale factor %.3f", image, image.total_size, lossless, scale_factor)
		reformatter = ImageReformatter(lossless = lossless, scale_factor = scale_factor, jpeg_quality = self._args.jpeg_quality, force_one_bit_alpha = self._args.one_bit_alpha)
		resampled_image = reformatter.reformat(image)
		return resampled_image

	def _replace_image(self, img_xref, resampled_image):
		image_meta = self._pdf.lookup(img_xref).content
		alpha_xref = image_meta.get(PDFName("/SMask"))

		new_image_obj = PDFObject.create_image(img_xref.objid, img_xref.gennum, resampled_image, alpha_xref = alpha_xref)
		self._pdf.replace_object(new_image_obj)
		if resampled_image.alpha:
			new_alpha_obj = PDFObject.create_image(alpha_xref.objid, alpha_xref.gennum, resampled_image.alpha)
			self._pdf.replace_object(new_alpha_obj)

	def run(self):
		self._draw_cmds = collections.defaultdict(list)

		# Run through pages first to determine image extents
		for (page_obj, page_content) in self._pdf.parsed_pages:
			interpreter = GraphicsInterpreter(pdf_lookup = self._pdf, page_obj = page_obj)
			interpreter.set_draw_callback(self._draw_callback)
			interpreter.run(page_content)

		for (img_xref, img_draw_cmds) in self._draw_cmds.items():
			try:
				image = self._pdf.get_image(img_xref)
			except UnsupportedImageException as e:
				self._log.warning("Ignoring unsupported image %s: %s", img_xref, e)
				continue
			self._save_image(image, img_xref, "original")

			if self._args.no_downscaling:
				# We arrive here if we're just trying to save exported images.
				# Maybe exporing of images should be a own filter?
				continue

			current_dpi = min(draw_cmd.native_extents.dpi(image.width, image.height) for draw_cmd in img_draw_cmds)
			scale_factor = min(self._args.target_dpi / current_dpi, 1)
			self._log.debug("Estimated image %s to have minimum resulution of %d dpi: scale factor = %.3f", img_xref, current_dpi, scale_factor)

			resampled_image = self._rescale_image(image, scale_factor)
			self._save_image(resampled_image, img_xref, "resampled")
			self._log.debug("Resulting image after resampling: %s (%d bytes, i.e., %+d bytes)", resampled_image, resampled_image.total_size, resampled_image.total_size - image.total_size)

			self._optimized(image.total_size, resampled_image.total_size)
			self._replace_image(img_xref, resampled_image)
