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
from llpdf.types.PDFObject import PDFObject
from llpdf.types.PDFName import PDFName
from llpdf.interpreter.GraphicsInterpreter import GraphicsInterpreter

class DownscaleImageOptimization(PDFFilter):
	def _draw_callback(self, draw_cmd):
		self._log.debug("Interpreter found image: %s", draw_cmd)
		image_xref = draw_cmd.image_obj.xref
		(w, h) = (abs(draw_cmd.extents.width), abs(draw_cmd.extents.height))
		if image_xref in self._max_image_extents:
			(current_w, current_h) = self._max_image_extents[image_xref]
			w = max(w, current_w)
			h = max(h, current_h)
		self._max_image_extents[image_xref] = (w, h)
		self._draw_cmds[image_xref].append(draw_cmd)

	def _save_image(self, subdir, img_object):
		if self._args.saveimgdir is not None:
			img = img_object.get_image()
			print(img_object.content)
			filename = "%s/%s_%04d.%s" % (self._args.saveimgdir, subdir, img_object.objid, img.extension)
			img.writefile(filename)

	def _rescale(self, image_obj, scale_factor):
		img = image_obj.get_image()

		if (img.imgtype == PDFImageType.FlateDecode) and (self._args.jpg_images):
			target_type = PDFImageType.DCTDecode
		else:
			target_type = img.imgtype
		self._log.debug("Resampling %s to %s with scale factor %.3f", img, target_type.name, scale_factor)
		img = img.reformat(target_type, scale_factor = scale_factor)

		new_obj = PDFObject.create_image(image_obj.objid, image_obj.gennum, img)
		self._optimized(len(image_obj), len(new_obj))
		self._save_image("resampled", new_obj)
		image_obj.replace_by(new_obj)

	def run(self):
		self._max_image_extents = { }
		self._draw_cmds = collections.defaultdict(list)

		# Run through pages first to determine image extents
		for (page_obj, page_content) in self._pdf.parsed_pages:
			interpreter = GraphicsInterpreter(pdf_lookup = self._pdf, page_obj = page_obj)
			interpreter.set_draw_callback(self._draw_callback)
			interpreter.run(page_content)

		for (img_xref, (maxw_mm, maxh_mm)) in self._max_image_extents.items():
			self._log.debug("Estimated image %s to have maximum dimensions of %.1f x %.1f mm", img_xref, maxw_mm, maxh_mm)
			image = self._pdf.get_image(img_xref)
			self._save_image("original", image)

		if False:
			maxw_inches = maxw_mm / 25.4
			maxh_inches = maxh_mm / 25.4
			current_dpi_w = pixel_w / maxw_inches
			current_dpi_h = pixel_h / maxh_inches
			current_dpi = min(current_dpi_w, current_dpi_h)
			if self._args.verbose:
				self._log.debug("Current resolution of %s: %.0f dpi", image, current_dpi)

			scale_factor = min(self._args.target_dpi / current_dpi, 1)
			self._rescale(image, scale_factor)

			draw_commands = self._draw_cmds[img_xref]
			pattern_draw_commands = [ draw_command for draw_command in draw_commands if draw_command.drawtype == "pattern" ]
			if len(pattern_draw_commands) != 0:
				print(pattern_draw_commands)

