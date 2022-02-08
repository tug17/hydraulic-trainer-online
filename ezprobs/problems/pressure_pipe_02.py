#!/usr/bin/env python3

from flask import Blueprint, Response, render_template, request, session
from ezprobs.geometry import area_circle
from ezprobs.hydraulics import pipe_loss, local_loss
from ezprobs.problems import Parameter, Plot
from ezprobs.units import M, CM, MM, M3PS, KINEMATIC_VISCOSITY, GRAVITY
from ezprobs.dict import DICT_GER, DICT_ENG
from io import BytesIO
from math import sqrt
from scipy.optimize import fsolve

import numpy as np
import matplotlib as mpl

mpl.use("Agg")

import matplotlib.pyplot as plt

__author__ = "Manuel Pirker"
__copyright__ = "Copyright (c) 2021 Manuel Pirker"
__license__ = "MIT"
__email__ = "manuel.pirker@tugraz.at"


bp = Blueprint("pressure_pipe_02", __name__)


def compute_solution():
    d = 5 * CM
    ha = 150 * CM
    hb = 20 * CM
    hout = 30 * CM
    l = 2 * M
    k = 0.3 * MM
    nu_entry = 0.5
	
    scale = 1 # over scaling velocity head for better display

    q_initial = 3 * 10 ** -3 * M3PS

    if request.method == "POST":
        d = float(request.form["d"]) * MM
        hb = float(request.form["hb"]) * CM

    a = area_circle(d / 2)
    
    
    if hb == ha:
        q = 0
    elif hb < hout:
        q = fsolve(
            lambda q: hout
            + (q / a) ** 2 / (2 * GRAVITY)
            + local_loss(nu_entry, a, q)
            + pipe_loss(l, a, k, d, q)
            - ha,
            1,
        )[0]
    else:
        q = fsolve(
            lambda q: hb
            + (q / a) ** 2 / (2 * GRAVITY)
            + local_loss(nu_entry, a, q)
            + pipe_loss(l, a, k, d, q)
            - ha,
            1,
        )[0]
	

    v = q / a

    distances = np.array([0, l])

    x = np.cumsum(distances)
    pipe = np.array([ha-0.85, hout])
    energy_horizon = np.full((len(x)), ha)
	
    if hb == ha:
        losses = np.array([0, 0])
    else:
        losses = np.array(
            [
                local_loss(nu_entry, a, q),
                pipe_loss(l, a, k, d, q),
            ]
        )
    cum_losses = np.cumsum(losses)
    energy_line = energy_horizon - cum_losses
    energy_line[0] = energy_horizon[0]-scale*cum_losses[0] # for display
    kinetic_energy = np.array([v, v]) ** 2 / (2 * GRAVITY)
    pressure_line = energy_line - kinetic_energy
    #pressure_line = energy_line - scale*kinetic_energy # for display

    return {
        "d": d,
        "hb": hb,
        "discharge": q,
        "x": x.tolist(),
        "pipe": pipe.tolist(),
        "energy_horizon": energy_horizon.tolist(),
        "energy_line": energy_line.tolist(),
        "pressure_line": pressure_line.tolist(),
    }


@bp.route("/", methods=["POST", "GET"])
def index():
    lang = DICT_GER
    
    solution = compute_solution()
    session["solution"] = solution

    parameters = [
        Parameter(
            "d",
            "d",
            10,
            120,
            5,
            solution["d"] / MM,
            unit="mm",
            description=lang["dia_pipe"],
        ),
        Parameter(
            "hb",
            "hb",
            10,
            160,
            5,
            solution["hb"] / CM,
            unit="cm",
            description=lang["wlvl_basin"]+" B",
        ),
    ]

    plot = Plot("plot", alt="plot", caption="Energy- and pressure lines")

    return render_template(
        "problems/pressure_pipe_02.html",
        plot=plot,
        parameters=parameters,
        solution=solution,
    )


