default: pylint
.PHONY: pylint_base pylint_plugins pylint
PROJDIR := $(realpath $(CURDIR))
PLUGINS = ${shell find $(PROJDIR)/plugins/ -maxdepth 1 -name "holland.*"  -print}


pylint_base:
	pylint --rcfile=.pylintrc --recursive=y holland || exit 1
	
pylint_plugins:
	for dir in $(PLUGINS) ; do echo $$dir; pylint --rcfile=.pylintrc --recursive=y $$dir/holland || exit 1; done

pylint: pylint_base pylint_plugins

