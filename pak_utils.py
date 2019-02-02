#!/usr/bin/env python

# Original file: http://code.google.com/searchframe#OAMlx_jo-ck/src/tools/grit/grit/format/data_pack.py
# Copyright (c) 2012 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.
# (http://code.google.com/searchframe#OAMlx_jo-ck/src/LICENSE)

# This file:
#
# Copyright (c) 2012 Adobe Systems Incorporated. All rights reserved.
#  
# Permission is hereby granted, free of charge, to any person obtaining a
# copy of this software and associated documentation files (the "Software"), 
# to deal in the Software without restriction, including without limitation 
# the rights to use, copy, modify, merge, publish, distribute, sublicense, 
# and/or sell copies of the Software, and to permit persons to whom the 
# Software is furnished to do so, subject to the following conditions:
#  
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#  
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, 
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER 
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING 
# FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER 
# DEALINGS IN THE SOFTWARE.


'''Provides functions to handle .pak files as provided by Chromium. If the optional argument is a file, it will be unpacked, if it is a directory, it will be packed.'''

import collections
import exceptions
import os
import struct
import sys
import re
import shutil

PACK_FILE_VERSION = 5
HEADER_LENGTH = 2 * 4 + 1  # Two uint32s. (file version, number of entries) and
                           # one uint8 (encoding of text resources)
BINARY, UTF8, UTF16 = range(3)


class WrongFileVersion(Exception):
  pass

class DataPackSizes(object):
  def __init__(self, header, id_table, alias_table, data):
    self.header = header
    self.id_table = id_table
    self.alias_table = alias_table
    self.data = data
  @property
  def total(self):
    return sum(v for v in self.__dict__.itervalues())
  def __iter__(self):
    yield ('header', self.header)
    yield ('id_table', self.id_table)
    yield ('alias_table', self.alias_table)
    yield ('data', self.data)
  def __eq__(self, other):
    return self.__dict__ == other.__dict__
  def __repr__(self):
    return self.__class__.__name__ + repr(self.__dict__)

class DataPackContents(object):
  def __init__(self, resources, encoding, version, aliases, sizes):
    # Map of resource_id -> str.
    self.resources = resources
    # Encoding (int).
    self.encoding = encoding
    # Version (int).
    self.version = version
    # Map of resource_id->canonical_resource_id
    self.aliases = aliases
    # DataPackSizes instance.
    self.sizes = sizes


def ReadDataPack(input_file):
  """Reads a data pack file and returns a dictionary."""
  with open(input_file, "rb") as file:
    data = file.read()
  original_data = data

  # Read the header.
  version = struct.unpack('<I', data[:4])[0]
  if version == 4:
    resource_count, encoding = struct.unpack('<IB', data[4:9])
    alias_count = 0
    header_size = 9
  elif version == 5:
    encoding, resource_count, alias_count = struct.unpack('<BxxxHH', data[4:12])
    header_size = 12
  else:
    raise WrongFileVersion('Found version: ' + str(version))
  resources = {}
  kIndexEntrySize = 2 + 4  # Each entry is a uint16 and a uint32.
  def entry_at_index(idx):
    offset = header_size + idx * kIndexEntrySize
    return struct.unpack('<HI', data[offset:offset + kIndexEntrySize])
  prev_resource_id, prev_offset = entry_at_index(0)
  for i in xrange(1, resource_count + 1):
    resource_id, offset = entry_at_index(i)
    resources[prev_resource_id] = data[prev_offset:offset]
    prev_resource_id, prev_offset = resource_id, offset
  id_table_size = (resource_count + 1) * kIndexEntrySize
  # Read the alias table.
  kAliasEntrySize = 2 + 2  # uint16, uint16
  def alias_at_index(idx):
    offset = header_size + id_table_size + idx * kAliasEntrySize
    return struct.unpack('<HH', data[offset:offset + kAliasEntrySize])
  aliases = {}
  for i in xrange(alias_count):
    resource_id, index = alias_at_index(i)
    aliased_id = entry_at_index(index)[0]
    aliases[resource_id] = aliased_id
    resources[resource_id] = resources[aliased_id]
  alias_table_size = kAliasEntrySize * alias_count
  sizes = DataPackSizes(
      header_size, id_table_size, alias_table_size,
      len(data) - header_size - id_table_size - alias_table_size)
  assert sizes.total == len(data), 'original={} computed={}'.format(
      len(data), sizes.total)
  return DataPackContents(resources, encoding, version, aliases, sizes)


