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
from llpdf.font.T1Command import T1Command, T1CommandCode
from llpdf.font.PostScriptEnums import PostScriptStandardCharacterName

class _T1ExecutionFinishedException(Exception):
	pass

class T1Interpreter(object):
	_log = logging.getLogger("llpdf.font.T1Interpreter")

	def __init__(self, canvas = None, parent_font = None):
		self._canvas = canvas
		self._parent_font = parent_font
		self._width = [ ]
		self._left_sidebearing = [ 0, 0 ]
		self._pos = None
		self._path = [ ]

	def _run_command(self, cmd):
		if cmd.cmdcode == T1CommandCode.hsbw:
			# Horizontal sidebearing and width
			self._left_sidebearing = [ cmd[0], 0 ]
			self._width = [ cmd[1], 0 ]
			if self._pos is None:
				self._pos = [ cmd[0], 0 ]
		elif cmd.cmdcode == T1CommandCode.sbw:
			# Sidebearing and width
			self._left_sidebearing = [ cmd[0], cmd[1] ]
			self._width = [ cmd[2], cmd[3] ]
			if self._pos is None:
				self._pos = [ cmd[0], cmd[1] ]
		elif cmd.cmdcode in [ T1CommandCode.rmoveto, T1CommandCode.rlineto ]:
			newpos = [ self._pos[0] + cmd[0], self._pos[1] + cmd[1] ]
			if cmd.cmdcode == T1CommandCode.rlineto:
				if self._canvas is not None:
					self._canvas.line(self._pos, newpos)
			self._pos = newpos
			self._path.append(self._pos)
		elif cmd.cmdcode == T1CommandCode.rrcurveto:
			pt1 = [ self._pos[0] + cmd[0], self._pos[1] + cmd[1] ]
			pt2 = [ pt1[0] + cmd[2], pt1[1] + cmd[3] ]
			pt3 = [ pt2[0] + cmd[4], pt2[1] + cmd[5] ]
			if self._canvas is not None:
				self._canvas.bezier(self._pos, pt1, pt2, pt3)
			self._pos = pt3
			self._path.append(self._pos)
		elif cmd.cmdcode == T1CommandCode.hmoveto:
			self._run_command(T1Command(T1CommandCode.rmoveto, cmd[0], 0))
		elif cmd.cmdcode == T1CommandCode.vmoveto:
			self._run_command(T1Command(T1CommandCode.rmoveto, 0, cmd[0]))
		elif cmd.cmdcode == T1CommandCode.hlineto:
			self._run_command(T1Command(T1CommandCode.rlineto, cmd[0], 0))
		elif cmd.cmdcode == T1CommandCode.vlineto:
			self._run_command(T1Command(T1CommandCode.rlineto, 0, cmd[0]))
		elif cmd.cmdcode == T1CommandCode.hvcurveto:
			self._run_command(T1Command(T1CommandCode.rrcurveto, cmd[0], 0, cmd[1], cmd[2], 0, cmd[3]))
		elif cmd.cmdcode == T1CommandCode.vhcurveto:
			self._run_command(T1Command(T1CommandCode.rrcurveto, 0, cmd[0], cmd[1], cmd[2], cmd[3], 0))
		elif cmd.cmdcode == T1CommandCode.callsubr:
			if self._parent_font is None:
				self._log.error("Unable to call subroutine %s without parent.", cmd)
			else:
				if len(cmd.args) == 0:
					self._log.warning("Unable to call indirect subroutine with address from stack as of now.")
				else:
					subr = self._parent_font.get_subroutine(cmd[0])
					if subr is None:
						self._log.error("T1 font code referenced subroutine %s, but no such subroutine known. Ignoring.", cmd)
					else:
						self.run(subr.parse())
		elif cmd.cmdcode == T1CommandCode.callothersubr:
			self._log.warning("Unsupported right now: %s", cmd)
		elif cmd.cmdcode in [ T1CommandCode.vstem, T1CommandCode.hstem, T1CommandCode.vstem3, T1CommandCode.hstem3, T1CommandCode.dotsection ]:
			# Hint commands, ignore
			pass
		elif cmd.cmdcode == T1CommandCode.seac:
			accent_sidebearing = cmd[0]
			(accent_x, accent_y) = (cmd[1], cmd[2])
			(base_char_code, accent_char_code) = (cmd[3], cmd[4])
			base_char = PostScriptStandardCharacterName(base_char_code)
			accent_char = PostScriptStandardCharacterName(accent_char_code)
			if self._parent_font is None:
				self._log.error("Unable to set accent %s without parent.", cmd)
			else:
#				print("Adding", accent_char.name, "to", base_char.name, "at", (accent_x, accent_y))
				base_glyph = self._parent_font.get_glyph(base_char)
				accent_glyph = self._parent_font.get_glyph(accent_char)

				self.run(base_glyph.parse())
				self._pos = [ accent_x, accent_y ]
				self.run(accent_glyph.parse())
		elif cmd.cmdcode == T1CommandCode.closepath:
			if self._canvas is not None:
				self._canvas.line(self._pos, self._path[0])
			self._path = [ ]
		elif cmd.cmdcode in [ T1CommandCode.endchar, T1CommandCode.retrn ]:
			raise _T1ExecutionFinishedException()
		elif cmd.cmdcode in [  T1CommandCode.div, T1CommandCode.pop ]:
			# Not handled at the moment
			pass
		else:
			raise Exception(NotImplemented, cmd)

	def run(self, commands):
		try:
			for command in commands:
				self._run_command(command)
		except _T1ExecutionFinishedException:
			# return or endchar command received
			pass
