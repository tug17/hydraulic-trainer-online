#!/usr/bin/env python3

from flask import Blueprint, Response, render_template, request, session
from ezprobs.hydraulics import (
    t_n_rect,
    t_crit_rect,
    l_transition_i_r_rect,
    depth_bernoulli_upstream,
    depth_bernoulli_downstream,
    froude,
)

from ezprobs.problems import Parameter, Plot
from ezprobs.units import M, S, M3PS, GRAVITY, PERMILLE
from ezprobs.dict import DICT_GER, DICT_ENG

from io import BytesIO
from math import sqrt

import numpy as np
import matplotlib as mpl


mpl.use("Agg")

import matplotlib.pyplot as plt

__author__ = "Manuel Pirker"
__copyright__ = "Copyright (c) 2021 Manuel Pirkerr"
__license__ = "MIT"
__email__ = "manuel.pirker@tugraz.at"


bp = Blueprint("free_surface_01", __name__)


def compute_solution():
    w = 30 * M
    q = 150 * M3PS
    iso = 8 * PERMILLE

    ks = 40 * M ** (1 / 3) / S

    if request.method == "POST":
        ks = int(request.form["ks"]) * M ** (1 / 3) / S
        iso = float(request.form["iso"]) * PERMILLE
        q = int(request.form["q"]) * M3PS

    t_crit = t_crit_rect(q, w)
    t_n = t_n_rect(q, ks, iso, w)

    return {
        "iso": iso,
        "w": w,
        "q": q,
        "t_crit": t_crit,
        "t_n": t_n,
        "ks": ks,
    }


