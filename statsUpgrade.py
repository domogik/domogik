#!/usr/bin/env python
import sys
from domogik.common.database import DbHelper

def corellateOld(devs):
    ret = {}
    for d in devs:
        d = list(d)
        if d[0] not in ret:
            ret[d[0]] = {}
            ret[d[0]]['name'] = d[1]
            ret[d[0]]['keys'] = []
            ret[d[0]]['keys'].append( d[2] )
        else:
            ret[d[0]]['keys'].append( d[2] )
    return ret


if __name__ == "__main__":
    # 0- connect to the DB
    db = DbHelper()
    db.open_session()

    # 1- list current devices  (odl ones)
    do = True
    old_devs = corellateOld(db.upgrade_list_old())
    while do:
        print old_devs
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
            print("")
            print("Selected Device {0}:".format(selDev['name']))
            j = 1
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
                    print("Starting the upgrade")
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

    # - print done
    print("")
    print("Hooray, all old devices have been uprgaded")

    # - Disconnect the db
    del(db)
