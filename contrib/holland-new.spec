# sitelib for noarch packages, sitearch for others (remove the unneeded one)
%{!?python_sitelib: %global python_sitelib %(%{__python} -c "from distutils.sysconfig import get_python_lib; print get_python_lib()")}
%{!?python_sitearch: %global python_sitearch %(%{__python} -c "from distutils.sysconfig import get_python_lib; print get_python_lib(1)")}
%global holland_version %(%{__python} setup.py --version)

Name:           holland
Version:        %{holland_version}
Release:        1%{?dist}
Summary:        Pluggable Backup Framework

Group:          Applications/Archiving
License:        BSD
URL:            http://hollandbackup.org
Source0:        %{name}-%{version}.tar.gz
BuildRoot:      %{_tmppath}/%{name}-%{version}-%{release}-root-%(%{__id_u} -n)

BuildArch:      noarch
BuildRequires:  python-devel python-setuptools

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


%package mysqldump
Summary: Logical mysqldump backup plugin for Holland
License: GPLv2
Group: Development/Libraries
Requires: %{name} = %{version}-%{release} %{name}-common = %{version}-%{release}

%description mysqldump
This plugin allows holland to perform logical backups of a MySQL database
using the mysqldump command.


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


%package mysqlhotcopy
Summary: Raw non-transactional backup plugin for Holland
License: GPLv2
Group: Development/Libraries
Requires: %{name} = %{version}-%{release} %{name}-common = %{version}-%{release}

%description mysqlhotcopy
This plugin allows holland to perform backups of MyISAM and other 
non-transactional table types in MySQL by issuing a table lock and copying the
raw files from the data directory.


%prep
%setup -q
find ./ -name setup.cfg -exec rm -f {} \;


%build
%{__python} setup.py build
cd docs
make html
rm -f build/html/.buildinfo
cd -

cd plugins/holland.lib.common
%{__python} setup.py build
cd -

cd plugins/holland.lib.mysql
%{__python} setup.py build
cd -

cd plugins/holland.backup.mysqldump
%{__python} setup.py build
cd -

cd plugins/holland.backup.mysql-lvm
%{__python} setup.py build
cd -

cd plugins/holland.backup.mysqlhotcopy
%{__python} setup.py build
cd -


%install
rm -rf %{buildroot}
%{__python} setup.py install -O1 --skip-build --root %{buildroot}
mkdir -p %{buildroot}%{_mandir}/man1
install -c -m 0644 docs/man/holland.1 %{buildroot}%{_mandir}/man1

cd plugins/holland.lib.common
%{__python} setup.py install -O1 --skip-build --root %{buildroot}
cd -

cd plugins/holland.lib.mysql
%{__python} setup.py install -O1 --skip-build --root %{buildroot}
cd -

cd plugins/holland.backup.mysqldump
%{__python} setup.py install -O1 --skip-build --root %{buildroot}
cd -

cd plugins/holland.backup.mysql-lvm
%{__python} setup.py install -O1 --skip-build --root %{buildroot}
cd -

cd plugins/holland.backup.mysqlhotcopy
%{__python} setup.py install -O1 --skip-build --root %{buildroot}
mkdir -p %{buildroot}%{_mandir}/man5
install -c -m 0644 docs/man/holland-mysqlhotcopy.5 %{buildroot}%{_mandir}/man5
cd -


%clean
rm -rf %{buildroot}


%files
%defattr(-,root,root,-)
%doc README INSTALL LICENSE docs/build/html/
%{_bindir}/holland
%{python_sitelib}/holland/core/
%{python_sitelib}/holland/cli/
%{python_sitelib}/holland-%{version}-*-nspkg.pth
%{python_sitelib}/holland-%{version}-*.egg-info
%{_mandir}/man1/holland.1*

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

%files mysqldump
%defattr(-,root,root,-)
%doc plugins/holland.backup.mysqldump/{README,LICENSE}
%{python_sitelib}/holland/backup/mysqldump/
%{python_sitelib}/holland.backup.mysqldump-%{version}-*-nspkg.pth
%{python_sitelib}/holland.backup.mysqldump-%{version}-*.egg-info

%files mysqllvm
%defattr(-,root,root,-)
%doc plugins/holland.backup.mysql-lvm/{README,LICENSE}
%{python_sitelib}/holland/backup/lvm/
%{python_sitelib}/holland/restore/lvm.py*
%{python_sitelib}/holland.backup.mysql_lvm-%{version}-*-nspkg.pth
%{python_sitelib}/holland.backup.mysql_lvm-%{version}-*.egg-info

%files mysqlhotcopy
%defattr(-,root,root,-)
%doc plugins/holland.backup.mysqlhotcopy/{README,LICENSE}
%{python_sitelib}/holland/backup/mysqlhotcopy.py*
%{python_sitelib}/holland.backup.mysqlhotcopy-%{version}-*-nspkg.pth
%{python_sitelib}/holland.backup.mysqlhotcopy-%{version}-*.egg-info
%{_mandir}/man5/holland-mysqlhotcopy.5*


%changelog
* Sat May 8 2010 Andrew Garner <andrew.garner@rackspace.com> - 0.9.9-1
- Initial spec build
