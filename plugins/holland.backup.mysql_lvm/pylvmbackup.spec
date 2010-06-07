# sitelib for noarch packages, sitearch for others (remove the unneeded one)
%{!?python_sitelib: %global python_sitelib %(%{__python} -c "from distutils.sysconfig import get_python_lib; print get_python_lib()")}
%define pylvmbackup_version %(%{__python} setup.py --version)

Name:           pylvmbackup
Version:        %{pylvmbackup_version}
Release:        3%{?dist}
Summary:        Utility for creating backups via LVM snapshots

Group:          Development/Languages
License:        Rackspace Proprietary
URL:            http://example.com/
Source0:        %{name}-%{version}.tar.gz
BuildRoot:      %{_tmppath}/%{name}-%{version}-%{release}-root-%(%{__id_u} -n)

BuildArch:      noarch
BuildRequires:  python-devel, python-setuptools

%description
pylvmbackup is a script for creating backups via LVM snapshots. pylvmbackup
can acquire MySQL locks to ensure consistency and perform InnoDB recovery
prior to making a backup. This script is inspired heavily by the excellent
mylvmbackup and other attempts are automating LVM snapshot based backups.


%prep
%setup -q


%build
%{__python} setup.py build


%install
rm -rf %{buildroot}
%{__python} setup.py install --skip-build --root %{buildroot}
%{__install} -Dpm 644 docs/%{name}.1 %{buildroot}/%{_mandir}/man1/%{name}.1
%{__install} -Dpm 600 examples/%{name}.conf %{buildroot}/%{_sysconfdir}/%{name}.conf

%clean
rm -rf %{buildroot}


%files
%defattr(-,root,root,-)
%config(noreplace,missingok) %attr(600, root, root) %{_sysconfdir}/%{name}.conf
%doc %{_mandir}/man1/%{name}.1.gz
%doc examples
# For noarch packages: sitelib
%{python_sitelib}/*
%_bindir/%{name}

%changelog
* Tue Jul 28 2009 Andrew Garner <andrew.garner@rackspace.com> - 0.4.2-3
- rebuilt

* Tue Jul 28 2009 Andrew Garner <andrew.garner@rackspace.com> - 0.4.2-2
- rebuilt

* Tue Jul 28 2009 Andrew Garner <andrew.garner@rackspace.com> - 0.4.2-1
- new minor version

* Sun Jul 26 2009 Andrew Garner <andrew.garner@rackspace.com> - 0.4.1-1
- new minor version

* Sun Jul 26 2009 Andrew Garner <andrew.garner@rackspace.com> - 0.4-2
- rebuilt

* Sun Jul 26 2009 Andrew Garner <andrew.garner@rackspace.com> - 0.4-1
- updated release

* Sun Jul 26 2009 Andrew Garner <andrew.garner@rackspace.com> - 0.3-3
- adding manpage and default config files

* Sun Jul 26 2009 Andrew Garner <andrew.garner@rackspace.com> - 0.3-2
- rebuilt

* Sun Jul 26 2009 Andrew Garner <andrew.garner@rackspace.com> - 0.3-1
- initial spec build
