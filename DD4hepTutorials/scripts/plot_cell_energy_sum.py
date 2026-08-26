#
# Copyright (c) 2020-2024 Key4hep-Project.
#
# This file is part of Key4hep.
# See https://key4hep.github.io/key4hep-doc/ for further info.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
import argparse
import os

import ROOT
# prevent ROOT to display things on the flight
ROOT.gROOT.SetBatch(ROOT.kTRUE)
from podio import root_io

parser = argparse.ArgumentParser()
parser.add_argument("input_file", type=str, help="Path to the input file")
parser.add_argument("-o", "--output", type=str, default=None,
                    help="Where to write the plot (default: next to the input file)")
args = parser.parse_args()

# Use the podio reader to open the file (it could also be opened with plain ROOT but that would not preserve the podio functionalities)
reader = root_io.Reader(args.input_file)

# Collect the per-event cell energy sums first, so that the histogram range can be
# taken from the data: the energy scale depends on the sampling fraction, which you
# are invited to change in Hands-on 3.
total_energies = []
for event in reader.get("events"):
    calo_cells = event.get("simplecaloRO")
    total_energies.append(sum([calo_cell.getEnergy() for calo_cell in calo_cells]))

if not total_energies:
    raise SystemExit(f"No events found in {args.input_file}")

# Prepare a ROOT TH1 to store the cell energy sum, sized to the data
max_energy = max(total_energies)
hist_max = 1.2 * max_energy if max_energy > 0 else 1.0
cell_energy_sum_th1 = ROOT.TH1F("cell_energy_sum_th1", ";Cell energy sum [GeV]; Number of events", 100, 0, hist_max)

# Fill the TH1 with the cell energy sum
for total_energy in total_energies:
    cell_energy_sum_th1.Fill(total_energy)

# Fit and draw the histogram
cell_energy_sum_canvas = ROOT.TCanvas("cell_energy_sum_canvas")
if cell_energy_sum_th1.GetEntries() > 0:
    fit_range_min = cell_energy_sum_th1.GetXaxis().GetBinCenter(cell_energy_sum_th1.GetMaximumBin()) - 3 * cell_energy_sum_th1.GetRMS()
    fit_range_max = cell_energy_sum_th1.GetXaxis().GetBinCenter(cell_energy_sum_th1.GetMaximumBin()) + 3 * cell_energy_sum_th1.GetRMS()
    fit_result = cell_energy_sum_th1.Fit("gaus", "SQ", "", fit_range_min, fit_range_max)
    ROOT.gStyle.SetOptFit(1111) # to get the fit result displayed

    # Hands-on 3 asks how the sampling fraction and frequency affect the energy
    # resolution, which is what the width of this peak divided by its mean is.
    mean = fit_result.Parameter(1)
    sigma = fit_result.Parameter(2)
    print(f"Fitted mean:  {mean:.4f} GeV")
    print(f"Fitted sigma: {sigma:.4f} GeV")
    if mean > 0:
        print(f"Energy resolution sigma/mean: {100 * sigma / mean:.2f} %")
else:
    print("Histogram is empty, skipping the fit.")
cell_energy_sum_th1.Draw()

output_file = args.output or f"{os.path.splitext(args.input_file)[0]}_cell_energy_sum.png"
cell_energy_sum_canvas.Print(output_file)
print(f"Wrote {output_file}")
