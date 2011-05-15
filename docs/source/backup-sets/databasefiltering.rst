**databases** = <glob>

**exclude-databases** = <glob>

**tables** = <glob>

**exclude-tables** = <glob>

**engines** = <glob>

**exclude-engines** == <glob>

The above options accept GLOBs in comma-separated lists. Multiple 
filtering options can be specified. When filtering on tables, be sure to 
include both the database and table name. 

Be careful with quotes. Normally these are not needed, but  when quotes 
are necessary, be sure to only quote each filtering statement, as 
opposed to putting quotes around all statements.
