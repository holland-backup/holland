# sitelib for noarch packages, sitearch for others (remove the unneeded one)
%{!?python_sitelib: %global python_sitelib %(%{__python} -c "from distutils.sysconfig import get_python_lib; print get_python_lib()")}
%{!?python_sitearch: %global python_sitearch %(%{__python} -c "from distutils.sysconfig import get_python_lib; print get_python_lib(1)")}
%{!?holland_version: %global holland_version 0.9.9}


Name:           holland
Version:        %{holland_version}
Release:        3%{?dist}
Summary:        Pluggable Backup Framework

Group:          Applications/Archiving
License:        BSD
URL:            http://hollandbackup.org
Source0:        %{name}-%{version}.tar.gz
BuildRoot:      %{_tmppath}/%{name}-%{version}-%{release}-root-%(%{__id_u} -n)

BuildArch:      noarch
BuildRequires:  python-devel python-setuptools
Requires:       python-setuptools

%description
A pluggable backup framework which focuses on, but is not limited to, highly
configurable database backups.


%package common
Summary:        Common library functionality for Holland Plugins
License:        GPLv2
Group:          Applications/Archiving
Requires:       %{name} = %{version}-%{release} MySQL-python

%description common
Library for common functionality used by holland plugins


%package maatkit
Summary: Holland mk-parallel-dump plugin
Group: Development/Libraries
Requires: %{name} = %{version}-%{release}, %{name}-common = %{version}-%{release}
Requires: maatkit

%description maatkit
This plugin provides support for holland to perform MySQL backups using the 
mk-parallel-dump script from the Maatkit toolkit.  


%package mysqldump
Summary: Logical mysqldump backup plugin for Holland
License: GPLv2
Group: Development/Libraries
Requires: %{name} = %{version}-%{release} %{name}-common = %{version}-%{release}

%description mysqldump
This plugin allows holland to perform logical backups of a MySQL database
using the mysqldump command.


%package mysqlhotcopy
Summary: Raw non-transactional backup plugin for Holland
License: GPLv2
Group: Development/Libraries
Requires: %{name} = %{version}-%{release} %{name}-common = %{version}-%{release}

%description mysqlhotcopy
This plugin allows holland to perform backups of MyISAM and other 
non-transactional table types in MySQL by issuing a table lock and copying the
raw files from the data directory.


%package mysqllvm
Summary: Holland LVM snapshot backup plugin for MySQL 
License: GPLv2
Group: Development/Libraries
Requires: %{name} = %{version}-%{release} %{name}-common = %{version}-%{release}
Provides: %{name}-lvm = %{version}-%{release}
Obsoletes: %{name}-lvm < 0.9.8
Requires: lvm2 MySQL-python tar

%description mysqllvm
This plugin allows holland to perform LVM snapshot backups of a MySQL database
and to generate a tar archive of the raw data directory.


%prep
%setup -q
find ./ -name setup.cfg -exec rm -f {} \;


%build
%{__python} setup.py build
cd docs
make html
rm -f build/html/.buildinfo
cd -

# library : holland.lib.common
cd plugins/holland.lib.common
%{__python} setup.py build
cd -

# library : holland.lib.mysql
cd plugins/holland.lib.mysql
%{__python} setup.py build
cd -

# plugin : holland.backup.maatkit
cd plugins/holland.backup.maatkit
%{__python} setup.py build
cd -

# plugin : holland.backup.mysqldump
cd plugins/holland.backup.mysqldump
%{__python} setup.py build
cd -

# plugin : holland.backup.mysqlhotcopy
cd plugins/holland.backup.mysqlhotcopy
%{__python} setup.py build
cd -

# plugin : holland.backup.mysql-lvm
cd plugins/holland.backup.mysql-lvm
%{__python} setup.py build
cd -


%install
rm -rf %{buildroot}

