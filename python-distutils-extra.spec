# Copyright 2022 Wong Hoi Sing Edison <hswong3i@pantarei-design.com>
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

%global debug_package %{nil}

Name: python-distutils-extra
Epoch: 100
Version: 2.39
Release: 1%{?dist}
BuildArch: noarch
Summary: Integrate more support into Python's distutils
License: GPL-2.0-or-later
URL: https://salsa.debian.org/python-team/packages/python-distutils-extra/-/tags
Source0: %{name}_%{version}.orig.tar.gz
BuildRequires: fdupes
BuildRequires: python-rpm-macros
BuildRequires: python3-devel
BuildRequires: python3-setuptools

%description
Enables you to easily integrate gettext support, themed icons and
scrollkeeper based documentation into Python's distutils.

%prep
%autosetup -T -c -n %{name}_%{version}-%{release}
tar -zx -f %{S:0} --strip-components=1 -C .

%build
%py3_build

%install
%py3_install
find %{buildroot}%{python3_sitelib} -type f -name '*.pyc' -exec rm -rf {} \;
fdupes -qnrps %{buildroot}%{python3_sitelib}

%check

%if 0%{?suse_version} > 1500 || 0%{?centos_version} == 700
%package -n python%{python3_version_nodots}-distutils-extra
Summary: Integrate more support into Python's distutils
Requires: python3
Provides: python3-distutils-extra = %{epoch}:%{version}-%{release}
Provides: python3dist(distutils-extra) = %{epoch}:%{version}-%{release}
Provides: python%{python3_version}-distutils-extra = %{epoch}:%{version}-%{release}
Provides: python%{python3_version}dist(distutils-extra) = %{epoch}:%{version}-%{release}
Provides: python%{python3_version_nodots}-distutils-extra = %{epoch}:%{version}-%{release}
Provides: python%{python3_version_nodots}dist(distutils-extra) = %{epoch}:%{version}-%{release}

%description -n python%{python3_version_nodots}-distutils-extra
Enables you to easily integrate gettext support, themed icons and
scrollkeeper based documentation into Python's distutils.

%files -n python%{python3_version_nodots}-distutils-extra
%license LICENSE
%{python3_sitelib}/*
%endif

%if !(0%{?suse_version} > 1500) && !(0%{?centos_version} == 700)
%package -n python3-distutils-extra
Summary: Integrate more support into Python's distutils
Requires: python3
Provides: python3-distutils-extra = %{epoch}:%{version}-%{release}
Provides: python3dist(distutils-extra) = %{epoch}:%{version}-%{release}
Provides: python%{python3_version}-distutils-extra = %{epoch}:%{version}-%{release}
Provides: python%{python3_version}dist(distutils-extra) = %{epoch}:%{version}-%{release}
Provides: python%{python3_version_nodots}-distutils-extra = %{epoch}:%{version}-%{release}
Provides: python%{python3_version_nodots}dist(distutils-extra) = %{epoch}:%{version}-%{release}

%description -n python3-distutils-extra
Enables you to easily integrate gettext support, themed icons and
scrollkeeper based documentation into Python's distutils.

%files -n python3-distutils-extra
%license LICENSE
%{python3_sitelib}/*
%endif

%changelog
