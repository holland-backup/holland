# sitelib for noarch packages, sitearch for others (remove the unneeded one)
%{!?python_sitelib: %global python_sitelib %(%{__python} -c "from distutils.sysconfig import get_python_lib; print get_python_lib()")}
%{!?python_sitearch: %global python_sitearch %(%{__python} -c "from distutils.sysconfig import get_python_lib; print get_python_lib(1)")}
%{!?holland_version: %global holland_version 0.9.9}


Name:           holland
Version:        %{holland_version}
Release:        7%{?dist}
Summary:        Pluggable Backup Framework
Group:          Applications/Archiving
License:        BSD 
URL:            http://hollandbackup.org
Source0:        %{name}-%{version}.tar.gz
BuildRoot:      %{_tmppath}/%{name}-%{version}-%{release}-root-%(%{__id_u} -n)

BuildArch:      noarch
BuildRequires:  python-devel python-setuptools python-sphinx
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

%package example
Summary: Example Backup Provider Plugin for Holland
Group: Development/Libraries
Requires: %{name} = %{version}-%{release}

%description example
Example Backup Plugin for Holland

%package random
Summary: Random Backup Provider Plugin for Holland
Group: Development/Libraries
Requires: %{name} = %{version}-%{release}

%description random
Random Backup Provider Plugin for Holland

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

%package sqlite
Summary: SQLite Backup Provider Plugin for Holland
Group: Development/Libraries
Requires: %{name} = %{version}-%{release}
Requires: %{name}-common = %{version}-%{release}

%description sqlite 
SQLite Backup Provider Plugin for Holland


%prep
%setup -q
find ./ -name setup.cfg -exec rm -f {} \;

# cleanup, will be removed upstream at some point
rm plugins/ACTIVE

# incomplete/not ready
rm -rf plugins/holland.backup.pgdump

%build
%{__python} setup.py build

# docs
pushd docs
make html
rm -f build/html/.buildinfo
popd

# plugins
for i in $(ls ./plugins); do
    pushd plugins/${i}
        %{__python} setup.py build
    popd
done

%install
rm -rf %{buildroot}

%{__mkdir} -p 	%{buildroot}%{_sysconfdir}/holland/{backupsets,providers} \
		%{buildroot}%{_sysconfdir}/holland/backupsets/examples \
		%{buildroot}%{_localstatedir}/spool/holland \
		%{buildroot}%{_localstatedir}/log/holland/ \
		%{buildroot}%{_mandir}/man5

# holland-core
%{__python} setup.py install -O1 --skip-build --root %{buildroot} --install-scripts %{_sbindir}
%{__mkdir_p} -p %{buildroot}%{_mandir}/man1
install -m 0644 docs/man/holland.1 %{buildroot}%{_mandir}/man1
%{__mkdir_p} %{buildroot}%{python_sitelib}/holland/{lib,backup,commands,restore}

# all plugins
for i in $(ls ./plugins); do
    pushd plugins/${i}
        %{__python} setup.py install -O1 --skip-build --root %{buildroot}
    popd
done

