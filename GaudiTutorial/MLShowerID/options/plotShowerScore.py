#!/usr/bin/env python3
"""Compare electron and pion cluster ID scores stored in EDM4hep files."""

import argparse
import math
import os
from pathlib import Path

# Run without opening a ROOT window on remote machines.
os.environ["ROOT_WEBDISPLAY"] = "off"

import podio
import ROOT


def read_histograms(input_file, sample, collection):
    histograms = []
    for index, score_name in enumerate(("EM score", "Hadronic score")):
        histogram = ROOT.TH1D(
            f"h_{sample}_shape_parameter_{index}",
            f";{score_name}",
            50, 0.0, 1.0,
        )
        histogram.SetStats(0)
        histogram.Sumw2()
        histograms.append(histogram)

    reader = podio.root_io.Reader(str(input_file))
    for event in reader.get("events"):
        clusters = event.get(collection)
        for cluster in clusters:
            parameters = cluster.getShapeParameters()
            histograms[0].Fill(parameters[0])
            histograms[1].Fill(parameters[1])

    return histograms


def main():
    ROOT.gROOT.SetBatch(True)
    electron = read_histograms("mlshowerid_output_e-_1-20GeV.root", "electron", "MLShowerIDClusters")
    pion = read_histograms("mlshowerid_output_pi-_1-20GeV.root", "pion", "MLShowerIDClusters")
    shapeParam_name = ["EM_score", "Hadronic_score"]

    for index in range(2):
        electron[index].SetLineColor(ROOT.kBlue)
        electron[index].SetLineWidth(3)
        pion[index].SetLineColor(ROOT.kRed)
        pion[index].SetLineWidth(3)

        canvas = ROOT.TCanvas(f"canvas_shape_parameter_{index}", "Cluster ID scores", 900, 650)
        canvas.SetLeftMargin(0.13)
        canvas.SetBottomMargin(0.13)
        canvas.SetGridy()
        electron[index].SetMinimum(0.0)
        electron[index].SetMaximum(1.25 * max(electron[index].GetMaximum(), pion[index].GetMaximum()))
        electron[index].Draw("HIST")
        pion[index].Draw("HIST SAME")

        legend = ROOT.TLegend(0.35, 0.73, 0.68, 0.88)
        legend.SetBorderSize(0)
        legend.AddEntry(electron[index], "e^{-}, 1-20 GeV", "l")
        legend.AddEntry(pion[index], "#pi^{-}, 1-20 GeV", "l")
        legend.Draw()

        canvas.SaveAs(f"MLshowerID_{shapeParam_name[index]}.png")


if __name__ == "__main__":
    main()
