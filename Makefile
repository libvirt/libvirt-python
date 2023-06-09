# Shim wrapper around setup.py to allow for familiar build targets

PYTHON ?= python

all:
	$(PYTHON) -m build

install: all
	$(PYTHON) -m pip install .

clean:
	rm -rf build/ dist/

check: all
	tox -e py36

test: all
	tox

rpm: all
	rpmbuild -ta dist/libvirt-python-$(shell tr -d '\n' < VERSION).tar.gz
