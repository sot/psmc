# Set the task name
TASK = psmc
# Version
VER = 0.02


# Uncomment the correct choice indicating either SKA or TST flight environment
FLIGHT_ENV = SKA

BIN = psmc_check
SHARE = psmc_check.py psmc_calibrate.py twodof.py characteristics.py VERSION
DATA = index_template.rst psmc_check.css fit_resid.png fit_resid_hist.png \
       fit_resid_vs_temp.png fit_pitch_simpos.png psmc_calibrate.log VERSION
DOC = docs/_build/html

include /proj/sot/ska/include/Makefile.FLIGHT

.PHONY: dist install docs version

# Make a versioned distribution.  Could also use an EXCLUDE_MANIFEST
dist: version
	mkdir $(TASK)-$(VER)
	tar --exclude CVS --exclude "*~" --create --files-from=MANIFEST --file - \
	 | (tar --extract --directory $(TASK)-$(VER) --file - )
	tar --create --verbose --gzip --file $(TASK)-$(VER).tar.gz $(TASK)-$(VER)
	rm -rf $(TASK)-$(VER)

docs:
	cd docs ; \
	make html

version:
	rm -f VER
	echo "$(VER)" > VERSION

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

