#!/usr/bin/env python3

from flask import Flask
from configparser import ConfigParser

__author__ = "Richard Pöttler & Manuel Pirker"
__copyright__ = "Copyright (c) 2021 Richard Pöttler & Manuel Pirker"
__license__ = "MIT"
__email__ = "manuel.pirker@tugraz.at"


app = Flask(__name__)

config = ConfigParser()
config.read("config.ini")
app.secret_key = config["server"]["secret_key"]

app.config["problems"] = {
    "Hydraulics": {
		"Free Surface Flow: Strickler": "flow_regime",
		"Free Surface Flow: Flow Transition": "flow_regime_transition_bernoulli",
		"Pressurized Flow: Pipe between Basins": "pressure_pipe_single",
        "Pressurized Flow: Pipe System": "pressure_pipe",
    },
    "Mathematics": {
        "Linear Equation: Test only": "xy",
    },
}
app.config["submit_on_change"] = config["application"].getboolean("submit_on_change")

import ezprobs.main
import ezprobs.demo
import ezprobs.problems.xy
import ezprobs.problems.free_surface_01
import ezprobs.problems.free_surface_02
import ezprobs.problems.pressure_pipe_01
import ezprobs.problems.pressure_pipe_02

app.register_blueprint(demo.bp, url_prefix="/demo")
app.register_blueprint(problems.xy.bp, url_prefix="/problems/xy")
app.register_blueprint(
    problems.free_surface_01.bp, url_prefix="/problems/flow_regime"
)
app.register_blueprint(
    problems.free_surface_02.bp, url_prefix="/problems/flow_regime_transition_bernoulli"
)
app.register_blueprint(
    problems.pressure_pipe_01.bp, url_prefix="/problems/pressure_pipe"
)
app.register_blueprint(
    problems.pressure_pipe_02.bp, url_prefix="/problems/pressure_pipe_single"
)
