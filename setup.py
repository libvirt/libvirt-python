#!/usr/bin/env python

from distutils.core import setup, Extension, Command
from distutils.command.build import build
from distutils.command.clean import clean
from distutils.command.sdist import sdist
from distutils.dir_util import remove_tree
from distutils.util import get_platform
from distutils.spawn import spawn
from distutils.errors import DistutilsExecError
import distutils

import sys
import os
import os.path
import re
import shutil
import time

MIN_LIBVIRT = "0.9.11"
MIN_LIBVIRT_LXC = "1.0.2"

# Hack to stop 'pip install' failing with error
# about missing 'build' dir.
if not os.path.exists("build"):
    os.mkdir("build")

_pkgcfg = -1
def get_pkgcfg(do_fail=True):
    global _pkgcfg
    if _pkgcfg == -1:
        _pkgcfg = os.getenv('PKG_CONFIG')
    if _pkgcfg is None:
        _pkgcfg = distutils.spawn.find_executable("pkg-config")
    if _pkgcfg is None and do_fail:
        raise Exception("pkg-config binary is required to compile libvirt-python")
    return _pkgcfg

def check_minimum_libvirt_version():
    spawn([get_pkgcfg(),
           "--print-errors",
           "--atleast-version=%s" % MIN_LIBVIRT,
           "libvirt"])

def have_libvirt_lxc():
    try:
        spawn([get_pkgcfg(),
               "--atleast-version=%s" % MIN_LIBVIRT_LXC,
             "libvirt"])
        return True
    except DistutilsExecError:
        return False

def have_libvirtaio():
    # This depends on asyncio, which in turn depends on "yield from" syntax.
    # The asyncio module itself is in standard library since 3.4, but there is
    # an out-of-tree version compatible with 3.3.
    return sys.version_info >= (3, 3)

def get_pkgconfig_data(args, mod, required=True):
    """Run pkg-config to and return content associated with it"""
    f = os.popen("%s %s %s" % (get_pkgcfg(), " ".join(args), mod))

    line = f.readline()
    if line is not None:
        line = line.strip()

    if line is None or line == "":
        if required:
            raise Exception("Cannot determine '%s' from libvirt pkg-config file" % " ".join(args))
        else:
            return ""

    return line

def get_api_xml_files():
    """Check with pkg-config that libvirt is present and extract
    the API XML file paths we need from it"""

    libvirt_api = get_pkgconfig_data(["--variable", "libvirt_api"], "libvirt")

    offset = libvirt_api.index("-api.xml")
    libvirt_qemu_api = libvirt_api[0:offset] + "-qemu-api.xml"

    offset = libvirt_api.index("-api.xml")
    libvirt_lxc_api = libvirt_api[0:offset] + "-lxc-api.xml"

    return (libvirt_api, libvirt_qemu_api, libvirt_lxc_api)

def get_module_lists():
    """
    Determine which modules we are actually building, and all their
    required config
    """
    if get_pkgcfg(do_fail=False) is None:
        return [], []

    c_modules = []
    py_modules = []
    ldflags = get_pkgconfig_data(["--libs-only-L"], "libvirt", False).split()
    cflags = get_pkgconfig_data(["--cflags"], "libvirt", False).split()

    module = Extension('libvirtmod',
                       sources = ['libvirt-override.c', 'build/libvirt.c', 'typewrappers.c', 'libvirt-utils.c'],
                       libraries = [ "virt" ],
                       include_dirs = [ "." ])
    module.extra_compile_args.extend(cflags)
    module.extra_link_args.extend(ldflags)

    c_modules.append(module)
    py_modules.append("libvirt")

    moduleqemu = Extension('libvirtmod_qemu',
                           sources = ['libvirt-qemu-override.c', 'build/libvirt-qemu.c', 'typewrappers.c', 'libvirt-utils.c'],
                           libraries = [ "virt-qemu" ],
                           include_dirs = [ "." ])
    moduleqemu.extra_compile_args.extend(cflags)
    moduleqemu.extra_link_args.extend(ldflags)

    c_modules.append(moduleqemu)
    py_modules.append("libvirt_qemu")

    if have_libvirt_lxc():
        modulelxc = Extension('libvirtmod_lxc',
                              sources = ['libvirt-lxc-override.c', 'build/libvirt-lxc.c', 'typewrappers.c', 'libvirt-utils.c'],
                              libraries = [ "virt-lxc" ],
                              include_dirs = [ "." ])
        modulelxc.extra_compile_args.extend(cflags)
        modulelxc.extra_link_args.extend(ldflags)

        c_modules.append(modulelxc)
        py_modules.append("libvirt_lxc")

    if have_libvirtaio():
        py_modules.append("libvirtaio")

    return c_modules, py_modules


###################
# Custom commands #
###################

class my_build(build):

    def run(self):
        check_minimum_libvirt_version()
        apis = get_api_xml_files()

        self.spawn([sys.executable, "generator.py", "libvirt", apis[0]])
        self.spawn([sys.executable, "generator.py", "libvirt-qemu", apis[1]])
        if have_libvirt_lxc():
            self.spawn([sys.executable, "generator.py", "libvirt-lxc", apis[2]])
        if have_libvirtaio():
            shutil.copy('libvirtaio.py', 'build')

        build.run(self)

