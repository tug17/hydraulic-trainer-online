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


bp = Blueprint("free_surface_01_fit_05", __name__)


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
    x_min = -1000 * M
    x_max = 400 * M
    x_max = 1000 * M
    y_min = 0 * M
    y_max = 12 * M
    y_max = 20 * M

    # start and end of the sufrace calculation
    x_a = 0 * M

    # assemble ruehlmann line
    xr = []
    tr = []
    yr = []

    if ks_1 == ks_2:
        xr = np.array([x_min, x_max])
        tr = np.array([t_n1, t_n2])
        yr = (i * (x_max - xr)) + tr
    elif t_n2 < t_crit:
        # fit polynominal for the water sufrace
        # y = a x^4 + b x^3 + c x^2 + d x + e
        # y' = 4 a x^3 + 3 b x^2 + 2 c x + d
        # y(x=0) = h_a + t_crit
        # y(-l_au) = h_au + t_n1
        # y(l_ad) = h_ad + t_n2
        # y'(-l_au) = -i
        # y'(l_ad) = -i

        l_au = ruehlmann_rect(0.99 * t_n1, t_n1, t_crit, t_crit, i)
        l_ad = l_transition_i_r_rect(q, ks_2, w, t_crit, t_n2, i)
        h_au = i * (x_max + l_au)
        h_a = i * x_max
        h_ad = i * (x_max - l_ad)

        e = h_a + t_crit

        left = np.array(
            [
                [(-l_au) ** 4, (-l_au) ** 3, (-l_au) ** 2, (-l_au) ** 1],
                [(l_ad) ** 4, (l_ad) ** 3, (l_ad) ** 2, (l_ad) ** 1],
                [
                    4 * (-l_au) ** 3,
                    3 * (-l_au) ** 2,
                    2 * (-l_au) ** 1,
                    1 * (-l_au) ** 0,
                ],
                [
                    4 * (l_ad) ** 3,
                    3 * (l_ad) ** 2,
                    2 * (l_ad) ** 1,
                    1 * (l_ad) ** 0,
                ],
            ]
        )
        right = np.array([h_au + t_n1 - e, h_ad + t_n2 - e, -i, -i])
        (a, b, c, d) = np.linalg.solve(left, right)
        fit = lambda x: a * x ** 4 + b * x ** 3 + c * x ** 2 + d * x + e

        x_pre = [x_min]
        y_pre = [i * (x_max - x_min) + t_n1]
        if -l_au < x_min:
            x_pre = [-l_au]
            y_pre = [h_au + t_n1]

        x_post = [x_max]
        y_post = [t_n2]
        if l_ad > x_max:
            x_post = [l_ad]
            y_post = [h_ad + t_n2]

        positions = np.linspace(-l_au, l_ad, 100)

        xr = np.concatenate((x_pre, positions, x_post))
        yr = np.concatenate((y_pre, list(map(fit, positions)), y_post))
    else:
        factor = 0.99 if t_n2 < t_n1 else 1.01
        l_au = ruehlmann_rect(factor * t_n1, t_n1, t_n2, t_crit, i)

        xr.append(min(x_start, x_a - l_au))
        xr.append(x_a - l_au)
        tr.append(t_n1)
        tr.append(t_n1)

        ys = np.linspace(t_n1, t_n2, 22)
        for y in ys[1:-1]:
            xr.append(x_a - ruehlmann_rect(y, t_n1, t_n2, t_crit, i))
            tr.append(y)
        xr.append(x_a)
        tr.append(t_n2)
        xr.append(x_max)
        tr.append(t_n2)

        xr = np.array(xr)
        tr = np.array(tr)
        yr = (i * (x_max - xr)) + tr

    # assemble crit line
    tcr = np.array([t_crit, t_crit])
    xcr = np.array([x_min, x_max])
    ycr = (i * (x_max - xcr)) + tcr

    # assemble normal line
    xn = np.array([x_min, x_a, x_a, x_max])
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
