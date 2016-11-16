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
from llpdf.img.PDFImage import PDFImageType
from llpdf.img.ImageReformatter import ImageReformatter
from llpdf.types.PDFObject import PDFObject
from llpdf.types.PDFName import PDFName
from llpdf.types.TransformationMatrix import TransformationMatrix
from llpdf.interpreter.GraphicsInterpreter import GraphicsInterpreter

class DownscaleImageOptimization(PDFFilter):
	def _draw_callback(self, draw_cmd):
		self._log.debug("Interpreter found %s image at %.1f, %.1f mm with extents %.1f x %.1f mm", draw_cmd.drawtype, draw_cmd.extents.x, draw_cmd.extents.y, draw_cmd.extents.width, draw_cmd.extents.height)
		image_xref = draw_cmd.image_obj.xref
		(w, h) = (abs(draw_cmd.extents.width), abs(draw_cmd.extents.height))
		if image_xref in self._max_image_extents:
			(current_w, current_h) = self._max_image_extents[image_xref]
			w = max(w, current_w)
			h = max(h, current_h)
		self._max_image_extents[image_xref] = (w, h)
		self._draw_cmds[image_xref].append(draw_cmd)

	def _save_image(self, image, image_xref, text):
		if self._args.saveimgdir is not None:
			self._log.debug("Saving %s", str(image))
			filename = "%s/%s_%04d.%s" % (self._args.saveimgdir, text, image_xref.objid, image.extension)
			image.writefile(filename)
			if image.alpha is not None:
				filename = "%s/%s_%04d_alpha.%s" % (self._args.saveimgdir, text, image_xref.objid, image.extension)
				image.alpha.writefile(filename)

	def _rescale_image(self, image, scale_factor):
		if (image.imgtype == PDFImageType.FlateDecode) and (self._args.jpg_images):
			target_type = PDFImageType.DCTDecode
		else:
			target_type = image.imgtype
		self._log.debug("Resampling %s (%d bytes) to %s with scale factor %.3f", image, image.total_size, target_type.name, scale_factor)
		reformatter = ImageReformatter(target_format = target_type, scale_factor = scale_factor, force_one_bit_alpha = self._args.one_bit_alpha)
		resampled_image = reformatter.reformat(image)
		return resampled_image

	@staticmethod
	def _calculate_dpi(image, maxw_mm, maxh_mm):
		maxw_inches = maxw_mm / 25.4
		maxh_inches = maxh_mm / 25.4
		current_dpi_w = image.width / maxw_inches
		current_dpi_h = image.height / maxh_inches
		current_dpi = min(current_dpi_w, current_dpi_h)
		return current_dpi

	def _replace_image(self, img_xref, resampled_image):
		image_meta = self._pdf.lookup(img_xref).content
		alpha_xref = image_meta.get(PDFName("/SMask"))

		new_image_obj = PDFObject.create_image(img_xref.objid, img_xref.gennum, resampled_image, alpha_xref = alpha_xref)
		self._pdf.replace_object(new_image_obj)
		if resampled_image.alpha:
			new_alpha_obj = PDFObject.create_image(alpha_xref.objid, alpha_xref.gennum, resampled_image.alpha)
			self._pdf.replace_object(new_alpha_obj)

	def run(self):
		self._max_image_extents = { }
		self._draw_cmds = collections.defaultdict(list)

		# Run through pages first to determine image extents
		for (page_obj, page_content) in self._pdf.parsed_pages:
			interpreter = GraphicsInterpreter(pdf_lookup = self._pdf, page_obj = page_obj)
			interpreter.set_draw_callback(self._draw_callback)
			interpreter.run(page_content)

		for (img_xref, (maxw_mm, maxh_mm)) in self._max_image_extents.items():
			image = self._pdf.get_image(img_xref)
			self._save_image(image, img_xref, "original")

			current_dpi = self._calculate_dpi(image, maxw_mm, maxh_mm)
			scale_factor = min(self._args.target_dpi / current_dpi, 1)
			self._log.debug("Estimated image %s to have maximum dimensions of %.1f x %.1f mm (%d dpi), scale = %.3f", img_xref, maxw_mm, maxh_mm, current_dpi, scale_factor)

			resampled_image = self._rescale_image(image, scale_factor)
			self._save_image(resampled_image, img_xref, "resampled")
			self._log.debug("Resulting image after resampling: %s (%d bytes, i.e., %+d bytes)", resampled_image, resampled_image.total_size, resampled_image.total_size - image.total_size)

			self._optimized(image.total_size, resampled_image.total_size)
			self._replace_image(img_xref, resampled_image)

#			draw_commands = self._draw_cmds[img_xref]
#			pattern_draw_commands = [ draw_command for draw_command in draw_commands if draw_command.drawtype == "pattern" ]
#			if len(pattern_draw_commands) != 0:
#				pattern_objs = set(draw_command.pattern_obj for draw_command in pattern_draw_commands)
#				for pattern_obj in pattern_objs:
#					pattern_matrix = TransformationMatrix(*pattern_obj.content[PDFName("/Matrix")])

#					scale_matrix = TransformationMatrix.scale(1.0)
#					scale_matrix *= pattern_matrix

#					pattern_obj.content[PDFName("/Matrix")] = pattern_matrix.aslist
#					pattern_obj.content[PDFName("/Matrix")][3] *= 0.5
#					print(pattern_obj, pattern_matrix, scale_matrix)
#					print(pattern_matrix)

