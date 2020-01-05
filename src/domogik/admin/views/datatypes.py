import json
import pprint
try:
    from flask_babel import gettext, ngettext
except ImportError:
    from flask.ext.babel import gettext, ngettext
    pass

from flask_login import login_required
from domogik.admin.application import app, render_template, timeit
from domogikmq.message import MQMessage
from domogikmq.reqrep.client import MQSyncReq
import collections

@app.route('/datatypes')
@login_required
@timeit
def datatypes():
    app.logger.debug(u"Display the datatypes page...")
    if app.datatypes == {}:
        app.logger.debug(u"No datatype in memory (app.datatypes), loading them from MQ...")
        cli = MQSyncReq(app.zmq_context)
        msg = MQMessage()
        msg.set_action('datatype.get')
        res = cli.request('manager', msg.get(), timeout=10)
        if res is not None:
            app.datatypes = res.get_data()['datatypes']
            app.logger.debug(u"Loading done!")
        else:
            app.datatypes = {}
            app.logger.warning(u"Loading failed : empty response o_O ?")

    def formatDT( dt ):
        tmp = {}
        tmp['text'] = dt
        no_child = False
        if 'childs' not in app.datatypes[dt]:
            no_child = True
        elif app.datatypes[dt]['childs'] == []:
            no_child = True
        if no_child == False:
            tmp['nodes'] = collections.OrderedDict()
        for (key, val) in app.datatypes[dt].items():
            tmp[key] = val
        return tmp

    def add_in_tree(dt, dt_tree, dt_parent=None, level=0, dt_tree_subpart=None):
        """ Recursive function to build the tree correctly
            @param dt : datatype name to add
            @param level : level of recursivity (for information only)
        """
        if dt_tree_subpart == None:
            dt_tree_subpart = dt_tree
        if dt_parent != None:
            dt_tree_subpart['nodes'][dt] =  formatDT(dt)
        else:
            dt_tree[dt] = formatDT(dt)

        for a_child in app.datatypes[dt]['childs']:
            #print("     - child of {1} : {0}".format(a_child, dt))
            #pp = pprint.PrettyPrinter(indent=4)
            #pp.pprint(dt_tree_subpart)
            if level > 0:
                add_in_tree(a_child, dt_tree, dt, level + 1, dt_tree_subpart['nodes'][dt])
            else:
                add_in_tree(a_child, dt_tree, dt, level + 1, dt_tree[dt])
        #pp = pprint.PrettyPrinter(indent=4)
        #pp.pprint(dt_tree)

    def gettext_dt(data_types) :
        """ Recursive function to translate the data_type 'usage' key
            @param data_types : list of datatypes value keys to translate
        """
        if 'usage' in data_types and data_types['usage'] != "" :
            data_types['usage'] = gettext(data_types['usage'])
        if 'example' in data_types and data_types['example'] != "" :
            data_types['example'] = gettext(data_types['example'])
        if 'values' in data_types :
            for v in data_types['values'] :
                 if data_types['values'][v] != "" : data_types['values'][v] = gettext(data_types['values'][v])
        if 'nodes' in data_types :
            for dt in data_types['nodes'] :
                data_types['nodes'][dt] = gettext_dt(data_types['nodes'][dt])
        return data_types

    dt_tree = collections.OrderedDict()
    app.logger.debug(u"Loop over all the datatypes...")
    for dt in app.datatypes:
        if 'parent' not in app.datatypes[dt]:
            no_parent = True
        elif app.datatypes[dt]['parent'] == "":
            no_parent = True
        else:
            no_parent = False
        app.logger.debug(u"- '{0}' (has no parent (bool) : '{1}'".format(dt, no_parent))
        # recursive call for the top datatypes (the ones with no parents)
        if no_parent:
            app.logger.debug("  => No parent : adding in the tree")
            add_in_tree(dt, dt_tree)
    dt_list =[]
    for dt in dt_tree :
        dt_list.append(dict(gettext_dt(dt_tree[dt])))

    return render_template('datatypes.html',
        datatypes = json.dumps(dt_list),
        mactive = "datatypes")
