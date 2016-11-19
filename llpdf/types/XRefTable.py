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

class CompressedXRefEntry(object):
	def __init__(self, objid, inside_objid, index):
		"""Object 'objid' is compressed inside object (objid = 'inside_objid',
		gennum = 0) at index 'index'."""
		self._objid = objid
		self._inside_objid = inside_objid
		self._index = index

	@property
	def objid(self):
		return self._objid

	@property
	def gennum(self):
		return 0

	@property
	def inside_objid(self):
		return self._inside_objid

	@property
	def index(self):
		return self._index

	def __str__(self):
		return "CompXRefEntry <ObjId=%d, GenNum=%d> inside object %d[%d]" % (self.objid, self.gennum, self.inside_objid, self.index)

class UncompressedXRefEntry(object):
	def __init__(self, objid, gennum, offset):
		self._objid = objid
		self._gennum = gennum
		self._offset = offset

	@property
	def objid(self):
		return self._objid

	@property
	def gennum(self):
		return self._gennum

	@property
	def offset(self):
		return self._offset

	def __str__(self):
		return "UncompXRefEntry <ObjId=%d, GenNum=%d>: @0x%x" % (self.objid, self.gennum, self.offset)

class XRefTable(object):
	_log = logging.getLogger("llpdf.types.XRefTable")

	def __init__(self):
		self._content = { }

	def _read_next_xref_batch(self, f):
		pos = f.tell()
		entries_hdr = f.readline()
		try:
			entries_hdr = entries_hdr.decode("ascii").rstrip("\r\n").split()
		except UnicodeDecodeError:
			# XRef Table is at end or we cannot parse this.
			f.seek(pos)
			return False

		if len(entries_hdr) != 2:
			# XRef Table is at end or we cannot parse this.
			f.seek(pos)
			return False

		(start_id, entry_cnt) = (int(entries_hdr[0]), int(entries_hdr[1]))
		self._log.debug("XRef table has %d entries starting with objid %d", entry_cnt, start_id)
		for objid in range(start_id, start_id + entry_cnt):
			line = f.readline()
			parsed_line = line.decode("ascii").strip().split()
			if len(parsed_line) != 3:
				raise Exception("Expected XRef line to contain three entries, but %d found: %s" % (len(parsed_line), line))
			if parsed_line[2] not in [ "f", "n" ]:
				raise Exception("Expected XRef line to contain free or nonfree object, but found: %s" % (line))

			offset = int(parsed_line[0])
			gennum = int(parsed_line[1])
			used_object = (parsed_line[2] == "n")
			if used_object:
				self.add_entry(UncompressedXRefEntry(objid = objid, gennum = gennum, offset = offset))
		return True

	def read_xref_table_from_file(self, f):
		self._log.debug("Started reading trailing XRef table.")
		while True:
			if not self._read_next_xref_batch(f):
				return False

	def parse_xref_object(self, rawdata, index, field_lengths):
		assert(isinstance(index, list))
		assert((len(index) % 2) == 0)
		assert(len(index) == 2)			# For now, only this is supported
		assert(isinstance(rawdata, bytes))
		assert(len(field_lengths) == 3)
		entry_width = sum(field_lengths)
		assert((len(rawdata) % entry_width) == 0)
		entries = [ rawdata[i : i + entry_width] for i in range(0, len(rawdata), entry_width) ]

		field_1_offset = 0
		field_2_offset = field_lengths[0]
		field_3_offset = field_lengths[0] + field_lengths[1]
		for (objid, entry) in enumerate(entries, index[0]):
			type_field = self._to_int(entry[field_1_offset : field_2_offset])
			field_2 = self._to_int(entry[field_2_offset : field_3_offset])
			field_3 = self._to_int(entry[field_3_offset : ])
			if type_field == 0:
				# Linked list of free objects
				(next_free_objid, next_free_gennum) = (field_2, field_3)
#				if (next_free_objid == 0) and (next_free_gennum):
#					# TODO: Is my assumption true?
#					print("%d: Currently no next free object." % (objid))
#				else:
#					print("%d: Next free object: ObjId=%d, GenNum=%d" % (objid, next_free_objid, next_free_gennum))
			elif type_field == 1:
				# Uncompressed object
				(byte_offset, gennum) = (field_2, field_3)
#				print("%d: Uncompressed object at %d, gennum %d" % (objid, byte_offset, gennum))
				self.add_entry(UncompressedXRefEntry(objid = objid, gennum = gennum, offset = byte_offset))
			elif type_field == 2:
				# Compressed object
				(objstrm_objid, index) = (field_2, field_3)
#				print("%d: Compressed object inside ObjStm objid = %d, index %d" % (objid, objstrm_objid, index))
				self.add_entry(CompressedXRefEntry(objid = objid, inside_objid = objstrm_objid, index = index))

	def add_entry(self, entry):
		self._content[(entry.objid, entry.gennum)] = entry

	@staticmethod
	def _to_int(data):
		return sum(value << (byteno * 8) for (byteno, value) in enumerate(reversed(data)))

	def __iter__(self):
		return iter(self._content.items())

	def __len__(self):
		return len(self._content)

	def dump(self):
		for ((objid, gennum), entry) in sorted(self):
			print(entry)

	def __str__(self):
		return "XRefTable<%d entries>" % (len(self))

if __name__ == "__main__":
	with open("xref.bin", "rb") as f:
		data = f.read()

	x = XRefTable()
	x.parse_xref_object(data, 0, [ 1, 3, 1 ])
	x.dump()
	print(x)

