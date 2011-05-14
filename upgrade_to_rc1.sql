/* Fix #848 */
ALTER TABLE core_device_stats CHANGE `key` `skey` VARCHAR( 30 ) CHARACTER SET utf8 COLLATE utf8_general_ci NOT NULL;
/* Fix #842 */
CREATE TABLE core_device_stats_temp LIKE core_device_stats;
ALTER TABLE core_device_stats_temp DROP PRIMARY KEY;
ALTER TABLE core_device_stats_temp ADD id INT(11) NOT NULL AUTO_INCREMENT PRIMARY KEY FIRST;
INSERT INTO core_device_stats_temp (date, timestamp, skey, device_id, value_num, value_str) SELECT date, timestamp, skey, device_id, value_num, value_str FROM core_device_stats;
DROP TABLE core_device_stats;
RENAME TABLE core_device_stats_temp TO core_device_stats;
