#!/usr/bin/env python3

from svgwrite import Drawing, cm, mm
from flask import Response, Blueprint
from io import BytesIO

import matplotlib as mpl

mpl.use("Agg")
# mpl.use("SVG")

import matplotlib.pyplot as plt


__author__ = "Richard Pöttler"
__copyright__ = "Copyright (c) 2021 Richard Pöttler"
__license__ = "MIT"
__email__ = "richard.poettler@gmail.com"


bp = Blueprint("demo", __name__)


@bp.route("/mpl")
def display_matplotlib():
    fig, ax = plt.subplots()
    ax.plot(range(10))

    buffer = BytesIO()
    # fig.savefig(buffer, format="svg")
    # return Response(buffer.getvalue(), mimetype="image/svg+xml")
    fig.savefig(buffer, format="png")
    return Response(buffer.getvalue(), mimetype="image/png")


@bp.route("/svg")
def display_svg():
    dwg = Drawing()
    hlines = dwg.add(dwg.g(id="hlines", stroke="green"))
    for y in range(20):
        hlines.add(dwg.line(start=(2 * cm, (2 + y) * cm), end=(18 * cm, (2 + y) * cm)))
    vlines = dwg.add(dwg.g(id="vline", stroke="blue"))
    for x in range(17):
        vlines.add(dwg.line(start=((2 + x) * cm, 2 * cm), end=((2 + x) * cm, 21 * cm)))
    shapes = dwg.add(dwg.g(id="shapes", fill="red"))

    # set presentation attributes at object creation as SVG-Attributes
    circle = dwg.circle(
        center=(15 * cm, 8 * cm), r="2.5cm", stroke="blue", stroke_width=3
    )
    circle["class"] = "class1 class2"
    shapes.add(circle)

    # override the 'fill' attribute of the parent group 'shapes'
    shapes.add(
        dwg.rect(
            insert=(5 * cm, 5 * cm),
            size=(45 * mm, 45 * mm),
            fill="blue",
            stroke="red",
            stroke_width=3,
        )
    )

    # or set presentation attributes by helper functions of the Presentation-Mixin
    ellipse = shapes.add(dwg.ellipse(center=(10 * cm, 15 * cm), r=("5cm", "10mm")))
    ellipse.fill("green", opacity=0.5).stroke("black", width=5).dasharray([20, 20])

    return Response(dwg.tostring(), mimetype="image/svg+xml")
