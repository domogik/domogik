from domogik.admin.application import app, login_manager, babel, render_template, timeit
from flask import request, flash, redirect, Response
import traceback
import time

@app.route('/dev/')
@timeit
def dev_root():
    try:
        return render_template('dev_index.html', nonav = True)
    except:
        app.logger.error(u"Error while displaying page : {0}".format(traceback.format_exc()))


@app.route('/dev/hello')
@timeit
def dev_hello():
    return render_template('dev_hello.html', nonav = True)


@app.route('/dev/sleep_during_20s')
@timeit
def dev_sleep_during_20s():
    print("Start sleeping...")
    time.sleep(20)
    print("Stop sleeping...")
    return render_template('dev_sleep.html', nonav = True)


@app.route('/dev/websockets')
@timeit
def dev_websockets():
    try:
        app.logger.error(u"WS test page displaying...")
        return render_template('dev_websockets.html', nonav = True)
    except:
        app.logger.error(u"Error while displaying page : {0}".format(traceback.format_exc()))




