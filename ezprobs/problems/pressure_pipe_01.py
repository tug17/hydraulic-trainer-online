#!/usr/bin/env python3

from flask import Blueprint, Response, render_template, request, session
from ezprobs.geometry import area_circle
from ezprobs.hydraulics import pipe_loss, local_loss
from ezprobs.problems import Parameter, Plot
from ezprobs.units import M, CM, MM, M3PS, KINEMATIC_VISCOSITY, GRAVITY
from io import BytesIO
from math import sqrt
from scipy.optimize import fsolve

import numpy as np
import matplotlib as mpl

mpl.use("Agg")

import matplotlib.pyplot as plt

__author__ = "Richard Pöttler"
__copyright__ = "Copyright (c) 2021 Richard Pöttler"
__license__ = "MIT"
__email__ = "richard.poettler@gmail.com"


bp = Blueprint("pressure_pipe_01", __name__)


def compute_solution():
    d1 = 70 * CM
    d2 = 70 * CM
    d3 = 70 * CM
    ha = 360.0 * M
    hb = 197.2 * M
    h2 = 231.6 * M
    h3 = 260.5 * M
    h4 = 210.45 * M
    l1 = 280 * M
    l2 = 150 * M
    l3 = 350 * M
    k = 0.3 * MM
    nu_entry = 0.5
	
    scale = 1 # over scaling velocity head for better display

    q_initial = 3 * 10 ** -3 * M3PS

    if request.method == "POST":
        d1 = float(request.form["d1"]) * CM
        d2 = float(request.form["d2"]) * CM
        d3 = float(request.form["d3"]) * CM

    a1 = area_circle(d1 / 2)
    a2 = area_circle(d2 / 2)
    a3 = area_circle(d3 / 2)

    q = fsolve(
        lambda q: h4
        + (q / a3) ** 2 / (2 * GRAVITY)
        + local_loss(nu_entry, a1, q)
        + pipe_loss(l1, a1, k, d1, q)
        + pipe_loss(l2, a2, k, d2, q)
        + pipe_loss(l3, a3, k, d3, q)
        - ha,
        1,
    )[0]

    v1 = q / a1
    v2 = q / a2
    v3 = q / a3

    #x2 = sqrt(l1 ** 2 - (ha - h2) ** 2)
    #x3 = sqrt(l2 ** 2 - (h2 - h3) ** 2)
    #x4 = sqrt(l3 ** 2 - (h3 - h4) ** 2)
    #distances = np.array([0, x2, 0, x3, 0, x4])
    distances = np.array([0, l1, 0, l2, 0, l3])

    x = np.cumsum(distances)
    pipe = np.array([ha-10, h2, h2, h3, h3, h4])
    energy_horizon = np.full((len(x)), ha)
    losses = np.array(
        [
            local_loss(nu_entry, a1, q),
            pipe_loss(l1, a1, k, d1, q),
            0,
            pipe_loss(l2, a2, k, d2, q),
            0,
            pipe_loss(l3, a3, k, d3, q),
        ]
    )
    cum_losses = np.cumsum(losses)
    energy_line = energy_horizon - cum_losses
    energy_line[0] = energy_horizon[0]-scale*cum_losses[0] # for display
    kinetic_energy = np.array([v1, v1, v2, v2, v3, v3]) ** 2 / (2 * GRAVITY)
    pressure_line = energy_line - kinetic_energy
    #pressure_line = energy_line - scale*kinetic_energy # for display

    return {
        "d1": d1,
        "d2": d2,
        "d3": d3,
        "discharge": q,
        "x": x.tolist(),
        "pipe": pipe.tolist(),
        "energy_horizon": energy_horizon.tolist(),
        "energy_line": energy_line.tolist(),
        "pressure_line": pressure_line.tolist(),
    }


@bp.route("/", methods=["POST", "GET"])
def index():
    solution = compute_solution()
    session["solution"] = solution

    parameters = [
        Parameter(
            "d1",
            "d1",
            70,
            90,
            2,
            solution["d1"] / CM,
            unit="cm",
            description="Diameter of the pipe between I and II",
        ),
        Parameter(
            "d2",
            "d2",
            70,
            90,
            2,
            solution["d2"] / CM,
            unit="cm",
            description="Diameter of the pipe between II and III",
        ),
        Parameter(
            "d3",
            "d3",
            70,
            90,
            2,
            solution["d3"] / CM,
            unit="cm",
            description="Diameter of the pipe between III and VI",
        ),
    ]

    plot = Plot("plot", alt="plot", caption="Energy- and pressure lines")

    return render_template(
        "problems/pressure_pipe_01.html",
        plot=plot,
        parameters=parameters,
        solution=solution,
    )


@bp.route("/plot")
def plot_function():
    ha = 360.0 * M
    hb = 197.2 * M
    h2 = 231.6 * M
    h3 = 260.5 * M
    h4 = 210.45 * M
	
    x = session["solution"]["x"]
    pipe = session["solution"]["pipe"]
    energy_horizon = session["solution"]["energy_horizon"]
    energy_line = session["solution"]["energy_line"]
    pressure_line = session["solution"]["pressure_line"]

    #xticks = np.array([0, l1, l1+l2, l1+l2+l3])
    #xticks = np.array([])
    xticks = np.array([0, x[5]])
    yticks = np.sort(np.array([ha, h2, h3, h4]))
	
    fig, ax = plt.subplots()
    ax.set_frame_on(False)
    ax.set_xticks(xticks)
    ax.set_xticklabels(['A','B'])
    #ax.set_yticks(yticks)
	
    ax.plot(x, energy_horizon, label="Energy Horizon", color="red", linestyle="dashdot", lw=1)
    ax.plot(x, energy_line, label="Energy Line", color="red", lw=1.5)
    ax.plot(x, pressure_line, label="Pressure Line", color="blue", linestyle="dashed", lw=1.5)
    ax.plot(x, pipe, label="Pipe Axis", color="black", linestyle="dashdot", lw=1)
	
	# plot reservoirs
    ax.plot(np.array([-50, 0]), np.array([ha, ha]), color="blue", lw=1.5)
    ax.plot(np.array([x[5], x[5]+50]), np.array([hb, hb]), color="blue", lw=1.5)
    ax.fill_between(np.array([-50, 0]), np.array([ha, ha]), np.array([ha, ha])-20, color="b", alpha=0.1)
    ax.fill_between(np.array([x[5], x[5]+50]), np.array([hb, hb]), np.array([hb, hb])-20, color="b", alpha=0.1)

	# add labels 
    ax.text(x[0],ha-10,'I ',ha="right")
    ax.text(x[1],h2,'II', va='top', ha='center')
    ax.text(x[3],h3,'III', va='bottom', ha='center')
    ax.text(x[5],h4,' IV')
	
    ax.grid(axis='x')
    ax.legend()
    ax.legend(loc='upper center', bbox_to_anchor=(0.5, -0.05),
          fancybox=True, shadow=True, ncol=4)
    #ax.set_xlabel("Distance [m]")
    ax.set_ylabel("Height [m.a.s.l.]")
    #ax.set_title("Pressure- and Energyline")

    buffer = BytesIO()
    fig.savefig(buffer, format="png", bbox_inch="tight")
    plt.close(fig)
    return Response(buffer.getvalue(), mimetype="image/png")


@bp.route("/ajax", methods=["POST", "GET"])
def ajax():
    solution = compute_solution()
    session["solution"] = solution

    return render_template(
        "problems/pressure_pipe_01_solution.html",
        solution=solution,
    )
