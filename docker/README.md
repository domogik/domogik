Domogik on Docker !
===================

Get and run the docker container
================================

Please note that the container name may change in the future ;)

To be informed on changes, you may come back and read this file.

To test Domogik, just run :

    docker pull domogik/domogik:develop 
    docker run -t -i -p 40404:40404 -p 40405:40405 -p 40406:40406 domogik/domogik:develop 

The following components will be installed : 

* a MySQL server with a fresh database (not persisted!)
* Domogik-MQ 1.4
* Domogik in the last release of the develop branch
* Domoweb in the last release of the develop branch
* A few packages : plugin diskfree, plugin weather, brain base (for the butler), ... They are not configured!

All will be started automatically and available on :
* Domogik administration : http://ip:40406/
* Domoweb interface : http://ip:40404/

The ip should be your docker host ip (on most configurations).

To connect to the interfacaes, you can use the user **admin** and password **123**.

On system side, the **password** for the users **root** and ** domogik** is : **domopass**


Enjoy ;)

When is the container updated ?
===============================

Each time we pus a commit on Github repository a new docker container is built to replace the previous one.

