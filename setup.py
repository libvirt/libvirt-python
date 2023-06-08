#!/usr/bin/env python3

import sys
import os
import re
import shutil
import subprocess
import time

from pathlib import Path
from setuptools import setup, Extension, Command
from setuptools.command.build_ext import build_ext
from setuptools.command.build_py import build_py
from setuptools.command.sdist import sdist


def check_pkgcfg():
    try:
        proc = subprocess.run(["pkg-config", "--version"],
                              stdout=subprocess.DEVNULL,
                              stderr=subprocess.DEVNULL)
        if proc.returncode != 0:
            print("pkg-config binary does not appear to be functional")
            sys.exit(1)
    except FileNotFoundError:
        print("pkg-config binary is required to compile libvirt-python")
        sys.exit(1)


def check_minimum_libvirt_version():
    subprocess.check_call(["pkg-config",
                           "--print-errors",
                           f"--atleast-version={MIN_LIBVIRT}",
                           "libvirt"])


def have_libvirt_lxc():
    proc = subprocess.run(["pkg-config",
                           f"--atleast-version={MIN_LIBVIRT_LXC}",
                           "libvirt"])
    if proc.returncode == 0:
        return True
    return False


def get_pkgconfig_data(args, mod, required=True):
    """Run pkg-config to and return content associated with it"""

    cmd = ["pkg-config"] + args + [f"{mod}"]
    with subprocess.Popen(cmd,
                          stdout=subprocess.PIPE,
                          stderr=subprocess.STDOUT,
                          universal_newlines=True) as p:

        line = p.stdout.readline()
        if line is None or line == "":
            if required:
                args_str = " ".join(args)
                raise Exception(f"Cannot determine '{args_str}' from "
                                "libvirt pkg-config file")
            line = ""
    return line.strip()


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
    c_modules = []
    py_modules = []
    ldflags = get_pkgconfig_data(["--libs-only-L"], "libvirt", False).split()
    cflags = get_pkgconfig_data(["--cflags"], "libvirt", False).split()

    module = Extension("libvirtmod",
                       sources=[
                            "libvirt-override.c",
                            "build/libvirt.c",
                            "typewrappers.c",
                            "libvirt-utils.c"
                       ],
                       libraries=["virt"],
                       include_dirs=["."])
    module.extra_compile_args.extend(cflags)
    module.extra_link_args.extend(ldflags)

    c_modules.append(module)
    py_modules.append("libvirt")

    moduleqemu = Extension("libvirtmod_qemu",
                           sources=[
                               "libvirt-qemu-override.c",
                               "build/libvirt-qemu.c",
                               "typewrappers.c",
                               "libvirt-utils.c"
                            ],
                           libraries=["virt-qemu", "virt"],
                           include_dirs=["."])
    moduleqemu.extra_compile_args.extend(cflags)
    moduleqemu.extra_link_args.extend(ldflags)

    c_modules.append(moduleqemu)
    py_modules.append("libvirt_qemu")

    if have_libvirt_lxc():
        modulelxc = Extension("libvirtmod_lxc",
                              sources=[
                                  "libvirt-lxc-override.c",
                                  "build/libvirt-lxc.c",
                                  "typewrappers.c",
                                  "libvirt-utils.c"
                              ],
                              libraries=["virt-lxc", "virt"],
                              include_dirs=["."])
        modulelxc.extra_compile_args.extend(cflags)
        modulelxc.extra_link_args.extend(ldflags)

        c_modules.append(modulelxc)
        py_modules.append("libvirt_lxc")

    py_modules.append("libvirtaio")

    return c_modules, py_modules


###################
# Custom commands #
###################

class my_build_ext(build_ext):

    def run(self):
        check_minimum_libvirt_version()
        apis = get_api_xml_files()

        subprocess.check_call([sys.executable, "generator.py", "libvirt", apis[0], "c"])
        subprocess.check_call([sys.executable, "generator.py", "libvirt-qemu", apis[1], "c"])
        if have_libvirt_lxc():
            subprocess.check_call([sys.executable, "generator.py", "libvirt-lxc", apis[2], "c"])

        build_ext.run(self)


