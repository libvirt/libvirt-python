# THIS FILE WAS AUTO-GENERATED
#
#  $ lcitool manifest ci/manifest.yml
#
# https://gitlab.com/libvirt/libvirt-ci

function install_buildenv() {
    zypper update -y
    zypper install -y \
           ca-certificates \
           ccache \
           gcc \
           git \
           glibc-locale \
           libvirt-devel \
           pkgconfig \
           python3-base \
           python3-devel \
           python3-lxml \
           python3-pip \
           python3-pytest \
           python3-setuptools \
           rpm-build
    rpm -qa | sort > /packages.txt
    mkdir -p /usr/libexec/ccache-wrappers
    ln -s /usr/bin/ccache /usr/libexec/ccache-wrappers/cc
    ln -s /usr/bin/ccache /usr/libexec/ccache-wrappers/gcc
}

export CCACHE_WRAPPERSDIR="/usr/libexec/ccache-wrappers"
export LANG="en_US.UTF-8"
export PYTHON="/usr/bin/python3"
