#!/bin/sh
#
# Sets the default svn properties

KEYWORDS="Author LastChangedDate LastChangedRevision LastChangedBy HeadURL Id"

for i in `find -name "*.py"`; do
	echo $i
	svn propset svn:eol-style native $i
	svn propset svn:keywords "$KEYWORDS" $i
	svn propset svn:mime-type "text/plain" $i
done

for i in `find -name "*.php"`; do
	echo $i
	svn propset svn:eol-style native $i
	svn propset svn:keywords "$KEYWORDS" $i
	svn propset svn:mime-type "text/plain" $i
done

for i in `find -name "*.html"`; do
	echo $i
	svn propset svn:eol-style native $i
	svn propset svn:keywords "$KEYWORDS" $i
	svn propset svn:mime-type "text/plain" $i
done

for i in `find -name "*.js"`; do
	echo $i
	svn propset svn:eol-style native $i
	svn propset svn:keywords "$KEYWORDS" $i
	svn propset svn:mime-type "text/plain" $i
done

for i in `find -name "*.css"`; do
	echo $i
	svn propset svn:eol-style native $i
	svn propset svn:keywords "$KEYWORDS" $i
	svn propset svn:mime-type "text/xml" $i
done

for i in `find -name "*.txt"`; do
	echo $i
	svn propset svn:eol-style native $i
	svn propset svn:keywords "$KEYWORDS" $i
	svn propset svn:mime-type "text/plain" $i
done

for i in `find -name "*.sql"`; do
	echo $i
	svn propset svn:eol-style native $i
	svn propset svn:keywords "$KEYWORDS" $i
	svn propset svn:mime-type "text/plain" $i
done

for i in `find -name "*.sh"`; do
	echo $i
	svn propset svn:executable true $i
	svn propset svn:eol-style native $i
	svn propset svn:keywords "$KEYWORDS" $i
	svn propset svn:mime-type "text/plain" $i
done

for i in `find -name "*.png"`; do
	echo $i
	svn propset svn:mime-type "image/png" $i
done

for i in `find -name "*.jpg"`; do
	echo $i
	svn propset svn:mime-type "image/jpeg" $i
done

for i in `find -name "*.jpeg"`; do
	echo $i
	svn propset svn:mime-type "image/jpeg" $i
done

for i in `find -name "*.gif"`; do
	echo $i
	svn propset svn:mime-type "image/gif" $i
done

for i in `find -name "*.zip"`; do
	echo $i
	svn propset svn:mime-type "application/zip" $i
done

