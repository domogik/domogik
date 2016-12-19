import json
import pprint
from flask_login import login_required
from domogik.admin.application import app, render_template

@app.route('/datatypes')
@login_required
def datatypes():
    if app.datatypes == {}:
        cli = MQSyncReq(app.zmq_context)
        msg = MQMessage()
        msg.set_action('datatype.get')
        res = cli.request('manager', msg.get(), timeout=10)
        if res is not None:
            app.datatypes = res.get_data()['datatypes']
        else:
            app.datatypes = {}

    def formatDT( dt ):
        tmp = {}
        tmp['text'] = dt
        for (key, val) in app.datatypes[dt].items():
            if key not in ['childs', 'parent']:
                tmp[key] = val
        return tmp

    tmp = {}
    for dt in app.datatypes:
        tmp[dt] = formatDT(dt)
        for ch in app.datatypes[dt]['childs']:
            if 'nodes' not in tmp[dt]: tmp[dt]['nodes'] = []
            tmp[dt]['nodes'].append( formatDT(ch) )
    pp = pprint.PrettyPrinter(indent=4)
    pp.pprint(tmp)

    return render_template('datatypes.html',
        datatypes = json.dumps( tmp.values() ),
        mactive = "datatypes")
