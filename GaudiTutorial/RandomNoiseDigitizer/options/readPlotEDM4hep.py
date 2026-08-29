import os

# Disable ROOT web display on remote machines
os.environ["ROOT_WEBDISPLAY"] = "off"

import argparse
import podio
import ROOT
from dd4hep import dd4hep 


parser = argparse.ArgumentParser()
parser.add_argument("-i", "--input-file", required=True, help="Input ROOT EDM4hep file")
parser.add_argument("-o", "--output-folder", default="../../data/digitizer-plots", help="Output folder for ROOT and pdf files")
args = parser.parse_args()

#input = "../../data/simpleCalo_noiseDigitizer.root"
input_file = args.input_file  
output_folder = args.output_folder

os.makedirs(output_folder, exist_ok=True)

# detector geometry parameters
n_layers = 20
calo_x = 1000.0       # mm
calo_y = 1000.0       # mm
calo_z = 2000.0       # mm
layer_thickness = 100.0  # mm
n_cells_x = 10
n_cells_y = 10

# Histos for transverse energy profile histograms for each layer
h_transverse = []
for layer in range(1, n_layers + 1):
    h = ROOT.TH2F(
        f"h_transverse_{layer}",
        f"Layer {layer}",
        n_cells_x, -calo_x / 2, calo_x / 2,
        n_cells_y, -calo_y / 2, calo_y / 2,
    )
    h.SetStats(0)
    h_transverse.append(h)
    
# Histo for longitudinal energy profile
h_longitudinal = ROOT.TH1F(
    "h_longitudinal",
    "Longitudinal energy profile;Layer;Energy [MeV]",
    n_layers, 0.5, n_layers + 0.5
)

# Read EDM4hep file using podio and python bindings
reader = podio.root_io.Reader(input_file)

n_events = 0
cell_diffs = []

# Event loop
for event in reader.get("events"):
    # Get relevant collections 
    simhits = event.get("simplecaloRO")
    digihits = event.get("CaloDigiHits")
    # Dictionaries for CellID-based sim-digi comparison 
    sim_by_cell = {}
    digi_by_cell = {}
    
    for hit in digihits:
        # Store hit by CellID for sim-digi comparison
        digi_by_cell[hit.getCellID()] = hit
        
        # Get hit energy and position
        energy = hit.getEnergy() * 1000.0  # GeV -> MeV
        pos = hit.getPosition()
        
        # Determine calorimeter layer and fill histograms
        decoder = dd4hep.BitFieldCoder("calolayer:5,abslayer:1,x:-10,y:-10")
        layer = decoder.get(hit.getCellID(), "calolayer")
        if 1 <= layer <= n_layers:
            h_transverse[layer - 1].Fill(pos.x, pos.y, energy)  
            h_longitudinal.Fill(layer, energy)
            
    for hit in simhits:
        sim_by_cell[hit.getCellID()] = hit
            
    common_cells = sim_by_cell.keys() & digi_by_cell.keys()
    
    for cellid in common_cells:
        sim_energy = sim_by_cell[cellid].getEnergy() * 1000.0
        digi_energy = digi_by_cell[cellid].getEnergy() * 1000.0
        cell_diffs.append(digi_energy - sim_energy)
            
    n_events += 1


# Average profiles over events
for h in h_transverse:
    h.Scale(1.0 / n_events)
h_longitudinal.Scale(1.0 / n_events)

# ---------------------------------
# Longitudinal profile
canvas_longitudinal = ROOT.TCanvas(
    "canvas_longitudinal",          # ROOT object name
    "Longitudinal energy profile",  # Canvas title
    800,                            # Width in pixels
    600                             # Height in pxels
)
canvas_longitudinal.SetLogy()       # Set log scale
h_longitudinal.SetLineColor(ROOT.kRed)
h_longitudinal.Draw("HIST")
canvas_longitudinal.SaveAs(os.path.join(output_folder, "longitudinal_profile.pdf"))

# ---------------------------------
# Transverse per-layer profiles

# Use same energy scale for each histogram
max_energy = max(h.GetMaximum() for h in h_transverse)
for h in h_transverse:
    h.SetMinimum(0.0)
    h.SetMaximum(max_energy)

# Draw all layers in one canvas
canvas_transverse = ROOT.TCanvas(
    "canvas_transverse",
    "Transverse energy profile by layer",
    1500,
    1100
)
canvas_transverse.Divide(5, 4)              # Split canvas in 5 columns x 4 rows
for layer, h in enumerate(h_transverse):

    canvas_transverse.cd(layer + 1)         # Select corresponding canvas pad

    ROOT.gPad.SetRightMargin(0.05)
    ROOT.gPad.SetLeftMargin(0.12)
    ROOT.gPad.SetBottomMargin(0.12)

    h.Draw("COL")                           # 2D histogram with color map
canvas_transverse.SaveAs(os.path.join(output_folder, "transverse_profiles_layers.pdf"))

# ---------------------------------
# Sim-digi cell energy difference 

diff_min = min(cell_diffs)
diff_max = max(cell_diffs)
# Histogram adapts to min, max
h_cell_diff = ROOT.TH1F(
    "h_cell_diff",
    "Cell-by-cell digitization effect;"
    "E_{digi} - E_{sim} [MeV];Cells",
    100,
    diff_min,
    diff_max
)
h_cell_diff.SetStats(0)

for diff in cell_diffs:
    h_cell_diff.Fill(diff)

canvas_energy_diff = ROOT.TCanvas(
    "canvas_energy_diff",
    "Energy difference",
    800,
    600
)
h_cell_diff.SetLineColor(ROOT.kGreen)

h_cell_diff.Fit("gaus") # Gaussian fit
fit = h_cell_diff.GetFunction("gaus")
mean = fit.GetParameter(1)
sigma = fit.GetParameter(2)

h_cell_diff.Draw("HIST")
fit.Draw("SAME")

legend = ROOT.TLegend(0.60, 0.70, 0.88, 0.88)
legend.AddEntry(h_cell_diff, "Cell energy difference", "l")
legend.AddEntry(fit, "Gaussian fit", "l")
legend.AddEntry(0, f"#mu = {mean:.4g} MeV", "")
legend.AddEntry(0, f"#sigma = {sigma:.4g} MeV", "")
legend.Draw()

canvas_energy_diff.SaveAs(os.path.join(output_folder, "energy_difference.pdf"))

# Save canvases to a ROOT file
output_file = ROOT.TFile(os.path.join(output_folder, "plots.root"), "RECREATE")

canvas_longitudinal.Write()
canvas_transverse.Write()
canvas_energy_diff.Write()

output_file.Close()