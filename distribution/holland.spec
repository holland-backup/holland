# Setting initial dist defaults.  Do not modify these.
# Note: Mock sets these up... but we need to default for manual builds.
%{!?el3:%define el3 0}
%{!?el4:%define el4 0}
%{!?el5:%define el5 0}
%{!?rhel:%define rhel 'empty'}

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


Summary: Holland is a Pluggable Backup Framework 
Name: holland
Version: %{src_version}%{?src_dev_tag} 
Release: 1.rs%{?dist}
License: Undetermined 
Group: Applications/Databases 
URL: https://gforge.rackspace.com/gf/project/holland
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
Summary: Holland Common Library Plugins
Group: Development/Libraries
Requires: %{name} = %{version}-%{release}, mysql, MySQL-python

%description common
Holland Common Library Plugins

%package mysqldump
Summary: Holland MySQL Dump Backup Provider Plugin
Group: Development/Libraries
Requires: %{name} = %{version}-%{release}

%description mysqldump
Holland MySQL Dump Backup Provider Plugin

%package example
Summary: Holland Example Backup Provider Plugin
Group: Development/Libraries
Requires: %{name} = %{version}-%{release}

%description example 
Holland Example Backup Provider Plugin

%package maatkit 
Summary: Holland Maatkit Backup Provider Plugin
Group: Development/Libraries
Requires: %{name} = %{version}-%{release}, %{name}-common = %{version}-%{release}
Requires: maatkit

%description maatkit
Holland Maatkit Backup Provider Plugin

%package mysqlhotcopy
Summary: Holland MySQL Hot Copy Backup Provider Plugin
Group: Development/Libraries
Requires: %{name} = %{version}-%{release}, %{name}-common = %{version}-%{release}

%description mysqlhotcopy
Holland MySQL Hot Copy Backup Provider Plugin

%package commvault 
Summary: Holland CommVault Addon
Group: Development/Libraries
Requires: %{name} = %{version}-%{release}, %{name}-common = %{version}-%{release}

%description commvault 
This package provides the holland commvault command plugin, enabling CommVault
environments to trigger a backup through holland.

%package mysql-lvm 
Summary: Holland LVM Backup Provider Plugin
Group: Development/Libraries
Provides: holland-lvm = 0.9.8
Obsoletes: holland-lvm < 0.9.8
Requires: %{name} = %{version}-%{release}, %{name}-common = %{version}-%{release}
Requires: lvm2, mysql-server, MySQL-python, tar

%description mysql-lvm
Holland LVM Backup Provider Plugin

%if %{with_mysqlcmds}
%package mysqlcmds
Summary: Holland MySQL support commands
Group: Development/Libraries
Requires: %{name} = %{version}-%{release}, %{name}-mysqldump = %{version}-%{release}, mysql

%description mysqlcmds
Holland MySQL support commands.
%endif

%prep
%setup -q -n %{name}-%{src_version}
find ./ -name setup.cfg -exec rm -f {} \;
sed -i 's/^backupsets = default/backupsets = /g' config/holland.conf

# FIX ME: remove this after its removed in trunk
rm -rf plugins/holland.lib.common/holland/lib/compression.old/

%build
# build core
pushd holland-core
%{__python} setup.py build 

# FIX ME - Tests fail
#%{__python} setup.py test 
popd


%install
[ "%{buildroot}" != "/" ] && rm -rf %{buildroot}

%{__mkdir_p} %{buildroot}%{_plugindir} \
             %{buildroot}%{_backupdir} \
             %{buildroot}%{_logdir} \
             %{buildroot}%{_confdir} \
             %{buildroot}%{_confdir}/providers \
             %{buildroot}%{_confdir}/backupsets \
             %{buildroot}%{_sysconfdir}

pushd holland-core
%{__python} setup.py install \
    --prefix=%{_prefix} \
    --root=%{buildroot} \
    --install-scripts=%{_sbindir}
popd

# plugins
for plugin in $(cat plugins/ACTIVE); do
    short_name=$(echo $plugin | awk -F . {' print $3 '})
    if [ -e config/providers/$short_name.conf ]; then
        install -m 0640 config/providers/$short_name.conf \
            %{buildroot}%{_confdir}/providers/
    fi
    pushd plugins/$plugin
    %{__python} setup.py bdist_egg -d %{buildroot}%{_plugindir}
    popd
done

# addons
for addon in $(cat addons/ACTIVE); do
    pushd addons/$addon
    %{__python} setup.py install \
        --prefix=%{_prefix} \
        --root=%{buildroot} \
        --install-scripts=%{_sbindir}
    popd
done

install -m 0640 config/holland.conf %{buildroot}%{_confdir}/holland.conf
cp -a config/backupsets/examples %{buildroot}%{_confdir}/backupsets


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

%pre
%post
%preun
%postun

%files
%defattr(-, root, root)
%doc docs config 
%{python_sitelib}/holland
%attr(0644,root,root) %{_sysconfdir}/logrotate.d/holland
%attr(0750,root,root) %dir %{_backupdir}
%attr(0750,root,root) %dir %{_logdir}
%attr(655,root,root)%dir  %{_plugindir}
%attr(750,root,root) %{_sbindir}/holland
%attr(750,root,root) %dir %{_confdir}
%attr(750,root,root) %dir %{_confdir}/backupsets
%attr(640,root,root) %{_confdir}/backupsets/*
%attr(750,root,root) %dir %{_confdir}/providers
%attr(640,root,root) %config(noreplace) %{_confdir}/holland.conf
%{python_sitelib}/%{name}-%{src_version}-py%{pybasever}-nspkg.pth
%{python_sitelib}/%{name}-%{src_version}-py%{pybasever}.egg-info


%files common
%defattr(-, root, root)
%{_plugindir}/holland.lib.common-*.egg
%{_plugindir}/holland.lib.mysql-*.egg

%files mysqldump
%defattr(-, root, root)
%attr(640,root,root) %config(noreplace) %{_confdir}/providers/mysqldump.conf
%{_plugindir}/holland.backup.mysqldump-*.egg

%files mysqlhotcopy
%defattr(-, root, root)
%attr(640,root,root) %config(noreplace) %{_confdir}/providers/mysqlhotcopy.conf
%{_plugindir}/holland.backup.mysqlhotcopy-*.egg

%files maatkit
%defattr(-, root, root)
%attr(640,root,root) %config(noreplace) %{_confdir}/providers/maatkit.conf
%{_plugindir}/holland.backup.maatkit-*.egg

%files example
%defattr(-, root, root)
%{_plugindir}/holland.backup.example-*.egg
%attr(640,root,root) %dir %{_confdir}/providers/example.conf

%files commvault 
%defattr(-, root, root)
%{python_sitelib}/holland_commvault-*.egg-info*
%{python_sitelib}/holland_commvault
%{_sbindir}/holland_cvmysqlsv

%files mysql-lvm
%defattr(-, root, root)
%attr(640,root,root) %config(noreplace) %{_confdir}/providers/mysql-lvm.conf
%{_plugindir}/holland.backup.mysql_lvm-*.egg

%if %{with_mysqlcmds}
%files example
%defattr(-, root, root)
%{_plugindir}/holland.backup.example-*.egg
%endif

%changelog
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
