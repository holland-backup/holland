%{!?python_sitelib: %define python_sitelib %(%{__python} -c "from distutils.sysconfig import get_python_lib; print get_python_lib()")}
%{!?pybasever: %define pybasever %(%{__python} -c "import sys ; print sys.version[0:3]")}

%define _plugindir %{_datadir}/holland/plugins
%define _backupdir %{_localstatedir}/spool/holland
%define _logdir %{_localstatedir}/log/holland
%define _confdir %{_sysconfdir}/holland

# optional plugins
%define with_mysqlcmds 0

# used by dev tools
%define src_version @@@VERSION@@@ 


Summary: Pluggable Backup Framework 
Name: holland
Version: %{src_version}%{?src_dev_tag} 
Release: 2.rs%{?dist}
License: Proprietary 
Group: Applications/Databases 
URL: http://hollandbackup.org 
Vendor: Rackspace US, Inc.
Source0: %{name}-%{src_version}.tar.gz
BuildRoot: %{_tmppath}/%{name}-%{version}-%{release}-buildroot
BuildArch: noarch

BuildRequires: python-devel, python-setuptools, grep, sed, gawk, findutils
Requires: python >= %{pybasever}, python-setuptools
Requires: %{name}-common


%description
A pluggable backup framework which focuses on, but is not limited to, highly 
configurable database backups. 


%package common
Summary: Common Library Plugins for Holland
Group: Development/Libraries
Requires: %{name} = %{version}-%{release}, mysql, MySQL-python

%description common
Common Library Plugins for Holland

%package mysqldump
Summary: MySQL Dump Backup Provider Plugin for Holland
Group: Development/Libraries
Requires: %{name} = %{version}-%{release}

%description mysqldump
MySQL Dump Backup Provider Plugin for Holland.

%package example
Summary: Example Backup Provider Plugin for Holland
Group: Development/Libraries
Requires: %{name} = %{version}-%{release}

%description example 
Example Backup Provider Plugin for Holland.

%package maatkit 
Summary: Maatkit Backup Provider Plugin for Holland
Group: Development/Libraries
Requires: %{name} = %{version}-%{release}, %{name}-common = %{version}-%{release}
Requires: maatkit

%description maatkit
Maatkit Backup Provider Plugin for Holland

%package mysqlhotcopy
Summary: MySQL Hot Copy Backup Provider Plugin for Holland
Group: Development/Libraries
Requires: %{name} = %{version}-%{release}, %{name}-common = %{version}-%{release}

%description mysqlhotcopy
MySQL Hot Copy Backup Provider Plugin for Holland.

%package mysqllvm 
Summary: MySQL LVM Backup Provider Plugin for Holland
Group: Development/Libraries
Requires: %{name} = %{version}-%{release}, %{name}-common = %{version}-%{release}
Obsoletes: %{name}-lvm < 0.9.8
Requires: lvm2, mysql-server, MySQL-python, tar

%description mysqllvm
MySQL LVM Backup Provider Plugin for Holland.

%if %{with_mysqlcmds}
%package mysqlcmds
Summary: MySQL Support Commands for Holland
Group: Development/Libraries
Requires: %{name} = %{version}-%{release}, %{name}-mysqldump = %{version}-%{release}, mysql

%description mysqlcmds
MySQL Support Commands for Holland.
%endif

%prep
%setup -q -n %{name}-%{src_version}
find ./ -name setup.cfg -exec rm -f {} \;
sed -i 's/^backupsets = default/backupsets = /g' config/holland.conf

%build
%{__python} setup.py build 
# FIX ME - Tests fail
#%{__python} setup.py test 


%install
[ "%{buildroot}" != "/" ] && rm -rf %{buildroot}

%{__mkdir_p} %{buildroot}%{_plugindir} \
             %{buildroot}%{_backupdir} \
             %{buildroot}%{_logdir} \
             %{buildroot}%{_confdir} \
             %{buildroot}%{_confdir}/providers \
             %{buildroot}%{_confdir}/backupsets \
             %{buildroot}%{_mandir}/man1 \
             %{buildroot}%{_sysconfdir}

%{__python} setup.py install \
    --prefix=%{_prefix} \
    --root=%{buildroot} \
    --skip-build \
    --install-scripts=%{_sbindir}

