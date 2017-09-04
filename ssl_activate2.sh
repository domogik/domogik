#!/bin/bash
#
# Domogik
#
# This script will :
# - create a root CA (if it does not exist)
# - create a certificate for Domogik
# - create a certificate for Domoweb (if installed)
# - configure Domogik to use the certificate
# - configure Domoweb (if installed) to use the certificate
#
# The certificate informations are generic. If you want to customize them, feel free to edit this script.
#
# The certificate will be associated to the server ip (dynamically found) and the internet public ip (dynamically found) to allow it to be granted on smartphone devices certificates stores.
#
#
# Inspiration from https://alexanderzeitler.com/articles/Fixing-Chrome-missing_subjectAltName-selfsigned-cert-openssl/

### functions ##################################

function info() {
    echo -e "[ INFO  ] \e[93m$*\e[39m"
}

function ok() {
    echo -e "[ OK    ] \e[92m$*\e[39m"
}

function error() {
    #echo -e "[ ERROR ] \e[91m$*\e[39m"
    echo -e "[ \e[5mERROR\e[0m ] \e[91m$*\e[39m"
}

function abort() {
    error $*
    echo -e "[ \e[5mABORT\e[0m ] \e[91mThe installation is aborted due to the previous error!\e[39m"
    exit 1
}


function get_server_ip() {
    # return all configured IP (except loopback)
    hostname -I
}

function get_public_ip() {
    curl ipinfo.io/ip
    [ $? -ne 0 ] && abort "Error : please check that 'curl' is installed"
}

################################################




### script #####################################

DIR=/var/lib/domogik
DIR_DOMOWEB=/var/lib/domoweb
PASSPHRASE=domogikpassphrase
DN_C=FR
DN_ST=France
DN_L=Paris
DN_O=Domogik
DN_OU=Domogik
DN_emailAddress=none@domogik.org

mkdir -p $DIR/ssl_test/

info "Step 1 : search your public ip from 'ipinfo.io/ip' to add it in the certificates..."
public_ip=$(get_public_ip)
ok "Your public ip is : $public_ip"

info "Step 2 : search your server ip(s) to add it(them) in the certificates..."
server_ip=$(get_server_ip)
ok "Your server ip(s) is(are) : $server_ip"

### Step 3 : create an openssl configuration file : $DIR/ssl/server.csr.cnf
info "Step 3 : create an openssl configuration file : $DIR/ssl/server.csr.cnf"
echo "[req]
default_bits = 2048
prompt = no
default_md = sha256
distinguished_name = dn

[dn]
C=$DN_C
ST=$DN_ST
L=$DN_L
O=$DN_O
OU=$DN_OU
emailAddress=$DN_emailAddress
CN = localhost" > $DIR/ssl/server.csr.cnf
[ $? -ne 0 ] && abort "Error"
ok "Done"



### Step 4 : create a root CA cert

# TODO : skip if it already exists
# TODO : skip if it already exists
# TODO : skip if it already exists

info "Step 4 : create a root CA cert"
if [[ ! -f $DIR/ssl/rootCA.key || ! -f $DIR/ssl/rootCA.pem ]] ; then
    info "There is no existing root CA in the folder '$DIR'. Creating it..."
    openssl genrsa -des3 -passout pass:$PASSPHRASE -out $DIR/ssl/rootCA.key 2048 
    [ $? -ne 0 ] && abort "Error"
    openssl req -x509 -new -nodes -passin pass:$PASSPHRASE -key $DIR/ssl/rootCA.key -sha256 -days 1024 -passout pass:$PASSPHRASE -out $DIR/ssl/rootCA.pem  -config <( cat $DIR/ssl/server.csr.cnf )
    [ $? -ne 0 ] && abort "Error"
    ok "Done"

else
    info "There is already an existing root CA in the folder '$DIR'. Skipping the creation."
fi





### Step 5 : create the $DIR/ssl/v3.ext file in order to create a X509 v3 certificate instead of a v1 which is the default when not specifying a extension file
info "Step 5 : create the $DIR/ssl/v3.ext file in order to create a X509 v3 certificate instead of a v1 which is the default when not specifying a extension file"

