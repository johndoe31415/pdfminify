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

import enum

class AnnotationFlag(enum.IntEnum):
	Invisible = (1 << 0)
	Hidden = (1 << 1)
	Print = (1 << 2)
	NoZoom = (1 << 3)
	NoRotate = (1 << 4)
	NoView = (1 << 5)
	ReadOnly = (1 << 6)
	Locked = (1 << 7)
	ToggleNoView = (1 << 8)
	LockedContents = (1 << 9)

class FieldFlag(enum.IntEnum):
	ReadOnly = (1 << 0)
	Required = (1 << 1)
	NoExport = (1 << 2)

class SignatureFlag(enum.IntEnum):
	SignaturesExist = (1 << 0)
	AppendOnly = (1 << 1)

class FontDescriptorFlag(enum.IntEnum):
	FixedPitch = (1 << 0)
	Serif = (1 << 1)
	Symbolic = (1 << 2)
	Script = (1 << 3)
	Nonsymbolic = (1 << 5)
	Italic = (1 << 6)
	AllCap = (1 << 16)
	SmallCap = (1 << 17)
	ForceBold = (1 << 18)