# install configs
install -m 0640 config/holland.conf %{buildroot}%{_sysconfdir}/holland/
install -m 0640 config/backupsets/examples/* %{buildroot}%{_sysconfdir}/%{name}/backupsets/examples
install -m 0640 config/providers/* %{buildroot}%{_sysconfdir}/holland/providers/
install -c -m 0644 plugins/holland.backup.mysqlhotcopy/docs/man/holland-mysqlhotcopy.5 \
                   %{buildroot}%{_mandir}/man5

# logrotate
%{__mkdir} -p %{buildroot}%{_sysconfdir}/logrotate.d
cat > %{buildroot}%{_sysconfdir}/logrotate.d/holland <<EOF
/var/log/holland.log /var/log/holland/holland.log {
    rotate 4
    weekly
    compress
    missingok
    create root adm
}
EOF


%clean
rm -rf %{buildroot}


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
%{_sysconfdir}/holland/providers/README
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

%files example
%defattr(-,root,root,-)
%doc plugins/holland.backup.example/{README,LICENSE}
%{python_sitelib}/holland/backup/example.py*
%{python_sitelib}/holland.backup.example-%{version}-*-nspkg.pth
%{python_sitelib}/holland.backup.example-%{version}-*.egg-info
%{_sysconfdir}/holland/backupsets/examples/example.conf
%config(noreplace) %{_sysconfdir}/holland/providers/example.conf

%files random
%defattr(-,root,root,-)
%doc plugins/holland.backup.random/{README,LICENSE}
%{python_sitelib}/holland/backup/random.py*
%{python_sitelib}/holland.backup.random-%{version}-*-nspkg.pth
%{python_sitelib}/holland.backup.random-%{version}-*.egg-info
%{_sysconfdir}/holland/backupsets/examples/random.conf
%config(noreplace) %{_sysconfdir}/holland/providers/random.conf

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
%{_sysconfdir}/holland/backupsets/examples/mysqldump.conf
%config(noreplace) %{_sysconfdir}/holland/providers/mysqldump.conf

%files mysqllvm
%defattr(-,root,root,-)
%doc plugins/holland.backup.mysql-lvm/{README,LICENSE}
%{python_sitelib}/holland/backup/lvm/
%{python_sitelib}/holland/restore/lvm.py*
%{python_sitelib}/holland.backup.mysql_lvm-%{version}-*-nspkg.pth
%{python_sitelib}/holland.backup.mysql_lvm-%{version}-*.egg-info
%{_sysconfdir}/holland/backupsets/examples/mysql-lvm.conf
%config(noreplace) %{_sysconfdir}/holland/providers/mysql-lvm.conf

%files mysqlhotcopy
%defattr(-,root,root,-)
%doc plugins/holland.backup.mysqlhotcopy/{README,LICENSE}
%{python_sitelib}/holland/backup/mysqlhotcopy.py*
%{python_sitelib}/holland.backup.mysqlhotcopy-%{version}-*-nspkg.pth
%{python_sitelib}/holland.backup.mysqlhotcopy-%{version}-*.egg-info
%{_sysconfdir}/holland/backupsets/examples/mysqlhotcopy.conf
%config(noreplace) %{_sysconfdir}/holland/providers/mysqlhotcopy.conf
%{_mandir}/man5/holland-mysqlhotcopy.5*

%files sqlite 
%defattr(-,root,root,-)
%doc plugins/holland.backup.sqlite/{README,LICENSE}
%{python_sitelib}/holland/backup/sqlite.py*
%{python_sitelib}/holland.backup.sqlite-%{version}-*-nspkg.pth
%{python_sitelib}/holland.backup.sqlite-%{version}-*.egg-info
%{_sysconfdir}/holland/backupsets/examples/sqlite.conf
%config(noreplace) %{_sysconfdir}/holland/providers/sqlite.conf

%changelog
* Wed May 19 2010 BJ Dierkes <wdierkes@rackspace.com> - 0.9.9-7
- BuildRequires: python-sphinx (to build docs)

* Mon May 17 2010 BJ Dierkes <wdierkes@rackspace.com> - 0.9.9-6
- Added sqlite plugin
- Loop over plugins rather than explicity build/install each.  Removes
  currently incomplete plugins first (pgdump)

* Fri May 14 2010 Tim Soderstrom <tsoderst@racksapce.com> - 0.9.9-5
- Added random plugin

* Mon May 10 2010 Andrew Garner <andrew.garner@rackspace.com> - 0.9.9-4
- Added missingok to holland.logrotate

* Sat May 8 2010 Andrew Garner <andrew.garner@rackspace.com> - 0.9.9-3
- Cleaned up /usr/share/docs/holland-* to only include html user documentation
  rather than everything in docs/
- /var/spool/holland and /var/log/holland/ are no longer world-readable
- /etc/holland/backupsets/examples is now a symlink to examples in the
  /usr/share/docs/holland-* directory
- The plugins/ACTIVE file is no longer used in order to have more flexibility
  in handling each individual plugin
- The setup.py --record mechanism is no longer used
- holland/{lib,commands,backup,restore} are now owned by the main holland
  package.

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
