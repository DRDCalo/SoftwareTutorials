// load required libraries for ROOT interpreter
R__LOAD_LIBRARY(libDDCore.so)
R__LOAD_LIBRARY(libpodio.so)
R__LOAD_LIBRARY(libpodioRootIO.so)
R__LOAD_LIBRARY(libedm4hep.so)

#include "DDSegmentation/BitFieldCoder.h"

// Declare the namespace for ROOT interpreter
namespace dd4hep {
  namespace DDSegmentation {
    class BitFieldCoder;
  }
}

#include "podio/ROOTReader.h"
#include "podio/Frame.h"

#include "edm4hep/SimCalorimeterHitCollection.h"

#include "TROOT.h"
#include "TH1F.h"
#include "TH2F.h"
#include "TFile.h"

// hands-on example to read edm4hep SimCalorimeterHitCollection and perform some basic analysis
void readEdm4hep(const std::string& filename) {
  // Open the ROOT file using podio
  std::vector<std::string> files = {filename};
  auto reader = podio::ROOTReader();
  reader.openFiles(files);

  // event tree is always named "events"
  unsigned int entries = reader.getEntries("events");

  // bit field decoder
  // Q1: which string should we use to decode the cellID for SimCalorimeterHitCollection in this file?
  // (hint: check the cellID encoding in the DD4hep XML file used for simulation)
  auto decoder = dd4hep::DDSegmentation::BitFieldCoder("/*fill me*/");

  // define histograms
  // add more histograms as needed for your analysis
  TH1::SetDefaultSumw2(); // enable Sumw2 for all histograms
  auto* hEnergy = new TH1F("hEnergy", "Total energy deposit;Energy (GeV);Events", 100, 0, 5.); // adjust range as needed
  auto* hLayerEnergySum = new TH1F("hLayerEnergySum", "Avg energy deposit for each active Layer;i-th layer;Energy (GeV)", 20, 0, 20);
  auto* hContributionTime = new TH1F("hContributionTime", "Timing distribution of hit contributions;Time (ns);Entries", 50, 0, 10); // adjust range as needed

  // lateral shower shape per layer
  std::vector<TH2F*> hLateralShapePerLayer;
  for (int i = 1; i <= 20; i++) { // layer index starts from 1
    hLateralShapePerLayer.push_back(new TH2F(Form("hLateralShape_Layer%d", i), Form("Lateral shower shape for Layer %d;iX;iY", i), 10, 0, 10, 10, 0, 10));
  }

  // loop over events
  for (unsigned int iEvt = 0; iEvt < entries; iEvt++) {
    if (iEvt % 100 == 0) printf("Analyzing %dth event ...\n", iEvt);

    // read podio::Frame for the current event
    auto aframe = podio::Frame(reader.readEntry("events",iEvt));

    // Q2: how to get the SimCalorimeterHitCollection from the frame? (hint: check the collection name in the file)
    const auto* simHits = static_cast<const edm4hep::SimCalorimeterHitCollection*>(aframe.get("/*fill me*/"));

    float totalEnergy = 0.f;

    // loop over hits in the event
    for (const auto& hit : *simHits) {
      // Q3: how to decode the cellID to get the calo layer, abs layer, and sub-cell id? (hint: use the bit field decoder)
      int caloLayer; /*fill me*/
      int absLayer; /*fill me*/
      int subCellId; /*fill me*/

      // std::cout << "Hit energy: " << hit.getEnergy() << " GeV, CellID: " << hit.getCellID()
      //           << ", CaloLayer: " << caloLayer << ", AbsLayer: " << absLayer
      //           << ", SubCellId: " << subCellId << std::endl;

      // Q4: fill the histograms defined above to analyze the energy distribution, layer-wise energy sum

      // Q5: fill lateral shower shape per layer
      // Note: cellid = 10*x + y

      // Q6: how to access the contributions to each hit and fill the timing distribution of contributions? (hint: check the edm4hep SimCalorimeterHit class definition for contributions)
      // fill timing distribution of contributions
    } // loop hits
  } // loop events

  hLayerEnergySum->Scale(1./static_cast<float>(entries)); // average energy per layer
  std::for_each(hLateralShapePerLayer.begin(), hLateralShapePerLayer.end(), [entries](TH2F* hist) { hist->Scale(1./static_cast<float>(entries)); }); // average lateral shape per layer

  // you know how to save or display the histograms from here
  // output results
  auto* outFile = TFile::Open("edm4hep_analysis.root", "RECREATE");
  hEnergy->Write();
  hLayerEnergySum->Write();
  hContributionTime->Write();

  for (auto* hist : hLateralShapePerLayer) {
    hist->Write();
  }

  outFile->Close();
}

// solution
// Q1: bit field decoder
// auto decoder = dd4hep::DDSegmentation::BitFieldCoder("calolayer:5,abslayer:1,cellid:10");

// Q2: get SimCalorimeterHitCollection from the frame
// const auto* simHits = static_cast<const edm4hep::SimCalorimeterHitCollection*>(aframe.get("simplecaloRO"));

// Q3: decode cellID
// int caloLayer = decoder.get(hit.getCellID(), "calolayer");
// int absLayer = decoder.get(hit.getCellID(), "abslayer");
// int subCellId = decoder.get(hit.getCellID(), "cellid");

// Q4: fill histograms
// total energy sum
// totalEnergy += hit.getEnergy();
// // and add to energy histogram at the end of the event loop
// hEnergy->Fill(totalEnergy);

// // energy per layer
// hLayerEnergySum->Fill(static_cast<float>(caloLayer) + 0.5, hit.getEnergy());
// // Note: the +0.5 is to fill the histogram bin corresponding to the integer layer number

// Q5: fill lateral shower shape per layer
// int x = subCellId / 10;
// int y = subCellId % 10;
// unsigned int layerIndex = caloLayer - 1; // assuming caloLayer starts from 1
// hLateralShapePerLayer[layerIndex]->Fill(static_cast<float>(x) + 0.5, static_cast<float>(y) + 0.5, hit.getEnergy());

// Q6: access contributions and fill timing distribution
// for (const auto& contrib : hit.getContributions()) {
// //   std::cout << "  Contrib energy: " << contrib.getEnergy() << " GeV, PDG: " << contrib.getPDG() << std::endl;
//   hContributionTime->Fill(contrib.getTime(), contrib.getEnergy());
// }
