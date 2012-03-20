#!/bin/bash

if [[ $# -eq 0 ]] ; then
    REVISION=a32a4824492a
    SHORT_RELEASE=0.1.0-alpha3
else
    case $1 in
        "tip")
            REVISION=$(hg log -r tip --template '{node|short}')
            SHORT_RELEASE=tip-$REVISION
            ;;
        *)
            echo "Bad usage. Exiting..."
            exit 1
    esac
fi

ARCHIVE_NAME=domogik-temp
ARCHIVE=/tmp/$ARCHIVE_NAME.tgz
POST_PROCESSING=/tmp/domogik-post-$$
FINAL_ARCHIVE=/tmp/domogik-$SHORT_RELEASE.tgz

function generate_pkg() {
    echo "Generate package..."
    hg archive \
    -p domogik-$SHORT_RELEASE \
    -r $REVISION \
    -I . \
    -X re:package.*.sh \
    -X .hg_archival.txt  \
    -X .coverage  \
    -X .hgignore  \
    -X src/domogik/ui/  \
    -X src/domogik/xpl/bin/ \
    -X src/domogik/xpl/lib/ \
    -X src/domogik/xpl/helpers/ \
    -X src/domogik/xpl/mocks/  \
    -X src/external/ \
    -X src/mpris/ \
    -X src/share/ \
    -X src/tools/demo/ \
    -X src/tools/drm/ \
    -X src/tools/drm-yii/ \
    -X src/tools/ipx800/ \
    -I src/domogik/xpl/__init__.py \
    -I src/domogik/xpl/bin/__init__.py \
    -I src/domogik/xpl/bin/dbmgr.py \
    -I src/domogik/xpl/bin/dump_xpl.py \
    -I src/domogik/xpl/bin/manager.py \
    -I src/domogik/xpl/bin/pkgmgr.py \
    -I src/domogik/xpl/bin/rest.py \
    -I src/domogik/xpl/bin/send.py \
    -I src/domogik/xpl/bin/version.py \
    -I src/domogik/xpl/helpers/__init__.py \
    -I src/domogik/xpl/lib/__init__.py \
    -I src/domogik/xpl/lib/rest \
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
    FILE2=$POST_PROCESSING/domogik-$SHORT_RELEASE/release
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
