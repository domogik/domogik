from domogik.admin.application import app
from flask import render_template

@app.route('/')
def index():
    return render_template('index.html')
