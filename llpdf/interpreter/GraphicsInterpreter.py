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

import logging
import collections
from llpdf.types.PDFName import PDFName
from llpdf.types.PDFXRef import PDFXRef

#> x := Matrix([[a,b,0],[c,d,0],[e,f,1]]);
#                                                                                   [a    b    0]
#                                                                                   [           ]
#                                                                              x := [c    d    0]
#                                                                                   [           ]
#                                                                                   [e    f    1]
#
#> y := Matrix([[a_,b_,0],[c_,d_,0],[e_,f_,1]]);
#                                                                                  [a_    b_    0]
#                                                                                  [             ]
#                                                                             y := [c_    d_    0]
#                                                                                  [             ]
#                                                                                  [e_    f_    1]
#
#> evalm(x&*y);
#                                                                 [  a a_ + b c_         a b_ + b d_       0]
#                                                                 [                                         ]
#                                                                 [  c a_ + d c_         c b_ + d d_       0]
#                                                                 [                                         ]
#                                                                 [e a_ + f c_ + e_    e b_ + f d_ + f_    1]

ImageExtents = collections.namedtuple("ImageExtents", [ "x", "y", "width", "height" ])

class TransformationMatrix(object):
	def __init__(self, a, b, c, d, e, f):
		self._a = a
		self._b = b
		self._c = c
		self._d = d
		self._e = e
		self._f = f

	@property
	def a(self):
		return self._a

	@property
	def b(self):
		return self._b

	@property
	def c(self):
		return self._c

	@property
	def d(self):
		return self._d

	@property
	def e(self):
		return self._e

	@property
	def f(self):
		return self._f

	def apply(self, x, y):
		return (
			self.a * x + self.c * y + self.e,
			self.b * x + self.d * y + self.f,
		)

	def extents(self, width = 1, height = 1, scale = 1):
		(x0, y0) = self.apply(0, 0)
		(x1, y1) = self.apply(width, height)
		(w, h) = (x1 - x0, y1 - y0)
		return ImageExtents(x = scale * x0, y = scale * y0, width = scale * w, height = scale * h)

	def __imul__(self, other):
		return TransformationMatrix(
			self.a * other.a + self.b * other.c,
			self.a * other.b + self.b * other.d,
			self.c * other.a + self.d * other.c,
			self.c * other.b + self.d * other.d,
			self.e * other.a + self.f * other.c + other.e,
			self.e * other.b + self.f * other.d + other.f,
		)

	@classmethod
	def identity(cls):
		return cls(1, 0, 0, 1, 0, 0)

	def __repr__(self):
		return str(self)

	def __str__(self):
		return "Matrix<%f %f %f %f %f %f>" % (self.a, self.b, self.c, self.d, self.e, self.f)

class GraphicsInterpreter(object):
	_log = logging.getLogger("llpdf.interpreter.GraphicsInterpreter")
	_DirectDrawCallbackResult = collections.namedtuple("DirectDrawCallbackResult", [ "drawtype", "image_obj", "extents" ])
	_PatternDrawCallbackResult = collections.namedtuple("DirectDrawCallbackResult", [ "drawtype", "pattern_obj", "image_obj", "extents" ])

	def __init__(self, pdf_lookup = None, page_obj = None):
		self._pdf_lookup = pdf_lookup
		self._page_obj = page_obj
		self._gs = {		# Graphic state
			"CTM":		TransformationMatrix.identity(),
			"color_ns":	None,
		}
		self._gss = [ ]		# Graphic state stack
		self._path = [ ]
		self._draw_callback = None

		if (pdf_lookup is not None) and (page_obj is not None):
			resources = self._page_obj.content[PDFName("/Resources")]
			if isinstance(resources, PDFXRef):
				resources = self._pdf_lookup.lookup(resources)
			self._page_resources = resources

	def set_draw_callback(self, callback):
		self._draw_callback = callback

	def _callback_fill_rect(self):
		if self._draw_callback is None:
			return

		patterns = self._page_resources.content.get(PDFName("/Pattern"))
		if patterns is None:
			return

		pattern_xref = patterns.get(self._gs["color_ns"])
		if pattern_xref is None:
			return

		pattern = self._pdf_lookup.lookup(pattern_xref)
		pattern_matrix = TransformationMatrix(*pattern.content[PDFName("/Matrix")])

		pattern_resource_xrefs = list(pattern.content[PDFName("/Resources")][PDFName("/XObject")].values())
		if len(pattern_resource_xrefs) != 1:
			return

		image_resource = self._pdf_lookup.lookup(pattern_resource_xrefs[0])
		width_px = image_resource.content[PDFName("/Width")]
		height_px = image_resource.content[PDFName("/Height")]

		extents = pattern_matrix.extents(width = width_px, height = height_px, scale = (1 / 72) * 25.4)

		self._log.debug("Pattern draw object of %s found with CTM %s and pattern matrix %s; extent at %s", image_resource, self._gs["CTM"], pattern_matrix, extents)
		self._draw_callback(self._PatternDrawCallbackResult(drawtype = "pattern", pattern_obj = pattern, image_obj = image_resource, extents = extents))

	def _run_command(self, cmd):
		cmdcode = cmd.command
		if cmdcode == "q":
			# Save graphic state
			self._gss.append(dict(self._gs))
		elif cmdcode == "Q":
			# Restore graphic state
			self._gs = self._gss.pop()
		elif cmdcode == "cm":
			# Apply to current transformation matrix (CTM)
			self._gs["CTM"] *= TransformationMatrix(*cmd.args)
		elif cmdcode in [ "re" ]:
			# Append a rectangle to the current path
			self._path.append(cmd)
		elif cmdcode in [ "W" ]:
			# Use current path as clipping
#			print("Cliping", self._path)
			pass
		elif cmdcode in [ "S", "s", "f", "F", "f*", "B", "B*", "b", "b*", "n" ]:
			# Any of these commands will finish a path
			if (cmdcode == "f") and (len(self._path) == 1) and (self._path[0].command == "re"):
				self._callback_fill_rect()
			self._path = [ ]
		elif cmdcode == "scn":
			# Set color for non-stroking
			self._gs["color_ns"] = cmd.args[0]
		elif cmdcode == "gs":
#			print("Load graphic state")
			pass
		elif cmdcode == "Do":
			# Draw object
			if self._draw_callback is not None:
				image_handle = cmd.args[0]
				xobjects = self._page_resources.content[PDFName("/XObject")]
				image_xref = xobjects[image_handle]
				image_obj = self._pdf_lookup.lookup(image_xref)

				# TODO FIXME: I'm VERY sure the constant factor of 1.25 here is
				# a bug. It's what is required to make PDFs that are generated
				# by Inkscape work properly, but that value cannot just come
				# out of nowhere. Threfore this most certainly will break other
				# implementations. Please send a PR if you know what's going
				# on.
				extents = self._gs["CTM"].extents(scale = 1.25)
				self._log.debug("Draw object of %s found with CTM %s; extent at %s", image_obj, self._gs["CTM"], extents)

				self._draw_callback(self._DirectDrawCallbackResult(drawtype = "direct", image_obj = image_obj, extents = extents))
#		else:
#			print("Ignoring unknown command: %s" % (cmd))

	def run(self, code):
		for command in code:
			self._run_command(command)