@bp.route("/plot")
def plot_function():
    ha = 1.5 * M
    hout = 0.5 * M
    lang = DICT_GER
	
    x = session["solution"]["x"]
    d = session["solution"]["d"]
    hb = session["solution"]["hb"]
    pipe = session["solution"]["pipe"]
    energy_horizon = session["solution"]["energy_horizon"]
    energy_line = session["solution"]["energy_line"]
    pressure_line = session["solution"]["pressure_line"]

    #xticks = np.array([0, l1, l1+l2, l1+l2+l3])
    #xticks = np.array([])
    xticks = np.array([-.50, 0, x[-1], x[-1]+.50])
    #yticks = np.sort(np.array([ha, hout, hb, 175]))
	
    fig, ax = plt.subplots(figsize=(9,5))
    ax.set_frame_on(False)
    ax.set_xticks(xticks)
    ax.set_xticklabels([' ','A','B',' '])
    #ax.set_yticks(yticks)
	
    ax.plot(x, energy_horizon, label=lang["ehorizont_l"], color="red", linestyle="dashdot", lw=1)
    ax.plot(x, energy_line, label=lang["eline_l"], color="red", lw=1.5)
    ax.plot(x, pressure_line, label=lang["pline_l"], color="blue", linestyle="dashed", lw=1.5)
    ax.plot(x, pipe, label=lang["paxis"], color="black", linestyle="dashdot", lw=1)
    ax.plot(x, np.array(pipe)+d/2, color="grey", linestyle="-", lw=0.5)
    ax.plot(x,  np.array(pipe)-d/2, color="grey", linestyle="-", lw=0.5)
	
	# plot reservoirs
    ax.plot(np.array([-.50, 0]), np.array([ha, ha]), color="blue", lw=1.5)
    ax.plot(np.array([x[-1], x[-1]+.50]), np.array([hb, hb]), color="blue", lw=1.5)
    ax.fill_between(np.array([-.50, 0]), np.array([ha, ha]), np.array([0, 0]), color="b", alpha=0.1)
    ax.fill_between(np.array([x[-1], x[-1]+.50]), np.array([hb, hb]), np.array([0, 0]), color="b", alpha=0.1)
    
    ax.plot(np.array([-.50, -.50, 0, 0]), np.array([ha+.3, 0, 0, ha+.3]), color="k", lw=1.5)
    ax.plot(np.array([x[-1], x[-1], x[-1]+.50, x[-1]+.50]), np.array([ha+.3, 0, 0, ha+.3]), color="k", lw=1.5)

    ax.text(x[-1], ha, lang["ehorizont_s"], ha='right', va="bottom")
    ax.text(x[-1]/2, np.mean(energy_line), lang["eline_s"], ha='left', va="bottom", color="red")
    ax.text(x[-1]/2, np.mean(pressure_line), lang["pline_s"], ha='left', va="bottom", color="blue")
    ax.text(0, ha-0.85, f"DN{int(d*1000)} ", ha='right', va="center")
    
	# add labels 
    #ax.text(x[0],ha-10,'I ',ha="right")
    #ax.text(x[1],h2,'II', va='top', ha='center')
    #ax.text(x[3],h3,'III', va='bottom', ha='center')
    #ax.text(x[5],h4,' IV')
	
    ax.grid(axis='x')
    #ax.legend()
    ax.set_xlim((-.51,x[-1]+.51))
    ax.set_ylim((-0.01,1.6))
    ax.legend(loc='upper center', bbox_to_anchor=(0.5, -0.05),
          fancybox=True, shadow=True, ncol=4)
    #ax.set_xlabel("Distance [m]")
    ax.set_ylabel(lang["height"]+" [m]")
    #ax.set_title("Pressure- and Energyline")
    
    
    secax = ax.secondary_yaxis("right")
    secax.spines["right"].set_visible(False)

    buffer = BytesIO()
    fig.savefig(buffer, format="png")
    plt.close(fig)
    return Response(buffer.getvalue(), mimetype="image/png")


@bp.route("/ajax", methods=["POST", "GET"])
def ajax():
    solution = compute_solution()
    session["solution"] = solution

    return render_template(
        "problems/pressure_pipe_02_solution.html",
        solution=solution,
    )
