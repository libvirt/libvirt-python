# Shim wrapper around setup.py to allow for familiar build targets

PYTHON  ?= python
VERSION := $(shell $(PYTHON) -c 'import sys; print("{}{}".format(sys.version_info.major, sys.version_info.minor))')

all:
	$(PYTHON) -m build

install: all
	$(PYTHON) -m pip install .

clean:
	rm -rf build/ dist/

check: all
	tox -e py$(VERSION)

test: all
	tox

rpm: all
	rpmbuild -ta dist/libvirt-python-$(shell tr -d '\n' < VERSION).tar.gz
