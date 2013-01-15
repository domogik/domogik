from flask import Flask

urlHandler = Flask(__name__)

import domogik.xpl.lib.rest.urls.root
import domogik.xpl.lib.rest.urls.blah
