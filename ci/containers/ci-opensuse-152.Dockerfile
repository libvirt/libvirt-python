# THIS FILE WAS AUTO-GENERATED
#
#  $ lcitool dockerfile opensuse-152 libvirt+dist,libvirt-python
#
# https://gitlab.com/libvirt/libvirt-ci/-/commit/94c25bde639eb31ff2071fb6abfd3d5c777f4ab2

FROM registry.opensuse.org/opensuse/leap:15.2

RUN zypper update -y && \
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
           python3-nose \
           python3-setuptools \
           rpm-build && \
    zypper clean --all && \
    rpm -qa | sort > /packages.txt && \
    mkdir -p /usr/libexec/ccache-wrappers && \
    ln -s /usr/bin/ccache /usr/libexec/ccache-wrappers/cc && \
    ln -s /usr/bin/ccache /usr/libexec/ccache-wrappers/$(basename /usr/bin/gcc)

ENV LANG "en_US.UTF-8"
ENV PYTHON "/usr/bin/python3"
ENV CCACHE_WRAPPERSDIR "/usr/libexec/ccache-wrappers"
