"""MySQLDump single-pass output filtering"""
import re
import sys
import textwrap

# For bailing out early, but with cleanup
CLEANUP = """\
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;\
"""


def parse_header(parser):
    """Parse the mysqldump header comments and session variables"""
    stream = parser.input
    result = []
    for lineno, line in enumerate(stream):
        result.append(line)
        if line == "\n":
            break
        # Try to bail out early if we're really not reading a dump file
        if not line.startswith('--'):
            filename = getattr(stream, 'name', '<PIPE>')
            filename = filename.replace('fdopen', 'PIPE')

            raise SyntaxError("Invalid dump file detected", (filename,
                                                             lineno + 1,
                                                             0, # offset
                                                             'Expected initial'
                                                            + ' comment "--"'))

    for line in stream:
        if line == "\n":
            break
        result.append(line)

    if not parser.binlog:
        result.append("/*!40101 SET @OLD_SQL_LOG_BIN=@@SQL_LOG_BIN*/;\n")
        result.append("/*!40101 SET SQL_LOG_BIN = 0 */;\n")
    result.append("\n")

    return ''.join(result)

def emit_master_data(parser, line):
    """Parse master replication data"""
    results = [
        "--\n",
        line,
        parser.input.next(), # consume --
        parser.input.next(), # consume eol
    ]
    master_data = parser.input.next()
    parser.input.next() # consume eol
    master_data = master_data.lstrip(' -')
    # Remove comment
    if not parser.replication:
        master_data = '-- ' + master_data

    results.append(master_data)
    results.append("\n")

    yield ''.join(results)

def emit_change_database(parser, line):
    """Parse a database section"""
    parser.current_db = line.split(None, 3)[-1].rstrip()[1:-1]
    parser.current_tbl = None
    should_filter = parser.filter()

    rewrite_db = parser.rewrite_db(parser.current_db)

    results = ["--\n"]

    results.append(line.replace(parser.current_db, rewrite_db))
    results.append(parser.input.next()) # consume --
    results.append(parser.input.next()) # consume eol

    if not should_filter:
        yield ''.join(results)

    ddl = parser.input.next()

    # This will be the final view recreation section
    if ddl.startswith('USE '):
        yield "USE `%s`;\n" % parser.rewrite_db(ddl.split(None, 1)[1].rstrip()[1:-2])
        # consume next line - either newline, or a comment, which gets handled by our harness 
        yield parser.input.next()
    else:
        db = parser.current_db
        rewritten_db = parser.rewrite_db(db)
        ddl = ddl.replace(db.replace('`', '``'), rewritten_db.replace('`', '``'))
        yield ddl
        yield parser.input.next() # consume newline after CREATE DATABASE
        # Initial database creation section
        peek = parser.input.next()
        if peek.startswith('USE '):
            # USE line, we should rewrite
            eol = parser.input.next() # consume eol (or possibly start of eoh)
            if not should_filter:
                yield "USE `%s`;\n" % parser.rewrite_db(peek.split(None, 1)[1].rstrip()[1:-2])
                yield eol
    
def _flush_default_database(parser):
    """When parsing a SQL file with no USE `database` statement
    this gets run before the first table structure is emitted.

    parser.rewrite_db(None) will be called - if nothing is returned,
    we will abort.
    """
    defaultdb = parser.rewrite_db(None)

    if not defaultdb:
        raise ValueError("No defaultdb set and no USE `database` line found!")
 
    parser.current_db = defaultdb

    result = textwrap.dedent("""
    --
    -- Current Database: `%(db)s`
    --

    CREATE DATABASE /*!32312 IF NOT EXISTS*/ `%(db)s` /*!40100 DEFAULT CHARACTER SET %(charset)s */;

    USE `%(db)s`
     
    """ % { 'db' : parser.rewrite_db(defaultdb), 'charset' : 'utf8' }).lstrip()

    return result

def emit_table_structure(parser, line):
    """Parse a table structure section"""

    if not parser.current_db:
        yield _flush_default_database(parser)

    parser.current_tbl = line.split(None, 5)[-1].rstrip()[1:-1]

    results = [
        "--\n",
        line,
        parser.input.next(), # consume --
        parser.input.next()  # consume eol
    ]

    for line in parser.input:
        results.append(line)
        if line == "\n":
            break

    if not parser.filter():
        yield ''.join(results)

def emit_table_data(parser, line):
    """Parse a table data section"""
    parser.current_tbl = line.split(None, 5)[-1].rstrip()[1:-1]
    if not parser.filter():
        yield "--\n"
        yield line
        yield parser.input.next() # consume --
        yield parser.input.next() # consume eol

    for line in parser.input:
        if not parser.filter():
            yield line
        if line == "\n":
            break

