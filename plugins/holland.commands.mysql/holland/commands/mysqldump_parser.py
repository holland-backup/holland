import os
import sys

"""
-- Current Database:
-- Dump completed
-- Dumping data
-- Final view
-- Table structure
-- Temporary table
-- Dumping routines
-- Position to
"""

class CountingStreamWrapper(object):
    def __init__(self, stream):
        self.stream = stream
        self.offset = 0
        self.lineno = 0

    def next(self):
        line = self.stream.next()
        self.offset += len(line)
        self.lineno += 1
        return line

    def __iter__(self):
        return self

class MySQLDumpParser(object):

    def __init__(self, stream, callback=None):
        self.stream = CountingStreamWrapper(stream)
        self.db = None
        self.tbl = None
        self.callback = callback or (lambda *x: 1)
        self.DISPATCH = {
            '-- Current Database:' : self.parse_database,
            '-- Table structure' : self.parse_table,
            '-- Temporary table' : self.parse_initial_view,
            '-- Final view' : self.parse_final_view,
            '-- Dumping data' : self.start_data_dump,
            '-- Dumping routines' : self.parse_routines,
            '-- Position to' : self.parse_master_data,
            '-- Dump completed' : self.dump_complete,
        }

    def parse_database(self, line, lineno, offset):
        # just got a -- Current Database line, so parse it out
        self.db = line.split('`')[1]
        # Run through lines until we hit a blank line:
        for line in self.stream:
            if not line.strip(): break

        # Run through lines until we hit a '^--$'
        for line in self.stream:
            if line.startswith('--'):
                break
        self.callback('database', 
                      self.db, 
                      lineno, 
                      offset, 
                      self.stream.offset - len(line))

    def parse_table(self, line, lineno, offset):
        self.tbl = line.split('`',1)[1].strip()[:-1]
        # Skip over rest of header
        for line in self.stream:
            if not line.strip():
                break
        # Run through stream until we hit next header block
        for line in self.stream:
            if line.startswith('--'):
                break
        self.callback('table_schema', self.tbl, lineno, offset, self.stream.offset - len(line)) 

    def parse_initial_view(self, line, lineno, offset):
        view = line.split('`',1)[1].strip()[:-1]
        for line in self.stream:
            if not line.strip():
                break
        for line in self.stream:
            if line.startswith('--'):
                break
        self.callback('fake_view', view, lineno, offset, self.stream.offset - len(line))

    def parse_final_view(self, line, lineno, offset):
        view = line.split('`', 1)[1].rstrip()[:-1]
        for line in self.stream:
            if not line.strip():
                break
        for line in self.stream:
            if line.startswith('--'):
                break
        self.callback('final_view', view, lineno, offset, self.stream.offset - len(line))

    def start_data_dump(self, line, lineno, offset):
        tbl = line.split('`',1)[1].strip()[:-1]
        for line in self.stream:
            if not line.strip():
                break
        for line in self.stream:
            if line.startswith('--'):
                break
        self.callback('table_data', tbl, lineno, offset, self.stream.offset - len(line))

    def parse_routines(self, line, lineno, offset):
        db = line
        for line in self.stream:
            if not line.strip():
                break
        for line in self.stream:
            if line.startswith('--'):
                break
        self.callback('routines', db, lineno, offset, self.stream.offset - len(line))

    def parse_master_data(self, line, lineno, offset):
        for line in self.stream:
            if line.startswith('-- CHANGE MASTER') or \
                line.startswith('CHANGE MASTER'):
                self.callback('master_data', line.strip(), lineno, offset, self.stream.offset)
                break

    def dump_complete(self, line, lineno, offset):
        self.callback('complete', line.strip(), lineno, offset, self.stream.offset)

    def parse(self):
        self.header = ''
        # first, parse header:
        for line in self.stream:
            if self.stream.lineno > 6 and not line.startswith('--'):
                break
            else:
                self.header += line

        for line in self.stream:
            if line.startswith('-- '):
                lookup = ' '.join(line.split()[0:3])
                if lookup not in self.DISPATCH:
                    self.callback('unknown', 
                                  line, 
                                  self.stream.lineno,
                                  self.stream.offset - len(line),
                                  self.stream.offset)
                else:
                    self.DISPATCH[lookup](line, 
                                          self.stream.lineno,
                                          self.stream.offset - len(line))
