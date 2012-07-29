#!/bin/bash
#
# Initiate a package documentation from the template
#
# Parameters: $1 : type of the package
#             $2 : name of the package

function usage(){
    echo "Usage : $(basename $0) <type of the package> <name of the package>"
}

# check parameters
[[ $# -ne 2 ]] && usage && exit 1
[ $1 != "plugin" -a $1 != "package" ] && usage && exit 2


# set variables
PKG_TYPE=$1
PKG_NAME=$2
TPL_DIR=$(dirname $0)
DOC_DIR=$(dirname $0)/../
NEW_DOC=$DOC_DIR/$PKG_TYPE/$PKG_NAME

# Start logs
echo "Creating template for the $PKG_TYPE $PKG_NAME..."

# check if target doesn't exists
echo "Check if the documentation doesn't already exists..."
[ -d $NEW_DOC ] && echo "ERROR : the documentation already exists for the $PKG_TYPE $PKG_NAME. Exiting." && exit 3
echo "OK"

# copy the template
echo "Copy the template..."
cp -R $TPL_DIR $NEW_DOC
[ $? -ne 0 ] && echo "ERROR : error during copy. Exiting" && exit 4
echo "OK"

# Update the new doc : conf.py
echo "Update conf.py..."
sed -i "s/__PKG_TYPE__/$PKG_TYPE/g" $NEW_DOC/conf.py
[ $? -ne 0 ] && echo "ERROR : error update. Exiting" && exit 5
sed -i "s/__PKG_NAME__/$PKG_NAME/g" $NEW_DOC/conf.py
[ $? -ne 0 ] && echo "ERROR : error update. Exiting" && exit 6
echo "OK"

# Update the new doc : contents.txt
echo "Update contents.txt..."
sed -i "s/__PKG_NAME__/$PKG_NAME/g" $NEW_DOC/contents.txt
[ $? -ne 0 ] && echo "ERROR : error update. Exiting" && exit 7
echo "OK"

# Update the new doc : helpers.txt
echo "Update helpers.txt..."
sed -i "s/__PKG_NAME__/$PKG_NAME/g" $NEW_DOC/helpers.txt
[ $? -ne 0 ] && echo "ERROR : error update. Exiting" && exit 8
echo "OK"

# Update the new doc : index.txt
echo "Update contents.txt..."
sed -i "s/__PKG_NAME__/$PKG_NAME/g" $NEW_DOC/index.txt
[ $? -ne 0 ] && echo "ERROR : error update. Exiting" && exit 9
echo "OK"

# Update the new doc : main file
echo "Update the main file..."
sed -i "s/__PKG_NAME__/$PKG_NAME/g" $NEW_DOC/__PKG_NAME__.txt
[ $? -ne 0 ] && echo "ERROR : error update. Exiting" && exit 10
mv $NEW_DOC/__PKG_NAME__.txt $NEW_DOC/$PKG_NAME.txt
[ $? -ne 0 ] && echo "ERROR : error while creating the file $PKG_NAME.txt. Exiting" && exit 11
echo "OK"

# End
echo ""
echo "The documentation for the $PKG_TYPE $PKG_NAME has been initiated. You can now update it in src/domogik_packages/docs/$PKG_TYPE/$PKG_NAME/"
echo "To generate the html documentation, do : "
echo " make clean && make html"
echo "It will be generated in the folder src/domogik_packages/docs/$PKG_TYPE/$PKG_NAME/_build/html/"
echo "The _build folder will not be updated on the mercurial repository as it is generated content."

