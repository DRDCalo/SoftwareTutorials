#!/usr/bin/env python3
"""Overlay stored electron cluster scores and inference from the original sample.

Use the first N input events, where N is the number of events in the output
file (runMLShowerID.py starts at entry zero). Input preparation follows
modeldev/pointnet_util.py:read_simplecalo, used by evaluate_pointnet_simplecalo.py.
"""

import argparse
import os
from pathlib import Path

os.environ["ROOT_WEBDISPLAY"] = "off"

import numpy as np
import onnxruntime as ort
import podio
import ROOT
import uproot


def read_stored_scores(path):
    reader = podio.root_io.Reader(str(path))
    scores = []
    for event in reader.get("events"):
        clusters = event.get("MLShowerIDClusters")
        parameters = clusters[0].getShapeParameters()
        scores.append([parameters[0], parameters[1]])
    return np.asarray(scores, dtype=np.float32)


def infer_scores(input_path, model_path, n_events):
    options = ort.SessionOptions()
    options.intra_op_num_threads = 1
    options.graph_optimization_level = ort.GraphOptimizationLevel.ORT_ENABLE_BASIC
    session = ort.InferenceSession(
        str(model_path), sess_options=options, providers=["CPUExecutionProvider"]
    )
    inputs = {item.name: item for item in session.get_inputs()}
    max_points = inputs["points"].shape[1]
    branches = [f"simplecaloRO/simplecaloRO.{field}" for field in
                ("energy", "position.x", "position.y", "position.z")]
    with uproot.open(input_path) as root_file:
        tree = root_file["events"]
        if tree.num_entries < n_events:
            raise ValueError("The original sample has fewer events than the output sample")
        arrays = tree.arrays(branches, entry_stop=n_events, library="np")

    scores = np.empty((n_events, 2), dtype=np.float32)
    for index in range(n_events):
        energy, x, y, z = [np.asarray(arrays[name][index], dtype=np.float32)
                           for name in branches]
        # Match MLShowerIDSolution's empty-shower fallback.
        if len(energy) == 0:
            scores[index] = (0.5, 0.5)
            continue
        order = np.argsort(energy)[::-1][:max_points]
        selected = np.stack((x[order], y[order], z[order], energy[order]), axis=1)
        points = np.zeros((1, max_points, 4), dtype=np.float32)
        mask = np.zeros((1, max_points), dtype=np.bool_)
        points[0, :len(order)] = selected
        mask[0, :len(order)] = True
        # Feed raw mm/GeV values: normalization and softmax are embedded in ONNX.
        result = session.run(["scores"], {"points": points, "mask": mask})[0]
        scores[index] = result[0]
    return scores


def plot_scores(stored, inferred):
    for index, name in enumerate(("EM_score", "Hadronic_score")):
        histograms = []
        for sample, values, color, style in (
            ("stored", stored, ROOT.kBlue, 1),
            ("onnx", inferred, ROOT.kRed, 2),
        ):
            histogram = ROOT.TH1D(
                f"h_{sample}_shape_parameter_{index}",
                f";{name.replace('_', ' ')}", 50, 0.0, 1.0,
            )
            histogram.SetDirectory(0)
            histogram.SetStats(0)
            histogram.Sumw2()
            histogram.SetLineColor(color)
            histogram.SetLineWidth(3)
            histogram.SetLineStyle(style)
            for score in values[:, index]:
                histogram.Fill(float(score))
            histograms.append(histogram)
        canvas = ROOT.TCanvas(f"canvas_compare_{index}", "Cluster ID score comparison", 900, 650)
        canvas.SetLeftMargin(0.13)
        canvas.SetBottomMargin(0.13)
        canvas.SetGridy()
        histograms[0].SetMinimum(0.0)
        histograms[0].SetMaximum(1.25 * max(h.GetMaximum() for h in histograms))
        histograms[0].Draw("HIST")
        histograms[1].Draw("HIST SAME")
        legend = ROOT.TLegend(0.32, 0.73, 0.76, 0.88)
        legend.SetBorderSize(0)
        legend.AddEntry(histograms[0], "Stored cluster shape parameter", "l")
        legend.AddEntry(histograms[1], "ONNX inference (original e^{-} sample)", "l")
        legend.Draw()
        canvas.SaveAs(f"compareShowerScore_{name}.png")


def main():
    ROOT.gROOT.SetBatch(True)

    model = "../../data/pointnet_simplecalo.onnx"
    stored = read_stored_scores("mlshowerid_output_e-_1-20GeV.root")
    inferred = infer_scores("../../data/clusterID_e-_1-20GeV_eval.root", model, len(stored))

    print(f"Comparing {len(stored)} output events with the first {len(stored)} input events")
    plot_scores(stored, inferred)


if __name__ == "__main__":
    main()