def emit_temporary_view(parser, line):
    """Parse initial view temporary table"""
    
    parser.current_tbl = line.split(None, 6)[-1].rstrip()[1:-1]

    results = [
        "--\n",
        line,
        parser.input.next(), # consume --
        parser.input.next(), # consume eol
    ]
    for line in parser.input:
        results.append(line)
        if line == "\n":
            break

    if not parser.filter():
        yield ''.join(results)

def emit_final_view(parser, line):
    """Parse final view section"""
    
    parser.current_tbl = line.split(None, 6)[-1].rstrip()[1:-1]
    should_filter = parser.filter()

    results = [
        "--\n",
        line,
        parser.input.next(), # consume --
        parser.input.next(), # consume eol
    ]

    if not should_filter:
        yield ''.join(results)

    for line in parser.input:
        if not should_filter:
            yield line
        if line == "\n":
            break


def emit_database_routines(parser, line):
    """Parse stored procedure/routines"""

    parser.current_tbl = None
    parser.current_db = line.split(None, 5)[-1].rstrip()[1:-1]
    should_filter = parser.filter()

    results = [
        "--\n",
        line,
        parser.input.next(), # consume --
        parser.input.next(), # consume eol
    ]

    for line in parser.input:
        if line.startswith('--'):
            break
        if not should_filter:
            yield line

def emit_restore_session(parser, line):
    results = []

    # TIME_ZONE is in 5.0+, and formatted weird, probably concatenated
    # with the previous section
    if 'TIME_ZONE' in line:
        results += ["\n"]
        parser.input.next() # consume eol
    results += [line]
    for line in parser.input:
        results += [line]
        if line == "\n":
            break
    if not parser.binlog:
        results.insert(-1, "/*!40101 SET SQL_LOG_BIN=@OLD_SQL_LOG_BIN*/;\n")

    yield ''.join(results)
        
def emit_flush_privileges(parser, line):
    """Parser flush privileges"""
    yield line

def emit_dump_finish(parser, line):
    """Parse dump completion"""
    yield line

_DISPATCH = (
    ('-- Table', emit_table_structure),
    ('-- Dumping data', emit_table_data),
    ('-- Current', emit_change_database),
    ('-- Temporary', emit_temporary_view),
    ('-- Final', emit_final_view),
    ('-- Dumping routines', emit_database_routines),
    ('-- Position', emit_master_data),
    ('/*!40101 SET SQL_MODE=', emit_restore_session),
    ('-- Dump ', emit_dump_finish),
    ('-- Flush ', emit_flush_privileges)
)

class Parser(object):
    def __init__(self, input, schema_filter=None, binlog=True, replication=False, dbrewriter=None):
        if isinstance(input, basestring):
            input = open(input, 'r')
        self.input = input
        self.schema_filter = schema_filter
        self.binlog = binlog
        self.replication=replication
        self.dbrewriter = dbrewriter
        self.current_db = None
        self.current_tbl = None

    def rewrite_db(self, name):
        if self.dbrewriter:
            return self.dbrewriter(name)
        else:
            return name

    def dispatch(self, line):
        for pattern, emit in _DISPATCH:
            if line.startswith(pattern):
                for chunk in emit(self, line):
                    #XXX: This is not very pretty and depends heavily on our emitter implementation
                    if chunk and chunk.startswith("/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;"):
                        yield emit_restore_session(self, chunk).next()
                        break
                    else:
                        yield chunk
                break

    def parse(self):
        yield parse_header(self)
        for line in self.input:
            for chunk in self.dispatch(line):
                yield chunk

    def filter(self):
        """Return whether the current database, table is filtered"""
        if self.schema_filter:
            result = self.schema_filter.is_filtered(self.current_db, self.current_tbl)
            return result
        # default, no filtering
        return False

    def __iter__(self):
        for chunk in self.parse():
            yield chunk

if __name__ == '__main__':
    def rewriter(name):
        mapper = {
            'world' : 'world_new',
            'employees' : 'employees_rack',
            'sakila' : 'pagila',
            'test' : 'racktest',
        }
        return mapper.get(name, name)

    import sys
    p = Parser(sys.stdin,binlog=False, dbrewriter=rewriter)
    from filter import SchemaFilter
    f = SchemaFilter()
    p.schema_filter = f
    #f.tables = ['sakila.film']

    for chunk in p:
        if chunk:
            print chunk,
