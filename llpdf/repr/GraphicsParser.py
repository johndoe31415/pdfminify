#!/usr/bin/python3
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

from . import tpg
from llpdf.types.PDFName import PDFName

def _to_hexstring(text):
	text = text[1 : -1]
	text = text.replace("\n", "")
	return bytes.fromhex(text)

class GraphCommand(object):
	def __init__(self, command, *args):
		self._command = command
		self._args = args

	@property
	def command(self):
		return self._command

	@property
	def args(self):
		return self._args

	def __repr__(self):
		return str(self)

	def __str__(self):
		if len(self._args) == 0:
			return "%s" % (self._command)
		else:
			return "%s(%s)" % (self._command, ", ".join(str(arg) for arg in self._args))

class GraphicsParser(tpg.VerboseParser):
	r"""
		separator space '[\s\n]+';

		token start_array '\[';
		token end_array '\]';
		token float   '-?\d*\.\d+'							$ float
		token integer   '-?\d+'								$ int
		token pdfname_token '/[a-zA-Z][-+a-zA-Z0-9]*'		$ PDFName
		token string '\([^()]*\)';
		token hexstring '<[\na-fA-F0-9]*>'					$ _to_hexstring
		token cmd134 '(SCN|scn|SC|sc)';
		token cmd0 '(BT|ET|BI|ID|EI|W\*|T\*|f\*|B\*|b\*|q|Q|h|S|s|f|F|B|b|n|W)';
		token cmd1 '(gs|CS|cs|sh|Do|Tj|TJ|Tc|Tw|Tz|TL|Tr|Ts|ri|w|J|j|M|i|G|g)';
		token cmd2 '(Td|TD|Tf|d0|m|l|d)';
		token cmd3 '(rg|RG)';
		token cmd4 '(re|v|y|K|k)';
		token cmd6 '(cm|Tm|d1|c)';

		START/e -> GraphExpression/e
		;

		GraphExpression/e ->								$ e = list()
							(
									GraphCommand/c			$ e.append(c)
							)*
		;


		GraphCommand/c -> (
							cmd0/c																									$ c = GraphCommand(c)
							| GraphParam/p1 (cmd1/c | cmd134/c)																		$ c = GraphCommand(c, p1)
							| GraphParam/p1 GraphParam/p2 cmd2/c																	$ c = GraphCommand(c, p1, p2)
							| GraphParam/p1 GraphParam/p2 GraphParam/p3 (cmd3/c | cmd134/c)											$ c = GraphCommand(c, p1, p2, p3)
							| GraphParam/p1 GraphParam/p2 GraphParam/p3 GraphParam/p4 (cmd4/c | cmd134/c)							$ c = GraphCommand(c, p1, p2, p3, p4)
							| GraphParam/p1 GraphParam/p2 GraphParam/p3 GraphParam/p4 GraphParam/p5 GraphParam/p6 cmd6/c			$ c = GraphCommand(c, p1, p2, p3, p4, p5, p6)
						)
		;

		GraphArray/a ->		start_array					$ a = list()
							(
								GraphParam/p			$ a.append(p)
							)* end_array
		;

		GraphParam/p -> (
							integer/p
							| float/p
							| GraphArray/p
							| string/p
							| pdfname_token/p
							| hexstring/p
						)
		;

	"""

	verbose = 0


def parse(text):
	try:
		parser = GraphicsParser()
		result = parser(text)
	except (tpg.LexicalError, tpg.SyntacticError) as e:
		print("-" * 120)
		print(text)
		print("-" * 120)
		print(text.split("\n")[e.line - 1])
		print((" " * (e.column - 1)) + "^")
		raise
	return result

if __name__ == "__main__":
	examples = [
		"q q q",
		"q q q Q 1 2 3 4 5 6 cm",
"""
q
Q q
79 841.89 516 -763 re W n
1 1 1 rg /a0 gs
79 1055.499 579.5 -976.5 re f
0.666656 0.666656 0.666656 RG 1 w
0 J
0 j
[ 1 1] 0.5 d
10 M q 0 1 -1 0 0 841.889764 cm
102.609 -79.5 -865 -485 re S Q
Q q
79.5 841.89 484.727 -762.391 re W n
q
0 866.230684 -486.499608 0 565.332662 78.832642 cm
/a0 gs /x5 Do
Q
1 1 1 rg /a0 gs
BT
0 66 -66 0 167.850006 107.849998 Tm
/f-0-0 1 Tf
[(FOO)3(BARY )3(BARFOO)3(BA)]TJ
0 -1.121212 Td
[(MOO KO)20(KOO)21(LOLS)3(KIX)]TJ
ET
Q
"""
	]

	pdf_parser = GraphicsParser()
	for example in examples:
#		lineno = 23; print(example.split("\n")[lineno - 1])
		result = pdf_parser(example)
		print(result)
