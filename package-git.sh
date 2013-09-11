#!/bin/bash

if [[ $# -lt 2 ]] ; then
    echo "Usage : "$(basename $0)" <branch or tag name> <package version>"
    echo "Example :"
    echo "$(basename $0) 0.3 0.3"
    exit 1
fi

BRANCH=$1
RELEASE=$2

ARCHIVE_NAME=domogik-temp
ARCHIVE=/tmp/$ARCHIVE_NAME.tgz
POST_PROCESSING=/tmp/domogik-post-$$
FINAL_ARCHIVE=/tmp/domogik-$RELEASE.tgz

function generate_pkg() {
    echo "Generate package..."
    git archive $BRANCH \
    --prefix domogik-$RELEASE/ \
    --worktree-attributes \
    --format tgz \
    --output $ARCHIVE \
    .
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
    FILE=$POST_PROCESSING/domogik-$RELEASE/install.sh
    sed -i "s/^.*Which install mode do you want.*$/MODE=install/" $FILE
    if [ $? -ne 0 ] ; then
        echo "Error... exiting"
        exit 1
    fi
    echo "Install.sh updated : force install mode"
}


function force_info_log_level() {
    FILE=$POST_PROCESSING/domogik-$RELEASE/src/domogik/examples/config/domogik.cfg
    sed -i "s/^log_level *=.*$/log_level = info/" $FILE
    if [ $? -ne 0 ] ; then
        echo "Error... exiting"
        exit 1
    fi
    echo "domogik.cfg updated : force info log level"
}


function set_release_number() {
    FILE=$POST_PROCESSING/domogik-$RELEASE/setup.py
    FILE2=$POST_PROCESSING/domogik-$RELEASE/release
    sed -i "s/version = '.*',/version = '"$RELEASE"',/" $FILE
    if [ $? -ne 0 ] ; then
        echo "Error... exiting"
        exit 1
    fi
    echo $RELEASE > $FILE2
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
