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
from llpdf.types.PDFObject import PDFObject
from llpdf.types.TransformationMatrix import TransformationMatrix

class GraphicsInterpreter(object):
	_log = logging.getLogger("llpdf.interpreter.GraphicsInterpreter")
	_DirectDrawCallbackResult = collections.namedtuple("DirectDrawCallbackResult", [ "drawtype", "image_obj", "native_extents" ])
	_PatternDrawCallbackResult = collections.namedtuple("DirectDrawCallbackResult", [ "drawtype", "pattern_obj", "image_obj", "native_extents" ])

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
		pattern_bbox = pattern.content[PDFName("/BBox")]
		pattern_matrix = TransformationMatrix(*pattern.content[PDFName("/Matrix")])

		pattern_resource_xrefs = list(pattern.content[PDFName("/Resources")][PDFName("/XObject")].values())
		if len(pattern_resource_xrefs) != 1:
			return

		image_resource = self._pdf_lookup.lookup(pattern_resource_xrefs[0])
		native_extents = pattern_matrix.extents(pattern_bbox)

		self._log.debug("Pattern draw object of %s found with CTM %s and pattern matrix %s; %s", image_resource, self._gs["CTM"], pattern_matrix, native_extents.format())
		self._draw_callback(self._PatternDrawCallbackResult(drawtype = "pattern", pattern_obj = pattern, image_obj = image_resource, native_extents = native_extents))

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
				if isinstance(self._page_resources, PDFObject):
					resources = self._page_resources.content
				else:
					resources = self._page_resources
				xobjects = resources[PDFName("/XObject")]
				image_xref = xobjects[image_handle]
				image_obj = self._pdf_lookup.lookup(image_xref)

				native_extents = self._gs["CTM"].extents([ 0, 0, 1, 1 ])
				self._log.debug("Draw object of %s found with CTM %s; %s", image_obj, self._gs["CTM"], native_extents.format())

				self._draw_callback(self._DirectDrawCallbackResult(drawtype = "direct", image_obj = image_obj, native_extents = native_extents))
#		else:
#			print("Ignoring unknown command: %s" % (cmd))

	def run(self, code):
		for command in code:
			self._run_command(command)
