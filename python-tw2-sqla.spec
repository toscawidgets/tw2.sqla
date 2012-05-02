%{!?python_sitelib: %global python_sitelib %(%{__python} -c "from distutils.sysconfig import get_python_lib; print get_python_lib()")}

%global modname tw2.sqla

Name:           python-tw2-sqla
Version:        2.0.1
Release:        1%{?dist}
Summary:        SQLAlchemy database layer for ToscaWidgets2

Group:          Development/Languages
License:        MIT
URL:            http://toscawidgets.org
Source0:        http://pypi.python.org/packages/source/t/%{modname}/%{modname}-%{version}.tar.gz
BuildArch:      noarch

# For building
BuildRequires:  python2-devel
BuildRequires:  python-setuptools
BuildRequires:  python-tw2-core
BuildRequires:  python-tw2-forms
BuildRequires:  python-tw2-dynforms
%if %{?rhel}%{!?rhel:0} >= 6
BuildRequires:  python-sqlalchemy0.7 >= 0.7
%else
BuildRequires:  python-sqlalchemy >= 0.7
%endif
BuildRequires:  python-zope-sqlalchemy

# For tests
BuildRequires:  python-nose
BuildRequires:  python-formencode
BuildRequires:  python-BeautifulSoup
BuildRequires:  python-strainer
BuildRequires:  python-webtest
BuildRequires:  python-elixir

# Templates for the test suite
BuildRequires:  python-genshi
BuildRequires:  python-mako
BuildRequires:  python-turbokid
BuildRequires:  python-turbocheetah

# Runtime requirements
Requires:  python-tw2-forms
Requires:  python-tw2-dynforms
%if %{?rhel}%{!?rhel:0} >= 6
Requires:  python-sqlalchemy0.7 >= 0.7
%else
Requires:  python-sqlalchemy >= 0.7
%endif
Requires:  python-zope-sqlalchemy

%description
tw2.sqla is a database layer for ToscaWidgets 2 and SQLAlchemy. It allows common
database tasks to be achieved with minimal code.

%prep
%setup -q -n %{modname}-%{version}

%if %{?rhel}%{!?rhel:0} >= 6

# Make sure that epel/rhel picks up the correct version of webob *and* SA
awk 'NR==1{print "import __main__; __main__.__requires__ = __requires__ = [\"WebOb>=1.0\", \"sqlalchemy>=0.7\"]; import pkg_resources"}1' setup.py > setup.py.tmp
mv setup.py.tmp setup.py

# Remove all the fancy nosetests configuration for older python
rm setup.cfg

%endif


%build
%{__python} setup.py build

%install
%{__python} setup.py install -O1 --skip-build \
    --install-data=%{_datadir} --root %{buildroot}

%check
%if %{?rhel}%{!?rhel:0} >= 6
# Don't actually run tests on el6.  There's an issue with python-elixir.
%else
PYTHONPATH=$(pwd) python setup.py test
%endif

%files
%doc README.rst LICENSE
%{python_sitelib}/*

%changelog
* Wed May 02 2012 Ralph Bean <rbean@redhat.com> - 2.0.1-1
- New upstream release, contains LICENSE.

* Wed May 02 2012 Ralph Bean <rbean@redhat.com> - 2.0.0-2
- Removed clean section
- Removed defattr in files section
- Removed unnecessary references to buildroot

* Wed Apr 11 2012 Ralph Bean <rbean@redhat.com> - 2.0.0-1
- Initial packaging for Fedora
