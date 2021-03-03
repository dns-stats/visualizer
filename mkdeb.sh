#!/bin/sh
#
# Make Debian package in subdir dist_deb.
#
# Requires VERSION set in environment.

rm -rf dist_deb

# Copy source tree into dist_deb/dsv-packages
#
# First the directories copied in toto.
mkdir -p dist_deb/dsv-packages
cp -pR bin doc etc sql src sampledata dist_deb/dsv-packages

# All Grafana dashboard JSON and Grafana provisioning.
find grafana/dashboards -name "*.json" | xargs tar -cf - | tar -C dist_deb/dsv-packages -xf -
cp -pR grafana/provisioning dist_deb/dsv-packages

# Now the Grafana bar chart. This needs to go into Grafana plugins.
mkdir -p dist_deb/dsv-packages/grafana/plugins/natel-plotly-panel
(cd tools/natel-plotly-panel; git archive HEAD) | tar -C dist_deb/dsv-packages/grafana/plugins/natel-plotly-panel -xf -

# The Python ClickHouse driver.
mkdir -p dist_deb/dsv-packages/tools/clickhouse-driver
(cd tools/clickhouse-driver; git archive HEAD) | tar -C dist_deb/dsv-packages/tools/clickhouse-driver -xf -

# Remove any Python cache dirs.
find dist_deb/dsv-packages -name __pycache__ -type d | xargs rm -rf

# Make the source tarball.
tar -c -z -f dist_deb/dns-stats-visualizer_${DSVVERSION}.orig.tar.gz -C dist_deb/dsv-packages bin doc etc grafana provisioning sql src sampledata tools

# Copy the debian dir into the build dir and make the packages.
cp -pR debian dist_deb/dsv-packages
cd dist_deb/dsv-packages
exec dpkg-buildpackage -us -uc