def WriteDataPackToString(resources, encoding):
  """Returns a string with a map of id=>data in the data pack format."""
  ret = []
  # Compute alias map.
  resource_ids = sorted(resources)
  # Use reversed() so that for duplicates lower IDs clobber higher ones.
  id_by_data = {resources[k]: k for k in reversed(resource_ids)}
  # Map of resource_id -> resource_id, where value < key.
  alias_map = {k: id_by_data[v] for k, v in resources.iteritems()
               if id_by_data[v] != k}
  # Write file header.
  resource_count = len(resources) - len(alias_map)
  # Padding bytes added for alignment.
  ret.append(struct.pack('<IBxxxHH', PACK_FILE_VERSION, encoding,
                         resource_count, len(alias_map)))
  HEADER_LENGTH = 4 + 4 + 2 + 2
  # Each main table entry is: uint16 + uint32 (and an extra entry at the end).
  # Each alias table entry is: uint16 + uint16.
  data_offset = HEADER_LENGTH + (resource_count + 1) * 6 + len(alias_map) * 4
  # Write main table.
  index_by_id = {}
  deduped_data = []
  index = 0
  for resource_id in resource_ids:
    if resource_id in alias_map:
      continue
    data = resources[resource_id]
    index_by_id[resource_id] = index
    ret.append(struct.pack('<HI', resource_id, data_offset))
    data_offset += len(data)
    deduped_data.append(data)
    index += 1
  assert index == resource_count
  # Add an extra entry at the end.
  ret.append(struct.pack('<HI', 0, data_offset))
  # Write alias table.
  for resource_id in sorted(alias_map):
    index = index_by_id[alias_map[resource_id]]
    ret.append(struct.pack('<HH', resource_id, index))
  # Write data.
  ret.extend(deduped_data)
  return ''.join(ret)


def WriteDataPack(resources, output_file, encoding):
  """Write a map of id=>data into output_file as a data pack."""
  content = WriteDataPackToString(resources, encoding)
  with open(output_file, "wb") as file:
    file.write(content)

def PackDirectoryIntoFile(directory, pakFile):
  if not os.path.isdir(directory):
    print "%s is not a directory (or does not exist)" % (directory)
    return False
  
  files = os.listdir(directory)
  files.sort()
  
  numeric = re.compile("^\d+$")
  
  data = {}
  for (id) in files:
    if not numeric.match(id):
      continue
    input_file = "%s/%s" % (directory, id)
    with open(input_file, "rb") as file:
      data[int(id)] = file.read()

  WriteDataPack(data, pakFile, UTF8)
  
  return True

def UnpackFileIntoDirectory(pakFile, directory):
  if not os.path.isfile(pakFile):
    print "%s is not a file (or does not exist)" % (pakFile)
    return False

  if os.path.exists(directory):
    shutil.rmtree(directory)
  os.makedirs(directory)

  data = ReadDataPack(pakFile)
  for (resource_id, contents) in data.resources.iteritems():
    output_file = "%s/%s" % (directory, resource_id)
    with open(output_file, "wb") as file:
      file.write(contents)

def FindIdForNameInHeaderFile(name, headerFile):
  print "Extracting ID for %s from header file %s" % (name, headerFile)
  with open(headerFile, "rb") as file:
    match = re.search("#define %s (\d+)" % (name), file.read())
    return int(match.group(1)) if match else None 

def main():
  if len(sys.argv) <= 1:
    print "Usage: %s <file_or_directory>" % sys.argv[0]
    return
  
  path = sys.argv[1]
  if os.path.isdir(path):
    PackDirectoryIntoFile(path, "resources.pak")
  else:
    UnpackFileIntoDirectory(path, re.sub("\.pak$", "", path))

if __name__ == '__main__':
  main()