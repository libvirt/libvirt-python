# THIS FILE WAS AUTO-GENERATED
#
#  $ lcitool manifest ci/manifest.yml
#
# https://gitlab.com/libvirt/libvirt-ci

FROM quay.io/centos/centos:stream10

RUN dnf --quiet distro-sync -y && \
    dnf --quiet install 'dnf-command(config-manager)' -y && \
    dnf --quiet config-manager --set-enabled -y crb && \
    dnf --quiet install -y epel-release && \
    dnf --quiet install -y \
                ca-certificates \
                ccache \
                gcc \
                git \
                glibc-langpack-en \
                libvirt-devel \
                pkgconfig \
                python3 \
                python3-build \
                python3-devel \
                python3-lxml \
                python3-pip \
                python3-pytest \
                python3-setuptools \
                python3-wheel \
                rpm-build && \
    dnf --quiet autoremove -y && \
    dnf --quiet clean all -y && \
    rm -f /usr/lib*/python3*/EXTERNALLY-MANAGED && \
    rpm -qa | sort > /packages.txt && \
    mkdir -p /usr/libexec/ccache-wrappers && \
    ln -s /usr/bin/ccache /usr/libexec/ccache-wrappers/cc && \
    ln -s /usr/bin/ccache /usr/libexec/ccache-wrappers/gcc

ENV CCACHE_WRAPPERSDIR="/usr/libexec/ccache-wrappers"
ENV LANG="en_US.UTF-8"
ENV PYTHON="/usr/bin/python3"