# TODO : fill dynamically the private ip and public ip (get it from myip.com or something like that)
# TODO : fill dynamically the private ip and public ip (get it from myip.com or something like that)
# TODO : fill dynamically the private ip and public ip (get it from myip.com or something like that)

echo "authorityKeyIdentifier=keyid,issuer
basicConstraints=CA:TRUE
keyUsage = digitalSignature, nonRepudiation, keyEncipherment, dataEncipherment
subjectAltName = @alt_names

[alt_names]
DNS.1 = localhost
IP.1 = 192.168.1.50" > $DIR/ssl/v3.ext
[ $? -ne 0 ] && abort "Error"
ok "Done"



### Step 6 : create the certificates for Domogik
info "Step 6 : create the certificates"
openssl req -new -sha256 -nodes -passin pass:$PASSPHRASE -out $DIR/server.csr -newkey rsa:2048 -keyout $DIR/server.key -config <( cat $DIR/ssl/server.csr.cnf )
[ $? -ne 0 ] && abort "Error"
openssl x509 -req -passin pass:$PASSPHRASE -in $DIR/server.csr -CA $DIR/ssl/rootCA.pem -CAkey $DIR/ssl/rootCA.key -CAcreateserial -out $DIR/server.crt -days 500 -sha256 -extfile $DIR/ssl/v3.ext
[ $? -ne 0 ] && abort "Error"
ok "Done"

info "Step 7 : Configuring Domogik..."

sed -i "s/^use_ssl.*/use_ssl = True/" /etc/domogik/domogik.cfg
[ $? -ne 0 ] && abort "Error"
sed -i "s#^ssl_certificate.*#ssl_certificate = $DIR/server.crt#" /etc/domogik/domogik.cfg
[ $? -ne 0 ] && abort "Error"
sed -i "s#^ssl_key.*#ssl_key = $DIR/server.key#" /etc/domogik/domogik.cfg
[ $? -ne 0 ] && abort "Error"
ok "Done"


### Domoweb (if installed)
if [[ -f /etc/domoweb.cfg ]] ; then
    AND_DOMOWEB="and Domoweb" # for the final message
    info "Domoweb seemed to be installed, activating SSL on Domoweb also..."

    ### Step 8 : create the certificates for Domoweb
    info "Step 8 : create the certificates for Domoweb"
    openssl req -new -sha256 -nodes -passin pass:$PASSPHRASE -out $DIR_DOMOWEB/server.csr -newkey rsa:2048 -keyout $DIR_DOMOWEB/server.key -config <( cat $DIR/ssl/server.csr.cnf )
    [ $? -ne 0 ] && abort "Error"
    openssl x509 -req -passin pass:$PASSPHRASE -in $DIR_DOMOWEB/server.csr -CA $DIR/ssl/rootCA.pem -CAkey $DIR/ssl/rootCA.key -CAcreateserial -out $DIR_DOMOWEB/server.crt -days 500 -sha256 -extfile $DIR/ssl/v3.ext
    [ $? -ne 0 ] && abort "Error"
    ok "Done"

    ### Step 9 : Configuring Domoweb...
    info "Setp 9 : Configuring Domoweb..."
    TMP_DMW_CFG=/tmp/domoweb.cfg.$$
    cp /etc/domoweb.cfg $TMP_DMW_CFG
    [ $? -ne 0 ] && abort "Error"
    sed -i "s/^use_ssl.*/use_ssl = True/" $TMP_DMW_CFG
    [ $? -ne 0 ] && abort "Error"
    sed -i "s#^ssl_certificate.*#ssl_certificate = \"$DIR_DOMOWEB/server.crt\"#" $TMP_DMW_CFG
    [ $? -ne 0 ] && abort "Error"
    sed -i "s#^ssl_key.*#ssl_key = \"$DIR_DOMOWEB/server.key\"#" $TMP_DMW_CFG
    [ $? -ne 0 ] && abort "Error"
    cp $TMP_DMW_CFG /etc/domoweb.cfg
    [ $? -ne 0 ] && abort "Error"
    ok "Done"

else
    info "Domoweb seemed not to be installed, nothing will be done for Domoweb."
    AND_DOMOWEB=""
fi

echo ""
echo ""
info "Please restart Domogik $AND_DOMOWEB to apply the new certificates!"
echo ""
