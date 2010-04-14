Frequently Asked Questions
==========================

Here are some common questions that seem to pop up regularly when dealing
with Holland, MySQL, and backups in general:

.. toctree::
   :maxdepth: 2
   :glob:

* **Holland sounds awesome! But how do I install it?**

    The easiest way to install Holland is via the provided RPM and DEB 
    packages. If you are using a platform that does not support either of
    these package formats, Holland can be installed just like any other 
    Python program that uses Eggs.
    
    If you are a Rackspace Managed Hosting customer, simply ask your support 
    team about Holland and they would be happy to install it for you!
    
* **I am using MySQL with MyISAM tables. Can Holland backup my tables without imposing costly locks that can bring down my website?**

    It depends. As of Holland 0.4, there are no providers that can produce
    consistent and lockless backups for MyISAM tables. It is possible to have
    near lockless backups when using LVM, however there is currently no
    provider that supports LVM at this time (though that is planned). Even
    if there was, LVM would still need to be setup on the system running
    MySQL.
    
    However, Holland is replication-aware. That means it is possible to 
    setup MySQL replication and do backups on the slave server. That will
    still either lock the tables on the slave or stop slave services for
    the duration of the backup, however these backups will not affect the
    master server.
    
    On an aside, if you are using nothing but MyISAM tables, unless you have
    a clear and concise reason to do so, consider using InnoDB. Chances are
    that you will get much better performance from InnoDB - at least for
    most database designs commonly used to power web-applications.
    
* **I found a bug in Holland, what do I do?**

    Bugs and feature requests are tracked via our GitHub project:

        http://github.com/holland-backup/holland/issues

    
    The Holland Core Developers can also be contacted via our mailing list:

        holland-devel@googlegroups.com

