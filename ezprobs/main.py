#!/usr/bin/env python3

from ezprobs import app

from flask import render_template

__author__ = "Richard Pöttler"
__copyright__ = "Copyright (c) 2021 Richard Pöttler"
__license__ = "MIT"
__email__ = "richard.poettler@gmail.com"


@app.route("/")
def index():
    return render_template("index.html")
