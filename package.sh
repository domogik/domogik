#!/bin/bash

if [[ $# -lt 1 ]] ; then
    echo "Usage : "$(basename $0)" <'tip' or revision number> [version name]"
    echo "Example :"
    echo "$(basename $0) tip 0.2.0-alpha1"
    exit 1
else
    case $1 in
        "tip")
            REVISION=$(hg log -r tip --template '{node|short}')
            SHORT_RELEASE=$REVISION-tip
            ;;
        *)
            set +e
            OK=$(hg log -r $1 >/dev/null 2>&1; echo $?)
            set -e
            #echo $OK
            if [[ $OK -eq 0 ]] ; then
                REVISION=$1
                SHORT_RELEASE=$REVISION
            else
                echo "Bad usage. C'ant find revision $1"
                exit 1
            fi
    esac
    if [[ $# -eq 2 ]] ; then
        SHORT_RELEASE=$2
    fi
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
    -X dists/  \
    -X src/domogik/ui/  \
    -X src/domogik_packages/ \
    -X src/external/ \
    -X src/mpris/ \
    -X src/share/ \
    -X src/tools/demo/ \
    -X src/tools/drm/ \
    -X src/tools/drm-yii/ \
    -X src/tools/ipx800/ \
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