@bp.route("/", methods=["POST", "GET"])
def index():
    lang = DICT_GER
    
    solution = compute_solution()
    session["solution"] = solution

    parameters = [
        Parameter(
            "ks",
            "kst",
            15,
            85,
            5,
            solution["ks"],
            unit="m^{1/3}/s",
            description=lang["kst_river"],
        ),
        Parameter(
            "iso",
            "iso",
            5,
            12,
            0.5,
            solution["iso"] / PERMILLE,
            unit="\\unicode{0x2030}",
            description=lang["iso"],
        ),
        Parameter(
            "q",
            "q",
            100,
            200,
            5,
            solution["q"] / M3PS,
            unit="m^3/s",
            description=lang["discharge"],
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
    lang = DICT_GER
    
    ## load values  -----------------------------------------------------------
    iso = session["solution"]["iso"]
    w = session["solution"]["w"]
    q = session["solution"]["q"]
    t_crit = session["solution"]["t_crit"]
    t_n = session["solution"]["t_n"]
    # ks = session["solution"]["ks"]
    
    v = q/(t_n*w)
    fr = v/np.sqrt(GRAVITY*t_n)

    if np.round(t_crit,1) == np.round(t_n,1):
        strFlow = lang["crit"]
        t_n = t_crit
        fr=1
        
    elif t_crit < t_n:
        strFlow = lang["sub_l"]
    else:
        strFlow = lang["super_l"]
    ## begin calculation  -----------------------------------------------------
    # define plot size
    x_min = -50 * M
    x_max = 0 * M
    y_min = -1 * M
    y_max = 5 * M

    xlabels = []
    xticks = []
    
    
    xx = np.array([x_min, x_max])
    so = -xx*iso
    head = (q / (w * t_n)) ** 2 / (2 * GRAVITY)
	
	
    ## begin plotting sequence ------------------------------------------------
    fig, ax = plt.subplots(1,2,figsize=(9,5))
    ax[0].fill_between(xx, so, so + t_n, color="b", alpha=0.1)
    ax[0].fill_between(xx, so, so - 0.5, color="k", alpha=0.1)

    # plot the sole
    ax[0].plot([x_min, x_max], [x_min * -iso, x_max * -iso], "k", lw=1.5)

    #ax.plot(xx, so + t_crit, "k:", label="Krit. Wassertiefe", lw=1.5)
    #ax.plot(xx, so + depth, "b", label="Wasserspiegel", lw=1.5)
    #ax.plot(head_xx, head_so + head_depth + head, "r--", label="Energielinie", lw=1.5)

    ax[0].plot(xx, so + t_crit, "k:", label=lang["tcrit"], lw=2)
    ax[0].plot(xx, so + t_n, "b", label=lang["wline_l"], lw=1.5)
    ax[0].plot(xx, so + t_n + head, "r--", label=lang["eline_l"], lw=1.5)
    
    ax[0].text(np.mean(xx), y_max, f"Fr = {fr:3.2f}", va="top", ha="center", weight="bold")

    ax[0].set_title(f"{strFlow}", 
        fontsize=12, 
        fontweight="bold",
        fontstyle="italic")
    ## figure style settings --------------------------------------------------
    ax[0].set_frame_on(False)
    ax[0].xaxis.grid()
    ax[0].set_xlim((x_min,x_max)) # keep x=0 in center of plot
    #ax.set_xlim(x_min, x_max)
    ax[0].set_xticks(xticks)
    ax[0].set_xticklabels(xlabels)

    ax[0].axhline(y=-x_min * iso + t_n + head, color="k", lw=0.5, alpha=0.4)
    ax[0].axhline(y=-x_max * iso, color="k", lw=0.5, alpha=0.4)
    ax[0].set_ylim(y_min, y_max)
    ax[0].set_yticks(
        [
            -x_max * iso,
            -x_min * iso,
            -x_min * iso + t_crit,
            -x_min * iso + t_n + head,
        ]
    )
    #ax.set_yticklabels(["$B.H.$", "$Sohle$", "$W.L.$", "$E.H.$"])
    ax[0].set_yticklabels([lang["href_s"], lang["bed"], "$t_{crit}$", lang["ehorizont_s"]])

    secax = ax[0].secondary_yaxis("right")
    secax.set_yticks(
        np.sort([
            -x_max * iso,
            -x_max * iso + t_n,
            -x_max * iso + t_n + head,
        ])
    )
    #secax.set_yticklabels(["$B.H.$", "$W.L.$", "$E.L.$", "$E.H.$"])
    if np.round(t_crit,1) == np.round(t_n,1):
        secax.set_yticklabels([lang["href_s"], "$t = t_{crit}$", lang["eline_s"]])
    else:
        secax.set_yticklabels([lang["href_s"], "$t = t_N$", lang["eline_s"]])
    

    secax.spines["right"].set_visible(False)
    ax[0].spines["right"].set_visible(False)

    #ax.legend(loc="right")
    ax[0].legend(loc='upper center', bbox_to_anchor=(0.5, -0.05),
          fancybox=True, shadow=True, ncol=3)
    
    ## second axes diagram
    xx = np.linspace(0.001,10, 100)
    xx1 = np.linspace(0.001,t_crit, 50)
    xx2 = np.linspace(t_crit,10, 50)
    heads = (q / (w * xx)) ** 2 / (2 * GRAVITY)
    heads1 = (q / (w * xx1)) ** 2 / (2 * GRAVITY)
    heads2 = (q / (w * xx2)) ** 2 / (2 * GRAVITY)
    crit_head = (q / (w * t_crit)) ** 2 / (2 * GRAVITY)
    
    ax[1].plot(xx + heads, xx, color='k', lw=2)
    ax[1].fill_betweenx( xx1, xx1 + heads1, color='g', alpha=0.15)
    ax[1].fill_betweenx( xx2, xx2 + heads2, color='r', alpha=0.15)
    ax[1].fill_betweenx( [0,-0.5], [5,5], color='k', alpha=0.1)
    ax[1].plot(xx, xx, color='k', lw=1.5, ls='--')
    ax[1].plot([0, 5], [t_crit, t_crit], color='k', lw=2, ls=':')
    ax[1].plot([0, t_n], [t_n, t_n], color='b', lw=2, label=lang["wlvl"])
    ax[1].plot([t_n, t_n+head], [t_n, t_n], color='r', lw=2, label=lang["vlvl"])
    
    ax[1].text(1,0.5,lang["super_s"], color='grey', size=12, style="italic", weight='bold')
    ax[1].text(1,3,lang["sub_s"], color='grey', size=12, style="italic", weight='bold')
    
    ax[1].axis("equal")
    ax[1].set_xlim((0,5))
    ax[1].set_ylim(ax[0].get_ylim())
    ax[1].set_frame_on(False)
    ax[1].set_xticks(np.sort([
            0,
            t_crit + crit_head,
        ]))
    ax[1].set_xticklabels(["0","$H_{min}$"])
    ax[1].set_yticks(np.sort([
            -x_max * iso,
            -x_max * iso + t_n,
        ]))
    ax[1].set_yticklabels([" "," "])
    ax[1].xaxis.grid()
    ax[1].yaxis.grid()
    ax[1].set_xlabel(lang["ehead"])
    ax[1].set_title(f"q={q:4.1f} $m^3/s$")
    
    ax[1].legend(loc='upper left',
        fancybox=True, shadow=True, ncol=1)
    
    ## cache figure -----------------------------------------------------------
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
