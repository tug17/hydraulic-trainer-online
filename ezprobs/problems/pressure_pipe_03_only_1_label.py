#!/usr/bin/env python3

from flask import Blueprint, Response, render_template, request, session
from ezprobs.geometry import area_circle
from ezprobs.hydraulics import pipe_loss, local_loss ,calculate_lambda
from ezprobs.problems import Parameter, Plot
from ezprobs.units import M, CM, MM, M3PS, KINEMATIC_VISCOSITY, GRAVITY
from ezprobs.dict import DICT_GER, DICT_ENG
from io import BytesIO
from math import sqrt, pi
from scipy.optimize import fsolve

import numpy as np
import matplotlib as mpl

mpl.use("Agg")

import matplotlib.pyplot as plt
    
__author__ = "Alexander Wiehn & Manuel Pirker"
__copyright__ = "Copyright (c) 2022 Alexander Wiehn & Manuel Pirker"
__license__ = ""
__email__ = "alexander.wiehn@tugraz.at"


bp = Blueprint("pressure_pipe_03", __name__)


def compute_solution():
    d = 1.2
    zheta = 0.15
    l_1 = 120
    l_2 = 200
    k = 0.02
    h_o = 250
    h_u = 150
    efficiency_turbine = 0.9
    efficiency_pump = 0.9
    vis = 1.31e-6
    g = 9.81 

    scale = 1 # over scaling velocity head for better display

    q = 0 * 10 ** -3 * M3PS

    if request.method == "POST":
        q = float(request.form["q"]) * M3PS

    if q > 0:
        v = q*4/(d*d*pi)
        lambda_1 = calculate_lambda(v,k,d,vis)
        height = h_o - h_u - pow(v,2)/(2*g)*(zheta+lambda_1*(l_1+l_2)/d +1)
        power = efficiency_turbine*9810*q*height/1000
        roundpower = round(power,2)
        if roundpower > 0: #"´Water from left to right, energy being used in a turbine."
            fd = 0 #flow_direction
            power_turbine = roundpower
            power_pump = 0
            v2 = pow(v,2)
            g2 = 2*g   
            "ex = np.array([0,100,100,300])"
            energy_line = np.array([h_o-v2/g2*(zheta),h_o-v2/g2*(zheta+lambda_1*l_1/d),h_o-v2/g2*(zheta+lambda_1*l_1/d)-height,h_u+v2/g2])
            "prx = np.array([0,100,100,300])"
            pressure_line = np.array([h_o-v2/g2*(zheta+1),h_o-v2/g2*(zheta+lambda_1*l_1/d+1),h_o-v2/g2*(zheta+lambda_1*l_1/d+1)-height,h_u])
        else: #"Water from left to right, further accelerated by a pump."
            fd = 0
            height = abs(height)
            power = 9810*q*height/(1000*efficiency_pump)
            power_pump = round(power,2)
            power_turbine = 0
            v2 = pow(v,2)
            g2 = 2*g
            #"ex = np.array([0,100,100,300])
            energy_line = np.array([h_o-v2/g2*(zheta),h_o-v2/g2*(zheta+lambda_1*l_1/d),h_u+v2/g2*(lambda_1*l_2/d+1),h_u+v2/g2])
            #"prx = np.array([0,100,100,300])
            pressure_line = np.array([h_o-v2/g2*(zheta+1),h_o-v2/g2*(zheta+lambda_1*l_1/d+1),h_u+v2/g2*(lambda_1*l_2/d),h_u])
            
    elif q == 0:
        fd = 0
        power_pump = 0
        power_turbine = 0
        energy_line = np.array([h_o,h_o,h_u,h_u])
        pressure_line = np.array([h_o,h_o,h_u,h_u]) 
        
            
    else: #"Water going from right to left witht the help of a pump."
        fd = np.pi
        q = abs(q)
        v = q*4/(d*d*pi)
        lambda_1 = calculate_lambda(v,k,d,vis)
        height = h_o - h_u + pow(v,2)/(2*g)*(zheta+lambda_1*(l_1+l_2)/d +1)
        power = 9810*q*height/(1000*efficiency_pump)
        power_pump = round(power,2)
        power_turbine = 0   
        v2 = pow(v,2)
        g2 = 2*g
        #"ex = np.array([0,100,100,300])
        energy_line = np.array([h_o+v2/g2,h_o+v2/g2*(lambda_1*l_1/d+1),h_u-v2/g2*(zheta+l_2*lambda_1/d),h_u-v2/g2*(zheta)])
        #"prx = np.array([0,100,100,300])
        pressure_line = np.array([h_o,h_o+v2/g2*(lambda_1*l_1/d),h_u-v2/g2*(zheta+l_2*lambda_1/d+1),h_u-v2/g2*(zheta+1)])

    

    distances = np.array([0, 100, 0, 200])

    x = np.cumsum(distances)
    pipe = np.array([230, 130, 130, 130])
    energy_horizon = np.full((len(x)), h_o)
	



    return {
        "q": q,
        "x": x.tolist(),
        "pipe": pipe.tolist(),
        "energy_horizon": energy_horizon.tolist(),
        "energy_line": energy_line.tolist(),
        "pressure_line": pressure_line.tolist(),
        "power_pump": power_pump,
        "power_turbine": power_turbine,
        "flow_direction": fd,
    }


