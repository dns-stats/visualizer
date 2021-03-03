.PHONY: clean test

# Putting the command straight into $(shell) gives 'missing ')'' error.
# This two-stage process works.
VERCMD := sed -e "s/.*(\([0-9][0-9.~rc]*\).*/\1/;q" debian/changelog
DSVVERSION := $(shell $(VERCMD))

MAN1=$(patsubst %.adoc,%.1, $(wildcard doc/man/man1/*.adoc))
MAN5=$(patsubst %.adoc,%.5, $(wildcard doc/man/man5/*.adoc))
MANS=$(MAN1) $(MAN5)
MANDOCS=$(MAN1:.1=.html) $(MAN5:.5=.html)
MANPDFS=$(MANDOCS:.html=.pdf)

DOCS=$(patsubst %.adoc,%.html, \
     $(wildcard doc/user/*.adoc doc/*.adoc) README.adoc)
DOCPDFS=$(DOCS:.html=.pdf)

JSON=$(patsubst %.dashboard.py,%.dashboard.json,$(wildcard \
        grafana/dashboards/main-site/*/*.dashboard.py))
JSONDEPS=$(JSON:.json=.d)

all: $(MANS) $(MANDOCS) $(DOCS) $(JSON)

%.1 :: %.adoc ; asciidoctor -b manpage -d manpage -o $@ $<

%.5 :: %.adoc ; asciidoctor -b manpage -d manpage -o $@ $<

%.html :: %.adoc ; asciidoctor -b html5 -d article -a dsvversion=$(DSVVERSION) -o $@ $<

%.pdf :: %.adoc ; asciidoctor-pdf -b pdf -d article -a dsvversion=$(DSVVERSION) -o $@ $<

%.dashboard.json :: %.dashboard.py ; DSVVERSION=$(DSVVERSION) grafana/bin/generate-dashboard -o $@ $<

%.dashboard.d :: %.dashboard.py ; grafana/bin/dash-depends $< > $@

doc: $(MANS) $(MANDOCS) $(DOCS)

pdf: $(MANPDFS) $(DOCPDFS)

json: $(JSON)

clean: ; rm -rf $(MANS) $(MANDOCS) $(DOCS) $(MANPDFS) $(DOCPDFS) $(JSON) dist_deb

distclean: clean ; rm -f $(JSONDEPS)

test:
	PYTHONPATH=src/python3 python3 -m unittest discover -s tests/python3/integration/

pylint:
	`command -v pylint3 2> /dev/null || echo "pylint"` --rcfile=src/python3/dsv.pylintrc src/python3/dsv

deb: $(MANS) $(DOCS) $(JSON) test
	DSVVERSION=$(DSVVERSION) ./mkdeb.sh

include $(JSONDEPS)

doc/Overview_and_Basic_Install.html: $(wildcard doc/adoc-source/*.adoc)
doc/Overview_and_Basic_Install.pdf: $(wildcard doc/adoc-source/*.adoc)
doc/Advanced_User_Guide.html: $(wildcard doc/adoc-source/*.adoc)
doc/Advanced_User_Guide.pdf: $(wildcard doc/adoc-source/*.adoc)
