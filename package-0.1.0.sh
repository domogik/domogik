#!/bin/bash

ARCHIVE=/tmp/domogik-release.tgz

echo "Generate package..."
#hg archive -X .hg_archival.txt -X .coverage -X .hgignore -X src/domogik/ui/work/web/ -X src/domogik/ui/xbmc/ -X src/domogik/xpl/bin/datetimemgr.py -X src/domogik/xpl/bin/dawndusk.py -X src/domogik/xpl/bin/gagenda.py -X src/domogik/xpl/bin/module_sample.py -X src/domogik/xpl/bin/xbmc_not.py -X src/domogik/xpl/lib/dawndusk.py -X src/domogik/xpl/lib/gagenda.py -X src/domogik/xpl/lib/xbmc_not.py -X src/domogik/xpl/mocks/ -X src/mpris/ -X src/share/domogik/plugins/gagenda.xml -X src/share/domogik/plugins/xbmc_not.xml -t tgz $ARCHIVE



hg archive \
-X .hg_archival.txt  \
-X .coverage  \
-X .hgignore  \
-X src/domogik/ui/xbmc/  \
-X src/domogik/xpl/bin/datetimemgr.py  \
-X src/domogik/xpl/bin/dawndusk.py  \
-X src/domogik/xpl/bin/gagenda.py  \
-X src/domogik/xpl/bin/knx.py  \
-X src/domogik/xpl/bin/module_sample.py  \
-X src/domogik/xpl/bin/tv_samsung.py  \
-X src/domogik/xpl/bin/xbmc_not.py  \
-X src/domogik/xpl/bin/yweather.py  \
-X src/domogik/xpl/lib/dawndusk.py  \
-X src/domogik/xpl/lib/gagenda.py  \
-X src/domogik/xpl/lib/knx.py  \
-X src/domogik/xpl/lib/tv_samsung.py  \
-X src/domogik/xpl/lib/tv_samsung_led.py  \
-X src/domogik/xpl/lib/xbmc_not.py  \
-X src/domogik/xpl/lib/yweather.py  \
-X src/domogik/xpl/mocks/  \
-X src/mpris/README.txt  \
-X src/mpris/XPLSCHEMA  \
-X src/mpris/__init__.py  \
-X src/mpris/controlers/GenericController.py  \
-X src/mpris/controlers/MPD.py  \
-X src/mpris/mprisMPD.py  \
-X src/mpris/xPLmpris.py  \
-X src/share/domogik/plugins/datetimemgr.xml  \
-X src/share/domogik/plugins/gagenda.xml  \
-X src/share/domogik/plugins/knx.xml  \
-X src/share/domogik/plugins/tv_samsung.xml  \
-X src/share/domogik/plugins/xbmc_not.xml  \
-X src/share/domogik/plugins/yweather.xml  \
-X src/share/domogik/scenarios/  \
-X src/share/domogik/stats/notification/notify.basic.xml  \
-X src/share/domogik/stats/online_service/sensor.basic-yweather.xml  \
-X src/share/domogik/stats/sample_databasemanager.xml  \
-X src/share/domogik/url2xpl/multimedia/channel_up.xml  \
-X src/tools/demo/ \
-t tgz $ARCHIVE 

if [ $? -ne 0 ] ; then
    echo "Error... exiting"
    exit 1
fi
echo "Package successfully created : $ARCHIVE"
