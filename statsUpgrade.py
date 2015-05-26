#!/usr/bin/env python
import sys
from domogik.common.database import DbHelper
from domogik import __version__

def corellateOld(devs):
    ret = {}
    for d in devs:
        d = list(d)
        if d[0] not in ret:
            ret[d[0]] = {}
            ret[d[0]]['name'] = d[1]
            ret[d[0]]['id'] = d[0]
            ret[d[0]]['keys'] = []
            ret[d[0]]['keys'].append( d[2] )
        else:
            ret[d[0]]['keys'].append( d[2] )
    return ret


if __name__ == "__main__":
    print("Welcome to the DOmogik upgrade system")
    print("This system can upgrade statistics to DOMOGIk 0.4")
    print("Source: 0.3")
    print("Destination: 0.4")
    if __version__ != "0.4.0":
        print("")
        print("ERROR: This is only supported in domogik 0.4.0")
        print("Your domogik version is {0}".format(__version__))
        print("")
        exit()
    # 0- connect to the DB
    db = DbHelper()
    db.open_session()

    # 1- list current devices  (odl ones)
    do = True
    old_devs = corellateOld(db.upgrade_list_old())
    if len(old_devs) == 0:
        do = False
        print("Hooray, all old devices have been uprgaded")
    while do:
        print("Here is a list of all old devices, select the one you want to upgrade")
        print("")
        # show dev menu
        i = 1
        for dev in old_devs:
            print("{0}. {1}".format(i, old_devs[dev]['name']))
            i = i + 1
        print("0. Exit")
        sel = i + 1
        while sel > i:
            try:
                sel = int(raw_input('Select Action: '))
            except:
                print('ERROR: select a number between 0 and {0}. Try again'.format(i))
                sel = i + 1
        # we have the device list stats keys
        if sel > 0:
            selDev = old_devs[old_devs.keys()[sel-1]]
            print("Selected Device {0}:".format(selDev['name']))
            print("")
            j = 1
            print("Now select the stats key you want to upgrade for this device")
            print("")
            for k in selDev['keys']:
                print("{0}. {1}".format(j, k))
                j = j + 1
            print("0. Cancel");
            selk = j + 1
            while selk > j:
                try:
                    selk = int(raw_input('Select Action: '))
                except:
                    print('ERROR: select a number between 0 and {0}. Try again'.format(j))
                    selk = j + 1
            if selk > 0:
                selKey = selDev['keys'][selk-1]
                print("")
                print("Select device '{0}' with key '{1}' to upgrade".format(selDev['name'], selKey))
                print("")

                print ("Select the sensor to copy the data to")
                print("")
                newDev = db.list_devices()
                k = 1
                for nDev in newDev:
                    print("{0}. {1}".format(k, nDev["name"]))
                    k = k +1
                print("0. Exit")
                seln = k + 1
                while seln > k:
                    try:
                        seln = int(raw_input('Select Action: '))
                    except:
                        print('ERROR: select a number between 0 and {0}. Try again'.format(k))
                        seln = k + 1
                if seln > 0:
                    print("")
                    print ("Select the sensor to copy the data to")
                    print("")
                    l = 1
                    for nSen in newDev[(seln - 1)]['sensors']:
                        print("{0}. {1}".format(l, newDev[(seln - 1)]['sensors'][nSen]["name"]))
                        l = l + 1
                    print("0. Exit")
                    sels = l + 1
                    while sels > l:
                        try:
                            sels = int(raw_input('Select Action: '))
                        except:
                            print('ERROR: select a number between 0 and {0}. Try again'.format(l))
                            sels = l + 1
                    if sels > 0:
                        l = 1
                        selS = None
                        for nSen in newDev[(seln - 1)]['sensors']:
                            if l == sels:
                                selS = nSen
                            l = l + 1
                        print("")
                        print("====================================================================================")
                        print("Upgrade with the folowing info")
                        print("Old device:      {0}({1})".format(selDev['name'], selDev['id']))
                        print("Old stats key:   {0}".format(selKey))
                        print("New device:      {0}({1})".format(newDev[(seln - 1)]["name"], newDev[(seln - 1)]['id']))
                        print("New sensor:      {0}({1})".format(newDev[(seln - 1)]["sensors"][nSen]["name"], newDev[(seln - 1)]["sensors"][nSen]["id"]))
                        print("")
                        print("WARNING:")
                        print("By typing YES below this will start the upgrade process, after the process")
                        print("the upgraded stats keys will be DELETED from the core_device_stats sql tabel.")
                        print("This process can not be reversed, it is advised to make a backup of your")
                        print("datatabse before starting this process")
                        print("")
                        conf = ""
                        while conf not in ["YES I AM SURE", "no"]:
                            conf = raw_input("Type 'YES I AM SURE' to confirm, 'no' to cancel: ")
                        if conf == "YES I AM SURE":
                            print("Copying the stats")
                            print("This can take some time be patiant")
                            db.upgrade_do(selDev['id'], selKey, newDev[(seln - 1)]['id'], newDev[(seln - 1)]["sensors"][nSen]["id"])
                            # check if this is the last key
                            if len(old_devs[selDev['id']]['keys']) == 1:
                                print("This was the last key of the device, so deleting the device")
                                db.del_device(selDev['id'])
                            print("Upgrade DONE")
                            print ""
                        else:
                            print("Upgrade CANCELED")

        else:
            do = False
        # close all
        db.close_session()
        if do:
            db.open_session()
            old_devs = corellateOld(db.upgrade_list_old())
            if len(old_devs) == 0:
                do = False
                print("Hooray, all old devices have been uprgaded")

    # - Disconnect the db
    del(db)
