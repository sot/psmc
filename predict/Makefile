# Set the task name
TASK = psmc
VERSI0N = 0.01

# Uncomment the correct choice indicating either SKA or TST flight environment
FLIGHT_ENV = SKA

BIN = psmc_check
SHARE = psmc_check.py psmc_calibrate.py twodof.py characteristics.py
DATA = index_template.rst psmc_check.css
DOC = docs/_build/html

include /proj/sot/ska/include/Makefile.FLIGHT

.PHONY: dist install docs

# Make a versioned distribution.  Could also use an EXCLUDE_MANIFEST
dist:
	mkdir $(NAME)-$(VERSION)
	tar --exclude CVS --exclude "*~" --create --files-from=MANIFEST --file - \
	 | (tar --extract --directory $(NAME)-$(VERSION) --file - )
	tar --create --verbose --gzip --file $(NAME)-$(VERSION).tar.gz $(NAME)-$(VERSION)
	rm -rf $(NAME)-$(VERSION)

docs:
	cd docs ; \
	make html

install:
#  Uncomment the lines which apply for this task
	mkdir -p $(INSTALL_BIN)
	mkdir -p $(INSTALL_SHARE)
	mkdir -p $(INSTALL_DATA)
	mkdir -p $(INSTALL_DOC)

	rsync --times --cvs-exclude $(BIN) $(INSTALL_BIN)/
	rsync --times --cvs-exclude $(SHARE) $(INSTALL_SHARE)/
	rsync --times --cvs-exclude $(DATA) $(INSTALL_DATA)/
	rsync --archive --times --cvs-exclude $(DOC)/ $(INSTALL_DOC)/