# /etc configs
install -m 0750 -d %{buildroot}%{_sysconfdir}/holland/{backupsets,providers}
install -m 0640 config/holland.conf %{buildroot}%{_sysconfdir}/holland/
ln -s ../../..%{_docdir}/%{name}-%{version}/examples \
    %{buildroot}%{_sysconfdir}/%{name}/backupsets/examples

# backup directory
install -m 0750 -d %{buildroot}%{_localstatedir}/spool/holland

# log directory
install -m 0750 -d %{buildroot}%{_localstatedir}/log/holland/

# logrotate
%{__mkdir} -p %{buildroot}%{_sysconfdir}/logrotate.d
cat > %{buildroot}%{_sysconfdir}/logrotate.d/holland <<EOF
/var/log/holland/holland.log {
    rotate 4
    weekly
    compress
    create root adm
}
EOF

# holland-core
%{__python} setup.py install -O1 --skip-build --root %{buildroot} --install-scripts %{_sbindir}
%{__mkdir_p} -p %{buildroot}%{_mandir}/man1
install -m 0644 docs/man/holland.1 %{buildroot}%{_mandir}/man1
# ensure we can %ghost this - we should own the directory
%{__mkdir_p} %{buildroot}%{python_sitelib}/holland/{lib,backup,commands,restore}

# library : holland.lib.common
cd plugins/holland.lib.common
%{__python} setup.py install -O1 --skip-build --root %{buildroot}
cd -

# library : holland.lib.mysql
cd plugins/holland.lib.mysql
%{__python} setup.py install -O1 --skip-build --root %{buildroot}
cd -

# plugin : holland.backup.maatkit
cd plugins/holland.backup.maatkit
%{__python} setup.py install -O1 --skip-build --root %{buildroot}
cd -
install -m 0640 config/providers/maatkit.conf %{buildroot}%{_sysconfdir}/holland/providers/

install -m 0640 config/providers/mysqldump.conf %{buildroot}%{_sysconfdir}/holland/providers/
# plugin : holland.backup.mysqldump
cd plugins/holland.backup.mysqldump
%{__python} setup.py install -O1 --skip-build --root %{buildroot}
cd -
install -m 0640 config/providers/mysqldump.conf %{buildroot}%{_sysconfdir}/holland/providers/

# plugin : holland.backup.mysqlhotcopy
cd plugins/holland.backup.mysqlhotcopy
%{__python} setup.py install -O1 --skip-build --root %{buildroot}
mkdir -p %{buildroot}%{_mandir}/man5
install -c -m 0644 docs/man/holland-mysqlhotcopy.5 %{buildroot}%{_mandir}/man5
cd -
install -m 0640 config/providers/mysqlhotcopy.conf %{buildroot}%{_sysconfdir}/holland/providers/

# plugin : holland.backup.mysql-lvm
cd plugins/holland.backup.mysql-lvm
%{__python} setup.py install -O1 --skip-build --root %{buildroot}
cd -
install -m 0640 config/providers/mysql-lvm.conf %{buildroot}%{_sysconfdir}/holland/providers/


%clean
rm -rf %{buildroot}


%pre
if [ $1 -gt 1 -a -d /etc/holland/backupsets/examples/ ]; then
    mv /etc/holland/backupsets/examples/ /etc/holland/backupsets/example.rpmsave
fi
exit 0


