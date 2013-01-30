- Make sure to add in /etc/domogik.cfg :
[mq]
event_pub_port = 40410
event_sub_port = 40411

- Run ./mq_event_fwd.py

- Run ./sample_receiver.py [filter1] [filter2] ... [filterN]
You can ran as many instances as you want.

- Run ./sample_emitter.py

Possible values for filter :

database
package
plugin
package plugin # 2 filters
package.installed
plugin.enabled
database.insert
...
(See sample_emitter.py)
