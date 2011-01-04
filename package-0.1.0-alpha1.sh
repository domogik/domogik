#!/bin/bash

REVISION=441ceeeef4c8
RELEASE=0.1.0-alpha1-$REVISION
SHORT_RELEASE=0.1.0-alpha1  # for base directory

ARCHIVE_NAME=domogik-temp
ARCHIVE=/tmp/$ARCHIVE_NAME.tgz
POST_PROCESSING=/tmp/domogik-post-$$
FINAL_ARCHIVE=/tmp/domogik-$SHORT_RELEASE.tgz

function generate_pkg() {
    echo "Generate package..."
    hg archive \
    -p domogik-$SHORT_RELEASE \
    -r $REVISION \
    -X re:package.*.sh \
    -X .hg_archival.txt  \
    -X .coverage  \
    -X .hgignore  \
    -X src/domogik/ui/xbmc/  \
    -X src/domogik/xpl/bin/datetimemgr.py  \
    -X src/domogik/xpl/bin/dawndusk.py  \
    -X src/domogik/xpl/bin/gagenda.py  \
    -X src/domogik/xpl/bin/knx.py  \
    -X src/domogik/xpl/bin/module_sample.py  \
    -X src/domogik/xpl/bin/tv_samsg.py  \
    -X src/domogik/xpl/bin/xbmc_not.py  \
    -X src/domogik/xpl/bin/yweather.py  \
    -X src/domogik/xpl/lib/dawndusk.py  \
    -X src/domogik/xpl/lib/gagenda.py  \
    -X src/domogik/xpl/lib/knx.py  \
    -X src/domogik/xpl/lib/tv_samsg.py  \
    -X src/domogik/xpl/lib/tv_samsg_led.py  \
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
    -X src/share/domogik/url2xpl/multimedia/  \
    -X src/tools/demo/ \
    -t tgz $ARCHIVE 

    if [ $? -ne 0 ] ; then
        echo "Error... exiting"
        exit 1
    fi
    echo "Package successfully created : $ARCHIVE"
}


function extract() {
    mkdir -p $POST_PROCESSING
    cd $POST_PROCESSING
    tar xzf $ARCHIVE
    if [ $? -ne 0 ] ; then
        echo "Error... exiting"
        exit 1
    fi
    echo "Package extracted in post processing path : $POST_PROCESSING"
}


function force_install_mode() {
    FILE=$POST_PROCESSING/domogik-$SHORT_RELEASE/install.sh
    sed -i "s/^.*Which install mode do you want.*$/MODE=install/" $FILE
    if [ $? -ne 0 ] ; then
        echo "Error... exiting"
        exit 1
    fi
    echo "Install.sh updated : force install mode"
}


function force_info_log_level() {
    FILE=$POST_PROCESSING/domogik-$SHORT_RELEASE/src/domogik/examples/config/domogik.cfg
    sed -i "s/^log_level *=.*$/log_level = info/" $FILE
    if [ $? -ne 0 ] ; then
        echo "Error... exiting"
        exit 1
    fi
    echo "domogik.cfg updated : force info log level"
}


function set_release_number() {
    FILE=$POST_PROCESSING/domogik-$SHORT_RELEASE/setup.py
    FILE2=$POST_PROCESSING/release
    sed -i "s/version = '.*',/version = '"$SHORT_RELEASE"',/" $FILE
    if [ $? -ne 0 ] ; then
        echo "Error... exiting"
        exit 1
    fi
    echo $SHORT_RELEASE > $FILE2
    if [ $? -ne 0 ] ; then
        echo "Error... exiting"
        exit 1
    fi
    echo "setup.py, release : release number updated"
}


function create_final_pkg() {
    cd $POST_PROCESSING/
    tar czf $FINAL_ARCHIVE *
    if [ $? -ne 0 ] ; then
        echo "Error... exiting"
        exit 1
    fi
    echo "Final package generated : $FINAL_ARCHIVE"
}


function clean() {
    rm -Rf $POST_PROCESSING
}

### main 
generate_pkg
extract
force_install_mode
force_info_log_level
set_release_number
create_final_pkg
clean