@bp.route("/", methods=["POST", "GET"])
def index():
    lang = DICT_GER
    
    solution = compute_solution()
    session["solution"] = solution

    parameters = [
        Parameter(
            "q",
            "q",
            -20,
            35,
            5,
            solution["q"] / M3PS,
            unit="M^3PS",
            description=lang["discharge"],
        ),
    ]

    plot = Plot("plot", alt="plot", caption="Energy- and pressure lines")

    return render_template(
        "problems/pressure_pipe_03.html",
        plot=plot,
        parameters=parameters,      
        solution=solution,
    )


@bp.route("/plot")
def plot_function():
    rl = 35 #reservoirs_length
    rh = 3 #reservoirs_extra_height
    h_o = 250
    h_u = 150   
    ha = h_o
    hb = h_u
    hout = 0.5 * M
    d = 1.2
    lang = DICT_GER
	
    x = session["solution"]["x"]
    pipe = session["solution"]["pipe"]
    energy_horizon = session["solution"]["energy_horizon"]
    energy_line = session["solution"]["energy_line"]
    pressure_line = session["solution"]["pressure_line"]
    power_pump = session["solution"]["power_pump"]
    power_turbine = session["solution"]["power_turbine"]
    fd = session["solution"]["flow_direction"]
    

    #xticks = np.array([0, l1, l1+l2, l1+l2+l3])
    #xticks = np.array([])
    #xticks = np.array([-.50, 0, x[-1], x[-1]+.50])
    #yticks = np.sort(np.array([ha, hout, hb, 175]))
	
    fig, ax = plt.subplots(figsize=(9,5))
    ax.set_frame_on(False)
    #ax.set_xticks(xticks)
    #ax.set_xticklabels([' ','A','B',' '])
    #ax.set_yticks(yticks)

	
    ax.plot(x, energy_horizon, label=lang["ehorizont_l"], color="red", linestyle="dashdot", lw=1)
    ax.plot(x, energy_line, label=lang["eline_l"], color="red", lw=1.5)
    ax.plot(x, pressure_line, label=lang["pline_l"], color="blue", linestyle="dashed", lw=1.5)
    ax.plot(x, pipe, label=lang["paxis"], color="black", linestyle="dashd""ot", lw=1)
    ax.plot(x, np.array(pipe)+d/2, color="grey", linestyle="-", lw=0.5)
    ax.plot(x,  np.array(pipe)-d/2, color="grey", linestyle="-", lw=0.5)
    
	# plot reservoirs
    ax.plot(np.array([-rl, 0]), np.array([ha, ha]), color="blue", lw=1.5)
    ax.plot(np.array([x[-1], x[-1]+rl]), np.array([hb, hb]), color="blue", lw=1.5)
    ax.fill_between(np.array([-rl, 0]), np.array([ha, ha]), np.array([230, 230]), color="b", alpha=0.1)
    ax.fill_between(np.array([x[-1], x[-1]+rl]), np.array([hb, hb]), np.array([130, 130]), color="b", alpha=0.1)
    
    ax.plot(np.array([-rl, -rl, 0, 0]), np.array([ha+rh, 230, 230, ha+rh]), color="k", lw=1.5)
    ax.plot(np.array([x[-1], x[-1], x[-1]+rl, x[-1]+rl]), np.array([hb+rh, 130, 130, hb+rh]), color="k", lw=1.5)
    
    plt.title(f'Turbinenleistung:{power_turbine/1000: 6.2f} MW \nPumpenleistung:{power_pump/1000: 6.2f} MW')
    ax.text(x[-1], ha, lang["ehorizont_s"], ha='right', va="bottom")
    pos_EL = np.mean(energy_line)
    pos_PL = np.mean(pressure_line)
    diff = abs(pos_EL-pos_PL)
    if diff < 10:
        ax.text(x[-1]/2, np.mean(energy_line), lang["eline_s"], ha='left', va="bottom", color="red")
        ax.text(x[-1]/2, np.mean(pressure_line)-10, lang["pline_s"], ha='left', va="bottom", color="blue")
    else:
        ax.text(x[-1]/2, np.mean(energy_line), lang["eline_s"], ha='left', va="bottom", color="red")
        ax.text(x[-1]/2, np.mean(pressure_line), lang["pline_s"], ha='left', va="bottom", color="blue")
    ax.text(0, ha-30, f"DN{int(d*1000)} ", ha='right', va="center")
    phi = np.linspace(0, 2*np.pi, 50)
    x_circle = 10*np.sin(phi)
    y_circle = 10*np.cos(phi)
    ax.plot(100+x_circle, 130+y_circle, color="k")
    phi = np.array([np.pi/2,-np.pi/6,7*np.pi/6,np.pi/2]) + fd
    x_triangle = 10*np.sin(phi)
    y_triangle = 10*np.cos(phi)
    ax.plot(100+x_triangle, 130+y_triangle, color="k")
    
	# add labels 
    #ax.text(x[0],ha-10,'I ',ha="right")
    #ax.text(x[1],h2,'II', va='top', ha='center')
    #ax.text(x[3],h3,'III', va='bottom', ha='center')
    #ax.text(x[5],h4,' IV')
	
    ax.grid(axis='x')
    #ax.legend()
    ax.set_xlim((-40,x[-1]+40))
    ax.set_ylim((100,300))
    plt.axis("equal")
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
        "problems/pressure_pipe_03_solution.html",
        solution=solution,
    )