class my_build_py(build_py):

    def run(self):
        check_minimum_libvirt_version()
        apis = get_api_xml_files()

        subprocess.check_call([sys.executable, "generator.py", "libvirt", apis[0], "py"])
        subprocess.check_call([sys.executable, "generator.py", "libvirt-qemu", apis[1], "py"])
        if have_libvirt_lxc():
            subprocess.check_call([sys.executable, "generator.py", "libvirt-lxc", apis[2], "py"])
        shutil.copy("libvirtaio.py", "build")

        build_py.run(self)


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

    @staticmethod
    def _gen_from_in(file_in, file_out, replace_pattern, replace):
        with open(file_in) as f_in, open(file_out, "w") as f_out:
            for line in f_in:
                f_out.write(line.replace(replace_pattern, replace))

    def gen_rpm_spec(self):
        return self._gen_from_in("libvirt-python.spec.in",
                                 "libvirt-python.spec",
                                 "@PY_VERSION@",
                                 self.distribution.get_version())

    def gen_authors(self):

        authors = []
        cmd = "git log --pretty=format:'%aN <%aE>'".split(" ")
        with subprocess.Popen(cmd,
                              stdout=subprocess.PIPE,
                              stderr=subprocess.DEVNULL,
                              universal_newlines=True) as p:
            for line in p.stdout:
                line = "   " + line.strip()
                if line not in authors:
                    authors.append(line)

        authors.sort(key=str.lower)
        self._gen_from_in("AUTHORS.in",
                          "AUTHORS",
                          "@AUTHORS@",
                          "\n".join(authors))

    def gen_changelog(self):
        cmd = "git log '--pretty=format:%H:%ct %an <%ae>%n%n%s%n%b%n'".split(" ")
        with open("ChangeLog", "w") as f_out, \
             subprocess.Popen(cmd,
                              stdout=subprocess.PIPE,
                              stderr=subprocess.DEVNULL,
                              universal_newlines=True) as p:
            for line in p.stdout:
                m = re.match(r"([a-f0-9]+):(\d+)\s(.*)", line)
                if m:
                    t = time.gmtime(int(m.group(2)))
                    fmt = "{: 04d}-{: 02d}-{: 02d} {}\n"
                    f_out.write(fmt.format(t.tm_year, t.tm_mon, t.tm_mday, m.group(3)))
                else:
                    if re.match(r"Signed-off-by", line):
                        continue
                    f_out.write("    " + line.strip() + "\n")

    def run(self):
        Path("build").mkdir(exist_ok=True)

        if Path(".git").exists():
            try:
                self.gen_rpm_spec()
                self.gen_authors()
                self.gen_changelog()

                sdist.run(self)

            finally:
                files = [
                    "libvirt-python.spec",
                    "AUTHORS",
                    "ChangeLog"
                ]
                for f in files:
                    try:
                        Path(f).unlink()
                    except FileNotFoundError:
                        pass
        else:
            sdist.run(self)


class my_test(Command):
    user_options = [
        ("build-base=", "b",
         "base directory for build library"),
        ("build-platlib=", None,
         "build directory for platform-specific distributions"),
        ("plat-name=", "p",
         "platform name to build for, if supported "),
    ]

    description = "Run test suite."

    def find_build_dir(self):
        if self.plat_name is not None:
            plat_specifier = f".{self.plat_name}-{sys.version_info[0]}.{sys.version_info[1]}"

            if hasattr(sys, "gettotalrefcount"):
                plat_specifier += "-pydebug"

            return Path(self.build_base, "lib" + plat_specifier).as_posix()
        else:
            dirs = [p.as_posix() for p in Path(self.build_base).glob("lib.*")]
            if len(dirs) == 0:
                print("No build directory found, run 'setup.py build'")
                sys.exit(1)
            if len(dirs) > 1:
                print("Multiple build dirs found, use --plat-name option")
                sys.exit(1)
            return dirs[0]

    def initialize_options(self):
        self.build_base = "build"
        self.build_platlib = None
        self.plat_name = None

    def finalize_options(self):
        if self.build_platlib is None:
            self.build_platlib = self.find_build_dir()

    def find_pytest_path(self):
        binaries = [
            f"pytest-{sys.version_info[0]}.{sys.version_info[1]}",
            f"pytest-{sys.version_info[0]}",
            f"pytest{sys.version_info[0]}",
            "pytest",
        ]

        for binary in binaries:
            path = shutil.which(binary)
            if path is not None:
                return path

        raise Exception("Cannot find any pytest binary")

    def run(self):
        """
        Run test suite
        """

        if "PYTHONPATH" in os.environ:
            os.environ["PYTHONPATH"] = self.build_platlib + ":" + os.environ["PYTHONPATH"]
        else:
            os.environ["PYTHONPATH"] = self.build_platlib

        pytest = self.find_pytest_path()
        subprocess.check_call([pytest, "tests"])


class my_clean(Command):
    user_options = [
        ("all", None, "unused, compatibility with distutils")
    ]

    def initialize_options(self):
        self.all = False

    def finalize_options(self):
        pass

    def run(self):
        if os.path.exists("build"):
            shutil.rmtree("build", ignore_errors=True)


##################
# Invoke setup() #
##################

if sys.version_info < (3, 6):
    print("libvirt-python requires Python >= 3.6 to build")
    sys.exit(1)

MIN_LIBVIRT = "0.9.11"
MIN_LIBVIRT_LXC = "1.0.2"

# Hack to stop "pip install" failing with error
# about missing "build" dir.
if not os.path.exists("build"):
    os.mkdir("build")

check_pkgcfg()

_c_modules, _py_modules = get_module_lists()

setup(name="libvirt-python",
      version="9.5.0",
      url="http://www.libvirt.org",
      maintainer="Libvirt Maintainers",
      maintainer_email="libvir-list@redhat.com",
      description="The libvirt virtualization API python binding",
      long_description=
        """The libvirt-python package provides a module that permits applications
written in the Python 3.x programming language to call the interface
supplied by the libvirt library, to manage the virtualization capabilities
of recent versions of Linux (and other OSes).""",
      license="LGPLv2+",
      ext_modules=_c_modules,
      py_modules=_py_modules,
      package_dir={
          "": "build"
      },
      cmdclass={
          "build_ext": my_build_ext,
          "build_py": my_build_py,
          "clean": my_clean,
          "sdist": my_sdist,
          "test": my_test
      },
      classifiers=[
          "Development Status :: 5 - Production/Stable",
          "Intended Audience :: Developers",
          "License :: OSI Approved :: GNU Lesser General Public License v2 or later (LGPLv2+)",
          "Programming Language :: Python :: 3",
      ]
)
