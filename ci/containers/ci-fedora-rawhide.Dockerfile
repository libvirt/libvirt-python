# THIS FILE WAS AUTO-GENERATED
#
#  $ lcitool dockerfile fedora-rawhide libvirt+dist,libvirt-python
#
# https://gitlab.com/libvirt/libvirt-ci/-/commit/94c25bde639eb31ff2071fb6abfd3d5c777f4ab2

FROM registry.fedoraproject.org/fedora:rawhide

RUN dnf update -y --nogpgcheck fedora-gpg-keys && \
    dnf install -y nosync && \
    echo -e '#!/bin/sh\n\
if test -d /usr/lib64\n\
then\n\
    export LD_PRELOAD=/usr/lib64/nosync/nosync.so\n\
else\n\
    export LD_PRELOAD=/usr/lib/nosync/nosync.so\n\
fi\n\
exec "$@"' > /usr/bin/nosync && \
    chmod +x /usr/bin/nosync && \
    nosync dnf update -y && \
    nosync dnf install -y \
        ca-certificates \
        ccache \
        gcc \
        git \
        glibc-langpack-en \
        libvirt-devel \
        pkgconfig \
        python3 \
        python3-devel \
        python3-lxml \
        python3-nose \
        python3-setuptools \
        rpm-build && \
    nosync dnf autoremove -y && \
    nosync dnf clean all -y && \
    rpm -qa | sort > /packages.txt && \
    mkdir -p /usr/libexec/ccache-wrappers && \
    ln -s /usr/bin/ccache /usr/libexec/ccache-wrappers/cc && \
    ln -s /usr/bin/ccache /usr/libexec/ccache-wrappers/$(basename /usr/bin/gcc)

ENV LANG "en_US.UTF-8"
ENV PYTHON "/usr/bin/python3"
ENV CCACHE_WRAPPERSDIR "/usr/libexec/ccache-wrappers"