%files
%defattr(-,root,root,-)
%doc README INSTALL LICENSE config/backupsets/examples/ docs/build/html/
%{_sbindir}/holland
%dir %{python_sitelib}/holland/
%{python_sitelib}/holland/core/
%{python_sitelib}/holland-%{version}-*-nspkg.pth
%{python_sitelib}/holland-%{version}-*.egg-info
%{_mandir}/man1/holland.1*
%{_localstatedir}/log/holland/
%{python_sitelib}/holland/commands/*.py*
%{_sysconfdir}/holland/backupsets/examples
%attr(0750,root,root) %dir %{_sysconfdir}/holland/
%attr(0750,root,root) %dir %{_sysconfdir}/holland/backupsets
%attr(0750,root,root) %dir %{_sysconfdir}/holland/providers
%attr(0640,root,root) %config(noreplace) %{_sysconfdir}/holland/holland.conf
%attr(0644,root,root) %config(noreplace) %{_sysconfdir}/logrotate.d/holland
%attr(0750,root,root) %{_localstatedir}/spool/holland
# virtual namespaces
%dir %{python_sitelib}/holland/backup/
%dir %{python_sitelib}/holland/restore/
%dir %{python_sitelib}/holland/commands/
%dir %{python_sitelib}/holland/lib/

%files common
%defattr(-,root,root,-)
%doc plugins/holland.lib.common/{README,LICENSE}
%{python_sitelib}/%{name}/lib/compression.py*
%{python_sitelib}/%{name}/lib/archive/
%{python_sitelib}/%{name}/lib/safefilename.py*
%{python_sitelib}/%{name}/lib/which.py*
%{python_sitelib}/%{name}/lib/multidict.py*
%{python_sitelib}/%{name}/lib/mysql/
%{python_sitelib}/holland.lib.common-%{version}-*-nspkg.pth
%{python_sitelib}/holland.lib.common-%{version}-*.egg-info
%{python_sitelib}/holland.lib.mysql-%{version}-*-nspkg.pth
%{python_sitelib}/holland.lib.mysql-%{version}-*.egg-info

%files maatkit
%defattr(-,root,root,-)
%doc plugins/holland.backup.maatkit/{README,LICENSE}
%{python_sitelib}/holland/backup/maatkit.py*
%{python_sitelib}/holland.backup.maatkit-%{version}-*-nspkg.pth
%{python_sitelib}/holland.backup.maatkit-%{version}-*.egg-info
%config(noreplace) %{_sysconfdir}/holland/providers/maatkit.conf

%files mysqldump
%defattr(-,root,root,-)
%doc plugins/holland.backup.mysqldump/{README,LICENSE}
%{python_sitelib}/holland/backup/mysqldump/
%{python_sitelib}/holland.backup.mysqldump-%{version}-*-nspkg.pth
%{python_sitelib}/holland.backup.mysqldump-%{version}-*.egg-info
%config(noreplace) %{_sysconfdir}/holland/providers/mysqldump.conf

%files mysqllvm
%defattr(-,root,root,-)
%doc plugins/holland.backup.mysql-lvm/{README,LICENSE}
%{python_sitelib}/holland/backup/lvm/
%{python_sitelib}/holland/restore/lvm.py*
%{python_sitelib}/holland.backup.mysql_lvm-%{version}-*-nspkg.pth
%{python_sitelib}/holland.backup.mysql_lvm-%{version}-*.egg-info
%config(noreplace) %{_sysconfdir}/holland/providers/mysql-lvm.conf

%files mysqlhotcopy
%defattr(-,root,root,-)
%doc plugins/holland.backup.mysqlhotcopy/{README,LICENSE}
%{python_sitelib}/holland/backup/mysqlhotcopy.py*
%{python_sitelib}/holland.backup.mysqlhotcopy-%{version}-*-nspkg.pth
%{python_sitelib}/holland.backup.mysqlhotcopy-%{version}-*.egg-info
%config(noreplace) %{_sysconfdir}/holland/providers/mysqlhotcopy.conf
%{_mandir}/man5/holland-mysqlhotcopy.5*


%changelog
* Sat May 8 2010 Andrew Garner <andrew.garner@rackspace.com> - 0.9.9-3
- Major spec cleanup

* Wed Apr 14 2010 Andrew Garner <andrew.garner@rackspace.com> - 0.9.9-2
- Updated rpm for new tree layout

* Tue Apr 13 2010 BJ Dierkes <wdierkes@rackspace.com> - 0.9.9-1.rs
- Removed -commvault subpackage
- Removed mysql-lvm config file hack
- Changed URL to http://hollandbackup.org
- No longer package plugins as eggs
- Conditionally BuildRequire: python-nose and run nose tests if _with_tests

* Thu Apr 07 2010 BJ Dierkes <wdierkes@rackspace.com> - 0.9.8-2.rs
- Rename holland-lvm to holland-mysqllvm, Obsoletes: holland-lvm
- Manually install mysql-lvm.conf provider config (fixed in 0.9.9)
- Install man files to _mandir
- Make logrotate.d/holland config(noreplace)

* Fri Apr 02 2010 BJ Dierkes <wdierkes@rackspace.com> - 0.9.8-1.rs
- Latest stable source from upstream.

* Wed Dec 09 2009 BJ Dierkes <wdierkes@rackspace.com> - 0.9.7dev-1.rs
- Latest development trunk.
- Adding /etc/logrotate.d/holland logrotate script.

* Wed Dec 09 2009 BJ Dierkes <wdierkes@rackspace.com> - 0.9.6-1.rs
- Latest stable sources from upstream.

* Fri Dec 04 2009 BJ Dierkes <wdierkes@rackspace.com> - 0.9.5dev-1.rs
- Removing mysqlcmds by default
- Adding lvm subpackage

* Thu Oct 08 2009 BJ Dierkes <wdierkes@rackspace.com> - 0.9.4-1.1.rs
- BuildRequires: python-dev
- Rebuilding for Fedora Core 

* Tue Sep 15 2009 BJ Dierkes <wdierkes@rackspace.com> - 0.9.4-1.rs
- Latest sources.

* Mon Jul 13 2009 BJ Dierkes <wdierkes@rackspace.com> - 0.9.3-1.rs
- Latest sources.

* Mon Jul 06 2009 BJ Dierkes <wdierkes@rackspace.com> - 0.9.2-1.1.rs
- Rebuild

* Thu Jun 11 2009 BJ Dierkes <wdierkes@rackspace.com> - 0.9.2-1.rs
- Latest sources from upstream.
- Only require epel for el4 (for now), and use PreReq rather than Requires.
- Require 'mysql' rather than 'mysqlclient'

* Wed Jun 03 2009 BJ Dierkes <wdierkes@rackspace.com> - 0.9.1-1.rs
- Latest sources from upstream.
- Requires epel.

* Mon May 18 2009 BJ Dierkes <wdierkes@rackspace.com> - 0.9.0-1.rs
- Latest from upstream
- Adding mysqlcmds package

* Tue May 05 2009 BJ Dierkes <wdierkes@rackspace.com> - 0.4-1.2.rs
- Rebuild from trunk

* Sun May 03 2009 BJ Dierkes <wdierkes@rackspace.com> - 0.4-1.1.rs
- Rebuild from trunk
- Adding commvault addon package.
- Removing Patch2: holland-0.3-config.patch
- Disable backupsets by default 

* Sat May 02 2009 BJ Dierkes <wdierkes@rackspace.com> - 0.3.1-1.2.rs
- Build as noarch.

* Tue Apr 29 2009 BJ Dierkes <wdierkes@rackspace.com> - 0.3.1-1.rs
- Latest sources.

* Tue Apr 28 2009 BJ Dierkes <wdierkes@rackspace.com> - 0.3-1.rs
- Latest sources.
- Removed tests for time being
- Added Patch2: holland-0.3-config.patch
- Sub package holland-mysqldump obsoletes holland-mysql = 1.0.  Resolves
  tracker [#1189].

* Fri Apr 17 2009 BJ Dierkes <wdierkes@rackspace.com> - 0.2-2.rs
- Rebuild.

* Wed Mar 11 2009 BJ Dierkes <wdierkes@rackspace.com> - 0.2-1.rs
- Latest sources from upstream.

* Fri Feb 20 2009 BJ Dierkes <wdierkes@rackspace.com> - 0.1.1.rs
- Updated with subpackages/plugins

* Wed Jan 28 2009 BJ Dierkes <wdierkes@rackspace.com> - 0.1-1.rs
- Initial spec build
