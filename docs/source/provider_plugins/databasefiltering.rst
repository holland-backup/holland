Database and Table filtering
----------------------------

**databases** = <glob>

**exclude-databases** = <glob>

**tables** = <glob>

**exclude-tables** = <glob>

The above options accepts GLOBs in comma-separated lists. Multiple 
filtering options can be specified. When filtering on tables, be sure to 
include both the database and table name. 

Be careful with quotes. Normally these are not needed, but  when quotes 
are necessary, be sure to only quote each filtering statement, as 
opposed to putting quotes around all statements.

Below are a few examples of how these can be applied:

Default (backup everything)::

  databases = *
  tables = *

Using database inclusion and exclusions::

 databases = drupal*, smf_forum, 
 exclude-databases = drupal5

Including Tables::

  tables = phpBB.sucks, drupal6.node*, smf_forum.*

Excluding Tables::

  exclude-tables = mydb.uselesstable1, x_cart.*, *.sessions

