from domogik.common.packagejson import PackageJson
from domogik.common.configloader import Loader
import json
from xml.dom import minidom

def url2xpl_stat_to_json(techno):
    # loda the json file
    pjson = PackageJson(techno)
    jsn = pjson.json
    jsn["xpl_commands"] = []
    jsn["xpl_stats"] = []
    cfg = Loader('domogik')
    config = cfg.load()
    conf = dict(config[1])
    if not conf.has_key('package_path'):
        print "This script should only be launched in DEV mode, exiting"
        return
    if not conf.has_key('src_prefix'):
        print "src_prefix is not defined, exiting"
        return
    # find all *.xml files
    for fname in jsn["files"]:
        if fname.endswith('.xml'):
            print "handling file %s" % (fname)
            # parse the files
            xml_data = minidom.parse(conf['src_prefix'] + '/' + fname)
            if xml_data.getElementsByTagName("command") == []:
                # We have a stats file
                for schema in xml_data.getElementsByTagName("schema"):
                    # values
                    for value in schema.getElementsByTagName("value"):
                        stat = {}
                        stat["parameters"] = {}
                        stat["parameters"]["static"] = []
                        stat["parameters"]["device"] = []
                        stat["parameters"]["dynamic"] = []
                        stat["schema"] = schema.attributes.get("name").value
                        stat["reference"] = fname
                        # device inside mapping = device
                        stat["parameters"]["device"].append(
                            {'key': 
                            schema.getElementsByTagName("device")[0].attributes.get("field").value})
                        #<value field="current" new_name="gust" 
                        #   filter_key="type" filter_value="gust" />
                        # filter_key + filter_value => static
                        if value.attributes.get("filter_key") is not None and \
                            value.attributes.get("filter_value") is not None:
                            item = {}
                            item["key"] = \
                                value.attributes.get("filter_key").value
                            item["value"] = \
                                value.attributes.get("filter_value").value
                            stat["parameters"]["static"].append(item)
                        # new_name => 
                        # field = dynamic
                        item = {}
                        item["key"] = value.attributes.get("field").value
                        if value.attributes.get("new_name") is not None:
                            item["new_name"] = value.attributes.get("new_name").value
                        stat["parameters"]["dynamic"].append(item)
                        # each value field
                        jsn["xpl_stats"].append(stat)
            else:
                cmd = {}
                cmd["parameters"] = {}
                cmd["parameters"]["static"] = []
                cmd["parameters"]["device"] = []
                cmd["parameters"]["dynamic"] = []
                stat = {}
                stat["parameters"] = {}
                stat["parameters"]["static"] = []
                stat["parameters"]["device"] = []
                stat["parameters"]["dynamic"] = []
                #=== Do the command part
                xml_command = xml_data.getElementsByTagName("command")[0]
                xml_parameters = xml_command.getElementsByTagName("parameters")[0]
                #   command name => reference
                cmd["reference"] = str(xml_data.getElementsByTagName("command")[0].attributes.get("name").value)
                #   schema => schema
                cmd["schema"] = str(xml_command.getElementsByTagName("schema")[0].firstChild.nodeValue)
                #   not all files have a command 
                if xml_command.getElementsByTagName("command-xpl-value") != []:
                    static = {}
                    #command-key => parameters static
                    static["key"] = str(xml_command.getElementsByTagName("command-key")[0].firstChild.nodeValue)
         	        #command-xpl-value => parameter static value
                    static["value"] = str(xml_command.getElementsByTagName("command-xpl-value")[0].firstChild.nodeValue)
                    cmd["parameters"]["static"].append(static)
       	        #   address-key => parameters device
                cmd["parameters"]["device"].append({'key': \
                    xml_command.getElementsByTagName("address-key")[0].firstChild.nodeValue})
	        #   parameters => dynamic
                for param in xml_parameters.getElementsByTagName("parameter"):
                #   loc = param.attributes.get("location")
                    value = param.attributes.get("value")
                    item = {}
                    item["key"] = param.attributes.get("key").value
                    if value is not None:
                        item["value"] = value.value
                        cmd["parameters"]["static"].append(item)
                    else:
                        cmd["parameters"]["dynamic"].append(item)
                #=== Do the stat part
                xml_listener = xml_data.getElementsByTagName("listener")[0]
                xml_filter = xml_listener.getElementsByTagName("filter")[0]
                #   command name => reference
                stat["reference"] = xml_data.getElementsByTagName("command")[0].attributes.get("name").value
                #   schema => schema
                stat["schema"] = xml_listener.getElementsByTagName("schema")[0].firstChild.nodeValue
                #   keys
                for key in xml_filter.getElementsByTagName("key"):
                    item = {}
                    item["key"] = key.attributes.get("name").value
                    value = key.attributes.get("value").value
                    if value.startswith('@') and value.endswith('@'):
                        stat["parameters"]["device"].append(item)
                    else:
                        item["value"] = value
                        stat["parameters"]["static"].append(item)
                #   link the stat with the cmd
                cmd["stat_reference"] = stat["reference"]
         	#   insert into json
                jsn["xpl_commands"].append(cmd)
                jsn["xpl_stats"].append(stat)
    # rewrite the json file
    print json.dumps(jsn, sort_keys=True, indent=4)
    

if __name__ == "__main__":
    url2xpl_stat_to_json('rfxcom')
    url2xpl_stat_to_json('velbus')
    url2xpl_stat_to_json('knx')
    url2xpl_stat_to_json('bluez')
