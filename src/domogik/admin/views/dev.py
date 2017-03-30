from domogik.admin.application import app, login_manager, babel, render_template
from flask import request, flash, redirect, Response
import traceback
import time

@app.route('/dev/')
def dev_root():
    try:
        return render_template('dev_index.html', nonav = True)
    except:
        app.logger.error(u"Error while displaying page : {0}".format(traceback.format_exc()))


@app.route('/dev/hello')
def dev_hello():
    return render_template('dev_hello.html', nonav = True)


@app.route('/dev/sleep_during_20s')
def dev_sleep_during_20s():
    print("Start sleeping...")
    time.sleep(20)
    print("Stop sleeping...")
    return render_template('dev_sleep.html', nonav = True)


@app.route('/dev/websockets')
def dev_websockets():
    try:
        app.logger.error(u"WS test page displaying...")
        return render_template('dev_websockets.html', nonav = True)
    except:
        app.logger.error(u"Error while displaying page : {0}".format(traceback.format_exc()))


# TODO : DEL
#@app.route('/dev/websockets_broadcast')
#def dev_websockets_broadcast():
#    try:
#        app.logger.error(u"WS test page displaying...")
#        return render_template('dev_websockets_broadcast.html', nonav = True)
#    except:
#        app.logger.error(u"Error while displaying page : {0}".format(traceback.format_exc()))