class my_sdist(sdist):
    user_options = sdist.user_options

    description = "Update libvirt-python.spec; build sdist-tarball."

    def initialize_options(self):
        self.snapshot = None
        sdist.initialize_options(self)

    def finalize_options(self):
        if self.snapshot is not None:
            self.snapshot = 1
        sdist.finalize_options(self)

    def gen_rpm_spec(self):
        f1 = open('libvirt-python.spec.in', 'r')
        f2 = open('libvirt-python.spec', 'w')
        for line in f1:
            f2.write(line
                     .replace('@PY_VERSION@', self.distribution.get_version()))
        f1.close()
        f2.close()

    def gen_authors(self):
        f = os.popen("git log --pretty=format:'%aN <%aE>'")
        authors = []
        for line in f:
            line = "   " + line.strip()
            if line not in authors:
                authors.append(line)

        authors.sort(key=str.lower)

        f1 = open('AUTHORS.in', 'r')
        f2 = open('AUTHORS', 'w')
        for line in f1:
            f2.write(line.replace('@AUTHORS@', "\n".join(authors)))
        f1.close()
        f2.close()


    def gen_changelog(self):
        f1 = os.popen("git log '--pretty=format:%H:%ct %an  <%ae>%n%n%s%n%b%n'")
        f2 = open("ChangeLog", 'w')

        for line in f1:
            m = re.match(r'([a-f0-9]+):(\d+)\s(.*)', line)
            if m:
                t = time.gmtime(int(m.group(2)))
                f2.write("%04d-%02d-%02d %s\n" % (t.tm_year, t.tm_mon, t.tm_mday, m.group(3)))
            else:
                if re.match(r'Signed-off-by', line):
                    continue
                f2.write("    " + line.strip() + "\n")

        f1.close()
        f2.close()


    def run(self):
        if not os.path.exists("build"):
            os.mkdir("build")

        if os.path.exists(".git"):
            try:
                self.gen_rpm_spec()
                self.gen_authors()
                self.gen_changelog()

                sdist.run(self)

            finally:
                files = ["libvirt-python.spec",
                         "AUTHORS",
                         "ChangeLog"]
                for f in files:
                    if os.path.exists(f):
                        os.unlink(f)
        else:
            sdist.run(self)

class my_rpm(Command):
    user_options = []

    description = "Build src and noarch rpms."

    def initialize_options(self):
        pass

    def finalize_options(self):
        pass

    def run(self):
        """
        Run sdist, then 'rpmbuild' the tar.gz
        """

        self.run_command('sdist')
        self.spawn(["/usr/bin/rpmbuild", "-ta", "--clean",
            "dist/libvirt-python-%s.tar.gz" % self.distribution.get_version()])

class my_test(Command):
    user_options = [
        ('build-base=', 'b',
         "base directory for build library"),
        ('build-platlib=', None,
         "build directory for platform-specific distributions"),
        ('plat-name=', 'p',
         "platform name to build for, if supported "
         "(default: %s)" % get_platform()),
    ]

    description = "Run test suite."

    def initialize_options(self):
        self.build_base = 'build'
        self.build_platlib = None
        self.plat_name = None

    def finalize_options(self):
        if self.plat_name is None:
            self.plat_name = get_platform()

        plat_specifier = ".%s-%s" % (self.plat_name, sys.version[0:3])

        if hasattr(sys, 'gettotalrefcount'):
            plat_specifier += '-pydebug'

        if self.build_platlib is None:
            self.build_platlib = os.path.join(self.build_base,
                                              'lib' + plat_specifier)

    def find_nosetests_path(self):
        binaries = [
            "nosetests-%d.%d" % (sys.version_info[0],
                                 sys.version_info[1]),
            "nosetests-%d" % (sys.version_info[0]),
            "nosetests",
        ]

        for binary in binaries:
            path = distutils.spawn.find_executable(binary)
            if path is not None:
                return path

        raise Exception("Cannot find any nosetests binary")

    def run(self):
        """
        Run test suite
        """

        apis = get_api_xml_files()

        if "PYTHONPATH" in os.environ:
            os.environ["PYTHONPATH"] = self.build_platlib + ":" + os.environ["PYTHONPATH"]
        else:
            os.environ["PYTHONPATH"] = self.build_platlib
        self.spawn([sys.executable, "sanitytest.py", self.build_platlib, apis[0]])
        nose = self.find_nosetests_path()
        self.spawn([sys.executable, nose])


class my_clean(clean):
    def run(self):
        clean.run(self)

        if os.path.exists("build"):
            remove_tree("build")


##################
# Invoke setup() #
##################

_c_modules, _py_modules = get_module_lists()

setup(name = 'libvirt-python',
      version = '4.1.0',
      url = 'http://www.libvirt.org',
      maintainer = 'Libvirt Maintainers',
      maintainer_email = 'libvir-list@redhat.com',
      description = 'The libvirt virtualization API python binding',
      long_description =
        '''The libvirt-python package provides a module that permits applications
written in the Python programming language to call the interface
supplied by the libvirt library, to manage the virtualization capabilities
of recent versions of Linux (and other OSes).''',
      license = 'LGPLv2+',
      ext_modules = _c_modules,
      py_modules = _py_modules,
      package_dir = {
          '': 'build'
      },
      cmdclass = {
          'build': my_build,
          'clean': my_clean,
          'sdist': my_sdist,
          'rpm': my_rpm,
          'test': my_test
      },
      classifiers = [
          "Development Status :: 5 - Production/Stable",
          "Intended Audience :: Developers",
          "License :: OSI Approved :: GNU Lesser General Public License v2 or later (LGPLv2+)",
          "Programming Language :: Python",
          "Programming Language :: Python :: 2",
          "Programming Language :: Python :: 3",
      ]
)
