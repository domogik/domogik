TMP_SQL=/tmp/dmg_tables_from_myisam_to_innodb.$$.sql
TMP_SQL2=/tmp/dmg_constraints.$$.sql
DMG_CFG=/etc/domogik/domogik.cfg
#DMG_CFG=/tmp/domogik.cfg

# automatically retrieve domogik 0.3 database configuration
if [ -f $DMG_CFG ] ; then
    echo "Domogik configuration file found. reading configuration..."
    IS_03=$(grep "^db_type" $DMG_CFG | wc -l)
    IS_04=$(grep "^type" $DMG_CFG | wc -l)
    if [ $IS_03 -eq 1 ] ; then
        PREFIX="db_"
    elif [ $IS_04 -eq 1 ] ; then
        PREFIX=""
    else
        "Domogik version unknown... Exiting!"
    fi
    SERVER=$(grep "^${PREFIX}host" $DMG_CFG | cut -d"=" -f2 | sed "s/ *//g" | head -1)
    PORT=$(grep "^${PREFIX}port" $DMG_CFG | cut -d"=" -f2 | sed "s/ *//g" | head -1)
    LOGIN=$(grep "^${PREFIX}user" $DMG_CFG | cut -d"=" -f2 | sed "s/ *//g" | head -1)
    PASSWORD=$(grep "^${PREFIX}password" $DMG_CFG | cut -d"=" -f2 | sed "s/ *//g" | head -1)
    DATABASE=$(grep "^${PREFIX}name" $DMG_CFG | cut -d"=" -f2 | sed "s/ *//g" | head -1)
else
    echo "It seems that no Domogik is installed... Exiting!"
    exit 1
fi

echo "Checking if some tables need to be converted to InnoDB..."
echo "- server : $SERVER:$PORT"
echo "- database : $DATABASE"
echo "- credentials : $LOGIN/****"
CMD="SELECT CONCAT('ALTER TABLE ', table_schema, '.', table_name, ' ENGINE=InnoDB;') from information_schema.tables where table_schema = '$DATABASE' and engine = 'MyISAM'"
mysql -u$LOGIN -p$PASSWORD -h$SERVER -P$PORT -B --skip-column-names -D$DATABASE -e "$CMD" > $TMP_SQL

# Try to add some possibly missing FK...
touch $TMP_SQL2
echo 'ALTER TABLE core_device ADD CONSTRAINT `core_device_ibfk_1` FOREIGN KEY (`device_usage_id`) REFERENCES `core_device_usage` (`id`);' >> $TMP_SQL2
echo 'ALTER TABLE core_device ADD CONSTRAINT `core_device_ibfk_2` FOREIGN KEY (`device_usage_id`) REFERENCES `core_device_type` (`id`);' >> $TMP_SQL2
echo 'ALTER TABLE core_device_feature ADD CONSTRAINT `core_device_feature_ibfk_2` FOREIGN KEY (`device_feature_model_id`) REFERENCES `core_device_feature_model` (`id`);' >> $TMP_SQL2
echo 'ALTER TABLE core_device_feature_model ADD CONSTRAINT `core_device_feature_model_ibfk_1` FOREIGN KEY (`device_type_id`) REFERENCES `core_device_type` (`id`);' >> $TMP_SQL2
echo 'ALTER TABLE core_device_stats ADD CONSTRAINT `core_device_stats_ibfk_1` FOREIGN KEY (`device_id`) REFERENCES `core_device` (`id`);' >> $TMP_SQL2
echo 'ALTER TABLE core_device_type ADD CONSTRAINT `core_device_type_ibfk_1` FOREIGN KEY (`device_technology_id`) REFERENCES `core_device_technology` (`id`);' >> $TMP_SQL2
echo 'ALTER TABLE core_user_account ADD CONSTRAINT `core_user_account_ibfk_1` FOREIGN KEY (`person_id`) REFERENCES `core_person` (`id`);' >> $TMP_SQL2


NB_LINES=$(cat $TMP_SQL | wc -l)

if [ $NB_LINES -gt 0 ] ; then
    echo "The following commands will be applied : this could take some time!"
    cat $TMP_SQL
    echo ""

    mysql -u$LOGIN -p$PASSWORD -h$SERVER -P$PORT -B --skip-column-names -D$DATABASE < $TMP_SQL
    if [ $? -eq 0 ] ; then
        echo "All is OK :)"
    else
        echo "ERROR : some error occured..."
    fi
else
    echo "All your tables are InnoDB. There is nothing to do"
fi
      
    
   
# add constraints in silence (as for most people they exist)
mysql -u$LOGIN -p$PASSWORD -h$SERVER -P$PORT -B --skip-column-names -D$DATABASE < $TMP_SQL2  > /dev/null 2>&1
