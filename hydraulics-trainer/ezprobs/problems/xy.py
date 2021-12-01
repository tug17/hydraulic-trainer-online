#!/usr/bin/env python3

from flask import Blueprint, Response, render_template, request, session
from ezprobs.problems import Parameter, Plot
from io import BytesIO

import matplotlib as mpl

mpl.use("Agg")

import matplotlib.pyplot as plt

__author__ = "Richard Pöttler"
__copyright__ = "Copyright (c) 2021 Richard Pöttler"
__license__ = "MIT"
__email__ = "richard.poettler@gmail.com"


bp = Blueprint("xy", __name__)


def compute_solution():
    a = 1
    b = 1

    # a POST request is used to pass parameters to the calculation
    if request.method == "POST":
        # extract and cast the parameters
        a = int(request.form["a"])
        b = int(request.form["b"])

    return {"a": a, "b": b}


@bp.route("/", methods=["POST", "GET"])
def index():
    # compute the solution
    solution = compute_solution()

    # pack the values needed when generating the solution section
    # add the solution values to the session since the generation of the
    # graph is a separate request
    session["solution"] = solution

    # define configurable parameters
    parameters = [
        Parameter(
            "a",
            "a",
            -5,
            5,
            1,
            solution["a"],
            description="Inclination of the function",
        ),
        Parameter(
            "b", "b", -5, 5, 1, solution["b"], description="Offset of the function"
        ),
    ]

    # define a plot which should appear above the parameters
    plot = Plot("plot", alt="plot", caption="Plot of the function.")

    return render_template(
        "problems/xy.html", plot=plot, parameters=parameters, solution=solution
    )


@bp.route("/plot")
def plot_function():
    # extract the needd values from the session
    a = session["solution"]["a"]
    b = session["solution"]["b"]

    # generate the plot
    fig, ax = plt.subplots()
    x = [0, 10]
    y = [i * a + b for i in x]
    ax.plot(x, y)

    # save the plot to a buffer
    buffer = BytesIO()
    fig.savefig(buffer, format="png")
    plt.close(fig)
    # stream the buffer to the client
    return Response(buffer.getvalue(), mimetype="image/png")


@bp.route("/ajax", methods=["POST", "GET"])
def ajax():
    solution = compute_solution()
    session["solution"] = solution

    return render_template(
        "problems/xy_solution.html",
        solution=solution,
    )
