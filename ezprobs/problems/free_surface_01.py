#!/usr/bin/env python3

from flask import Blueprint, Response, render_template, request, session
from ezprobs.hydraulics import (
    t_n_rect,
    t_crit_rect,
    ruehlmann_rect,
    l_transition_i_r_rect,
)
from ezprobs.problems import Parameter, Plot
from ezprobs.units import M, S, M3PS, GRAVITY, PERMILLE
from io import BytesIO

import numpy as np
import matplotlib as mpl

mpl.use("Agg")

import matplotlib.pyplot as plt

__author__ = "Richard Pöttler"
__copyright__ = "Copyright (c) 2021 Richard Pöttler"
__license__ = "MIT"
__email__ = "richard.poettler@gmail.com"


bp = Blueprint("free_surface_01", __name__)


def compute_solution():
    w = 4 * M
    q = 30 * M3PS
    i = 7.6 * PERMILLE

    ks1 = 25 * M ** (1 / 3) / S
    ks2 = 55 * M ** (1 / 3) / S

    if request.method == "POST":
        ks1 = int(request.form["ks1"]) * M ** (1 / 3) / S
        ks2 = int(request.form["ks2"]) * M ** (1 / 3) / S

    t_crit = t_crit_rect(q, w)
    t_n1 = t_n_rect(q, ks1, i, w)
    t_n2 = t_n_rect(q, ks2, i, w)

    return {
        "i": i,
        "w": w,
        "q": q,
        "t_crit": t_crit,
        "t_n1": t_n1,
        "ks_1": ks1,
        "t_n2": t_n2,
        "ks_2": ks2,
    }


@bp.route("/", methods=["POST", "GET"])
def index():
    solution = compute_solution()
    session["solution"] = solution

    parameters = [
        Parameter(
            "ks1",
            "ks1",
            20,
            30,
            1,
            solution["ks_1"],
            unit="m^{1/3}/s",
            description="Strickler value section 1",
        ),
        Parameter(
            "ks2",
            "ks2",
            10,
            70,
            10,
            solution["ks_2"],
            unit="m^{1/3}/s",
            description="Strickler value section 2",
        ),
    ]

    plot = Plot("plot", alt="surface", caption="Water Surface")

    return render_template(
        "problems/free_surface_01.html",
        plot=plot,
        parameters=parameters,
        solution=solution,
    )


@bp.route("/plot")
def plot_function():
    i = session["solution"]["i"]
    w = session["solution"]["w"]
    q = session["solution"]["q"]
    t_crit = session["solution"]["t_crit"]
    t_n1 = session["solution"]["t_n1"]
    ks_1 = session["solution"]["ks_1"]
    t_n2 = session["solution"]["t_n2"]
    ks_2 = session["solution"]["ks_2"]

    # plot window
    x_min = -400 * M
    x_max = 400 * M
    y_min = 0 * M
    y_max = 12 * M

    # start and end of the sufrace calculation
    x_start = -400 * M
    x_a = 0 * M
    x_end = 400 * M

    # assemble ruehlmann line
    xr = []
    tr = []

    if ks_1 == ks_2:
        xr.append(x_start)
        tr.append(t_n1)
    elif t_n2 < t_crit:
        # ruehlmann decline until t_crit at point a
        l_au = ruehlmann_rect(0.99 * t_n1, t_n1, t_crit, t_crit, i)
        x_start = min(x_start, x_a - l_au)

        xr.append(x_start)
        xr.append(x_a - l_au)
        tr.append(t_n1)
        tr.append(t_n1)

        ys = np.linspace(t_n1, t_crit, 22)
        for y in ys[1:-1]:
            xr.append(x_a - ruehlmann_rect(y, t_n1, t_crit, t_crit, i))
            tr.append(y)
        xr.append(x_a)
        tr.append(t_crit)

        # decline with i_r
        l_transition = l_transition_i_r_rect(q, ks_2, w, t_crit, t_n2, i)
        xr.append(x_a + l_transition)
        tr.append(t_n2)

        x_end = max(x_end, x_a + l_transition)
    else:
        factor = 0.99 if t_n2 < t_n1 else 1.01
        l_au = ruehlmann_rect(factor * t_n1, t_n1, t_n2, t_crit, i)
        x_start = min(x_start, x_a - l_au)

        xr.append(x_start)
        xr.append(x_a - l_au)
        tr.append(t_n1)
        tr.append(t_n1)

        ys = np.linspace(t_n1, t_n2, 22)
        for y in ys[1:-1]:
            xr.append(x_a - ruehlmann_rect(y, t_n1, t_n2, t_crit, i))
            tr.append(y)
        xr.append(x_a)
        tr.append(t_n2)

    xr.append(x_end)
    tr.append(t_n2)

    xr = np.array(xr)
    tr = np.array(tr)
    yr = (i * (x_max - xr)) + tr

    # assemble crit line
    tcr = np.array([t_crit, t_crit])
    xcr = np.array([x_start, x_end])
    ycr = (i * (x_max - xcr)) + tcr

    # assemble normal line
    xn = np.array([x_start, x_a, x_a, x_end])
    tn = np.array([t_n1, t_n1, t_n2, t_n2])
    yn = (i * (x_max - xn)) + tn

    # assemble river bed
    xsole1 = [x_min, x_a]
    ysole1 = [i * (x_max - x_min), i * (x_max - x_a)]
    xsole2 = [x_a, x_max]
    ysole2 = [i * (x_max - x_a), 0]

    fig, ax = plt.subplots()
    ax.plot(xn, yn, label="Normal Depth", color="black", linestyle="dashed")
    ax.plot(xr, yr, label="Water Surface", color="blue", linewidth=3)
    ax.plot(xcr, ycr, label="Critical Depth", color="black", linestyle="dashdot")
    ax.plot(xsole1, ysole1, label="Ground 1", color="black")
    ax.plot(xsole2, ysole2, label="Ground 2", color="black", linewidth=4)

    ax.grid()
    ax.legend()
    ax.set_xlim(x_min, x_max)
    ax.set_ylim(y_min, y_max)
    ax.set_xlabel("Distance [m]")
    ax.set_ylabel("Height [m]")
    ax.set_title("Water Surface")

    buffer = BytesIO()
    fig.savefig(buffer, format="png")
    plt.close(fig)
    return Response(buffer.getvalue(), mimetype="image/png")


@bp.route("/ajax", methods=["POST", "GET"])
def ajax():
    solution = compute_solution()
    session["solution"] = solution

    return render_template(
        "problems/free_surface_01_solution.html",
        solution=solution,
    )
