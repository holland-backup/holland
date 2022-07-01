default: pylint
.PHONY: pylint_base pylint_plugins pylint
PROJDIR := $(realpath $(CURDIR))
PLUGINS = ${shell find $(PROJDIR)/plugins/ -maxdepth 1 -name "holland.*"  -print}


pylint_base:
	pylint holland || exit 1
	
pylint_plugins:
	for dir in $(PLUGINS) ; do echo $$dir; pylint $$dir/holland || exit 1; done

pylint: pylint_base pylint_plugins

