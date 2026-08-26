/*
 * Copyright (c) 2020-2024 Key4hep-Project.
 *
 * This file is part of Key4hep.
 * See https://key4hep.github.io/key4hep-doc/ for further info.
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *     http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */

// k4FWCore
#include "k4FWCore/Transformer.h"

// edm4hep/podio
#include "Gaudi/Property.h"
#include "edm4hep/SimCalorimeterHitCollection.h"
#include "podio/UserDataCollection.h"

// STL
#include <cmath>
#include <mutex>
#include <string>
#include <vector>

// ROOT
#include "TFile.h"
#include "TH1D.h"

struct EventStats final
    : k4FWCore::MultiTransformer<
          // The MultiTransformer returns a tuple containing:
          std::tuple<std::vector<podio::UserDataCollection<double>>, /* Contains the UserDataCollection of each
                                                                        barycentre component*/
                     podio::UserDataCollection<double> /* Contains the value of the total deposited energy */
                     >
          // The MultiTransformer operates on a SimCalorimeterHitCollection as input
          (const edm4hep::SimCalorimeterHitCollection& /* Contains the SimCalorimeterHits correspoding to each energy
                                                          deposit */
           )> {

public:
  // Constructor
  EventStats(const std::string& name, ISvcLocator* svcLoc)
      : MultiTransformer(
            name, svcLoc,
            // Input collections for the transformer
            {
                KeyValues("InputCaloHitCollection", {"simplecaloRO"}) /* name of the input calorimeter hit collection */
            },
            // Output collections for the transformer
            {
                KeyValues("OutputEnergyBarycentre", {"EnergyBarycentre"}), /* barycentre components per event */
                KeyValues("OutputTotalEnergy", {"TotalEnergy"})            /* total energy per event */
            }) {
    // constructor body
  }

  // Initialize
  StatusCode initialize() override {

    if (m_saveHisto.value()) {

      hTotalEnergy = new TH1D("hTotalEnergy", "Total Deposited Energy, in GeV", 50, 0, 10);
      hMaxEnergy = new TH1D("hMaxEnergy", "Max Deposited Energy, in GeV", 50, 0, 10);
      hMinEnergy = new TH1D("hMinEnergy", "Min Deposited Energy, in GeV", 50, 0, 10);
    }

    return StatusCode::SUCCESS;
  }

  // Operator: transforms a SimCalorimeterHitCollection into a tuple of output collections
  std::tuple<std::vector<podio::UserDataCollection<double>>, /* vector of barycentre components (x, y, z) */
             podio::UserDataCollection<double>               /* additional scalar values (total energy) */
             >
  operator()(const edm4hep::SimCalorimeterHitCollection& InputSimCaloHitCollection) const override {

    //////////////////////////////////////////
    //// DEFINITION OF OUTPUT COLLECTIONS ////
    //////////////////////////////////////////

    // Define a vector of UserDataCollections, each storing doubles.
    // This stores the components (x,y,z) of the energy barycentre.
    std::vector<podio::UserDataCollection<double>> Barycentre;

    // Define three separate UserDataCollections for the barycentre coordinates.
    auto BarycentreX = podio::UserDataCollection<double>(); // x-coordinates of the barycentre
    auto BarycentreY = podio::UserDataCollection<double>(); // y-coordinates of the barycentre
    auto BarycentreZ = podio::UserDataCollection<double>(); // z-coordinates of the barycentre

    // Define a UserDataCollections for TotalDepositedEnergy
    auto TotalDepositedEnergy = podio::UserDataCollection<double>();

    /////////////////////////////////////////
    //// CALCULATION OF EVENT STATISTICS ////
    /////////////////////////////////////////

    double totalEnergy = 0.0;
    double barycentre_x = 0.0;
    double barycentre_y = 0.0;
    double barycentre_z = 0.0;

    double max_pos_x = std::numeric_limits<double>::lowest();
    double min_pos_x = std::numeric_limits<double>::max();

    double max_pos_y = std::numeric_limits<double>::lowest();
    double min_pos_y = std::numeric_limits<double>::max();

    double max_pos_z = std::numeric_limits<double>::lowest();
    double min_pos_z = std::numeric_limits<double>::max();

    double maxEnergy = std::numeric_limits<double>::lowest();
    double minEnergy = std::numeric_limits<double>::max();
    double maxEnergy_x = 0.0;
    double maxEnergy_y = 0.0;
    double maxEnergy_z = 0.0;
    double minEnergy_x = 0.0;
    double minEnergy_y = 0.0;
    double minEnergy_z = 0.0;

    for (const auto& simhit : InputSimCaloHitCollection) {

      double x = simhit.getPosition().x;
      double y = simhit.getPosition().y;
      double z = simhit.getPosition().z;
      double energy = simhit.getEnergy();

      barycentre_x += x * energy;
      barycentre_y += y * energy;
      barycentre_z += z * energy;
      totalEnergy += energy;

      if (energy > maxEnergy) {
        maxEnergy = energy;
        maxEnergy_x = x;
        maxEnergy_y = y;
        maxEnergy_z = z;
      }
      if (energy < minEnergy) {
        minEnergy = energy;
        minEnergy_x = x;
        minEnergy_y = y;
        minEnergy_z = z;
      }
      if (x > max_pos_x)
        max_pos_x = x;
      if (y > max_pos_y)
        max_pos_y = y;
      if (z > max_pos_z)
        max_pos_z = z;
      if (x < min_pos_x)
        min_pos_x = x;
      if (y < min_pos_y)
        min_pos_y = y;
      if (z < min_pos_z)
        min_pos_z = z;
    }

    // An event without any energy deposit has no barycentre: dividing here would
    // hand NaN to every downstream algorithm.
    if (totalEnergy > 0.0) {
      barycentre_x /= totalEnergy;
      barycentre_y /= totalEnergy;
      barycentre_z /= totalEnergy;
    }

    /////////////////////////////////////////
    //// SAVE HISTOGRAMS OF ENERGY STATS ////
    /////////////////////////////////////////

    if (m_saveHisto && totalEnergy > 0.0) {
      // operator() is const and the Avalanche scheduler calls it from several
      // threads at once (see runEventStatsMultithreading.py). TH1::Fill is not
      // thread safe, so the shared histograms have to be protected.
      std::scoped_lock lock(m_histoMutex);
      hTotalEnergy->Fill(totalEnergy);
      hMaxEnergy->Fill(maxEnergy);
      hMinEnergy->Fill(minEnergy);
    }

    /////////////////////////////////////////////////////
    //// FILL BARYCENTRE AND TOTALENERGY COLLECTIONS ////
    /////////////////////////////////////////////////////

    TotalDepositedEnergy.push_back(totalEnergy);

    BarycentreX.push_back(barycentre_x);
    Barycentre.push_back(std::move(BarycentreX));

    BarycentreY.push_back(barycentre_y);
    Barycentre.push_back(std::move(BarycentreY));

    BarycentreZ.push_back(barycentre_z);
    Barycentre.push_back(std::move(BarycentreZ));

    ///////////////////////////
    //// PRINT EVENT STATS ////
    ///////////////////////////

    info() << "Event statistics:" << endmsg;
    info() << "Total deposited energy = " << totalEnergy << " GeV" << endmsg;
    info() << "Energy Barycentre position: (" << barycentre_x << ", " << barycentre_y << ", " << barycentre_z << ") mm"
           << endmsg;
    info() << "Max energy: " << maxEnergy << " GeV at (" << maxEnergy_x << ", " << maxEnergy_y << ", " << maxEnergy_z
           << ") mm" << endmsg;
    info() << "Min energy: " << minEnergy << " GeV at (" << minEnergy_x << ", " << minEnergy_y << ", " << minEnergy_z
           << ") mm" << endmsg;
    info() << "MaxXYZ values: (" << max_pos_x << ", " << max_pos_y << ", " << max_pos_z << ") mm" << endmsg;
    info() << "MinXYZ values: (" << min_pos_x << ", " << min_pos_y << ", " << min_pos_z << ") mm" << endmsg;
    info() << "------------------------------" << endmsg;

    ////////////////
    //// OUTPUT ////
    ////////////////

    return std::make_tuple(std::move(Barycentre), std::move(TotalDepositedEnergy));
  }

  // Finalize
  StatusCode finalize() override {

    if (m_saveHisto.value()) {

      TFile* f = new TFile("debugEventStats.root", "RECREATE");
      hTotalEnergy->Write();
      hMaxEnergy->Write();
      hMinEnergy->Write();
      f->Close();

      delete hTotalEnergy;
      delete hMaxEnergy;
      delete hMinEnergy;
      delete f;
    }

    return StatusCode::SUCCESS;
  }

private:
  Gaudi::Property<bool> m_saveHisto{this, "SaveHistograms", false, "flag to save histograms"};

  mutable std::mutex m_histoMutex;

  TH1D* hTotalEnergy = nullptr;
  TH1D* hMaxEnergy = nullptr;
  TH1D* hMinEnergy = nullptr;
};

DECLARE_COMPONENT(EventStats)
