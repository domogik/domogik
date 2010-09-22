#!/bin/bash

ARCHIVE=/tmp/domogik-release.tgz

echo "Generate package..."
hg archive -X .hg_archival.txt -X .coverage -X .hgignore -X src/domogik/ui/work/web/ -X src/domogik/ui/xbmc/ -X src/domogik/xpl/bin/datetimemgr.py -X src/domogik/xpl/bin/dawndusk.py -X src/domogik/xpl/bin/gagenda.py -X src/domogik/xpl/bin/module_sample.py -X src/domogik/xpl/bin/xbmc_not.py -X src/domogik/xpl/lib/dawndusk.py -X src/domogik/xpl/lib/gagenda.py -X src/domogik/xpl/lib/xbmc_not.py -X src/domogik/xpl/mocks/ -X src/mpris/ -X src/share/domogik/plugins/gagenda.xml -X src/share/domogik/plugins/xbmc_not.xml -t tgz $ARCHIVE

if [ $? -ne 0 ] ; then
    echo "Error... exiting"
    exit 1
fi
echo "Package successfully created"