# plugins
for plugin in $(cat plugins/ACTIVE); do
    short_name=$(echo $plugin | awk -F . {' print $3 '})
    if [ -e config/providers/$short_name.conf ]; then
        install -m 0640 config/providers/$short_name.conf \
            %{buildroot}%{_confdir}/providers/
    fi
    cd plugins/$plugin
    %{__python} setup.py install --prefix=%{_prefix} --root=%{buildroot} --install-scripts=%{_sbindir} --record=rpm_manifest.txt
    # clip extraneous egg-info/ entries - we only capture the directory
    %{__sed} -i -e '\_.*.egg-info/_d' rpm_manifest.txt 
    cd -
done

install -m 0640 config/holland.conf %{buildroot}%{_confdir}/holland.conf
cp -a config/backupsets/examples %{buildroot}%{_confdir}/backupsets

# man
install -m 0644 docs/man/holland*.1 %{buildroot}%{_mandir}/man1

# logrotate
%{__mkdir} -p %{buildroot}%{_sysconfdir}/logrotate.d
cat >%{buildroot}%{_sysconfdir}/logrotate.d/holland <<EOF
/var/log/holland.log /var/log/holland/holland.log {
    rotate 4
    weekly
    compress
    create root adm
}
EOF

%clean
[ "%{buildroot}" != "/" ] && rm -rf %{buildroot}

%files
%defattr(-, root, root)
%doc docs config 
%{python_sitelib}/holland
%attr(0644,root,root) %config(noreplace) %{_sysconfdir}/logrotate.d/holland
%attr(0755,root,root) %dir %{_backupdir}
%attr(0755,root,root) %dir %{_logdir}
%attr(655,root,root)%dir  %{_plugindir}
%attr(754,root,root) %{_sbindir}/holland
%attr(755,root,root) %dir %{_confdir}
%attr(755,root,root) %dir %{_confdir}/backupsets
%attr(640,root,root) %{_confdir}/backupsets/*
%attr(755,root,root) %dir %{_confdir}/providers
%attr(640,root,root) %config(noreplace) %{_confdir}/holland.conf
%{python_sitelib}/%{name}-%{src_version}-py%{pybasever}-nspkg.pth
%{python_sitelib}/%{name}-%{src_version}-py%{pybasever}.egg-info
%{_mandir}/man1/holland*.1.gz

%files common -f plugins/holland.lib.common/rpm_manifest.txt
%defattr(-, root, root)
%{python_sitelib}/holland.lib.mysql-%{src_version}-py%{pybasever}-nspkg.pth
%{python_sitelib}/holland.lib.mysql-%{src_version}-py%{pybasever}.egg-info

%files mysqldump -f plugins/holland.backup.mysqldump/rpm_manifest.txt
%defattr(-, root, root)
%attr(640,root,root) %config(noreplace) %{_confdir}/providers/mysqldump.conf

%files mysqlhotcopy -f plugins/holland.backup.mysqlhotcopy/rpm_manifest.txt
%defattr(-, root, root)
%attr(640,root,root) %config(noreplace) %{_confdir}/providers/mysqlhotcopy.conf

%files maatkit -f plugins/holland.backup.maatkit/rpm_manifest.txt
%defattr(-, root, root)
%attr(640,root,root) %config(noreplace) %{_confdir}/providers/maatkit.conf

%files example -f plugins/holland.backup.example/rpm_manifest.txt
%defattr(-, root, root)
%attr(640,root,root) %config(noreplace) %{_confdir}/providers/example.conf

%files mysqllvm -f plugins/holland.backup.mysql-lvm/rpm_manifest.txt
%defattr(-, root, root)
%attr(640,root,root) %config(noreplace) %{_confdir}/providers/mysql-lvm.conf

%changelog
* Wed Apr 14 2010 Andrew Garner <andrew.garner@rackspace.com> - 0.9.9-2
- Updated rpm for new tree layout

* Tue Apr 13 2010 BJ Dierkes <wdierkes@rackspace.com> - 0.9.9-1.rs
- Removed -commvault subpackage
- Removed mysql-lvm config file hack
- Changed URL to http://hollandbackup.org

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
