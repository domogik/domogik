#!/usr/bin/python
import json
import types

# read the datatypes file
f = open('../../src/domogik/common/datatypes.json', 'r')
fl = f.read()
f.close()

# json load
json = json.loads(fl)

# generate an ordered list
order_list = {}
for item_name in json.keys():
    item = json[item_name]
    if item['childs'] != []:
        order_list[item_name] = []
        for child_name in item['childs']:
            order_list[item_name].append(child_name)

# start generating the output
print("===============")
print("Known datatypes")
print("===============")
print("")
for main in order_list.keys():
    print(main)
    rule = ""
    for n in range(0,len(main)):
        rule += "="
    print(rule)
    print("")
    for child in order_list[main]:
        print "* {0}".format(child)
        data = json[child]
        for key in data.keys():
            if data[key] is not None:
                if key != 'childs' and key != 'parent':
                    if type(data[key]) is list:
                        print "   * {0}: {1}".format(key, data[key])
                    elif type(data[key]) is dict:
                        print "   * {0}:".format(key)
                        for item in data[key].keys():
                            print "      * {0} = {1}".format(item, data[key][item])
                    elif type(data[key]) is int:
                        print "   * {0}: {1}".format(key, data[key])
                    else:
                        print "   * {0}: {1}".format(key, data[key].encode('ascii', 'replace'))
        #print "   * raw: {0}".format(data)

    print("")
    print("")
