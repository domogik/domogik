# This script will generate a self signed SSL certificate which will be valid for 2 years.
# The certificate will have no passphrase

DIR=/var/lib/domogik
echo "----------------------------------------------------------"
echo "Generating the certificate and key !"
echo "----------------------------------------------------------"
echo ""
echo "Certificates will be generated in the folder '$DIR'"
openssl req -x509 -newkey rsa:2048 -keyout $DIR/ssl_key.pem -out $DIR/ssl_cert.pem -days 730 -nodes << EOF
FR
Domogik state
Domogik city
Domogik inc
.
.
.
.
EOF

if [[ ! -f $DIR/ssl_key.pem || ! -f $DIR/ssl_cert.pem ]] ; then
    echo "[ ERROR ] An error occured, please check the lines before!"
    exit 1
fi

echo ""
echo "[  OK  ] SSL certificate and key created. "
echo ""
echo ""
echo "----------------------------------------------------------"
echo "Setting domogik configuration..."
echo "----------------------------------------------------------"
echo ""
sed -i "s/^use_ssl.*/use_ssl = True/" /etc/domogik/domogik.cfg
sed -i "s#^ssl_certificate.*#ssl_certificate = $DIR/ssl_cert.pem#" /etc/domogik/domogik.cfg
sed -i "s#^ssl_key.*#ssl_key = $DIR/ssl_key.pem#" /etc/domogik/domogik.cfg
if [[ $? -ne 0 ]] ; then
    echo "[ ERROR ] An error occured, please check the lines before!"
    exit 2
fi
echo "[  OK  ] Configuration file updated!"
echo ""
echo "----------------------------------------------------------"
echo "==>        All is OK, please restart Domoweb!          <=="
echo "----------------------------------------------------------"

