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

// Gaudi
#include "Gaudi/Accumulators.h"

// k4FWCore
#include "k4FWCore/Transformer.h"

// podio
#include "podio/UserDataCollection.h"

// edm4hep
#include "edm4hep/CalorimeterHitCollection.h"

// STL
#include <algorithm> // std::sort
#include <cmath>
#include <string>
#include <vector>

struct MoliereRadiusSolution final
    : k4FWCore::MultiTransformer<std::tuple<podio::UserDataCollection<double>>(
          const edm4hep::CalorimeterHitCollection&, const std::vector<const podio::UserDataCollection<double>*>&,
          const podio::UserDataCollection<double>&)> {

public:
  // Constructor
  MoliereRadiusSolution(const std::string& name, ISvcLocator* svcLoc)
      : MultiTransformer(name, svcLoc,
                         // Input collections for the transformer
                         {KeyValues("InputCaloHitCollection", {"RndNoiseCaloDigiHits"}),
                          KeyValues("InputBarycenter", {"Barycentre"}), KeyValues("InputTotalEnergy", {"TotalEnergy"})},
                         // Output collections for the transformer
                         {KeyValues("OutputMoliereRadius", {"MoliereRadius"})}) {}

  // Operator: transforms a CalorimeterHitCollection into a tuple of output collections
  std::tuple<podio::UserDataCollection<double>>
  operator()(const edm4hep::CalorimeterHitCollection& InputCaloHitCollection,
             const std::vector<const podio::UserDataCollection<double>*>& InputBarycenter,
             const podio::UserDataCollection<double>& InputTotalEnergy) const override {

    // Define a UserDataCollections for Moliere radius output
    auto MoliereRadiusCollection = podio::UserDataCollection<double>();

    std::vector<HitData> radialHits;

    // Retrieve barycentre and total energy
    double barycentre_x = InputBarycenter[0]->at(0);
    double barycentre_y = InputBarycenter[1]->at(0);
    double totalEnergy = InputTotalEnergy.at(0);

    // Step 1: Calculate radius for each hit and store with energy
    for (const auto& hit : InputCaloHitCollection) {
      const auto& pos = hit.getPosition();
      double dx = pos.x - barycentre_x;
      double dy = pos.y - barycentre_y;
      double r = std::sqrt(dx * dx + dy * dy);
      double e = hit.getEnergy();
      radialHits.push_back({r, e});
    }

    // Step 2: Sort hits by radius
    std::sort(radialHits.begin(), radialHits.end(), [](const HitData& a, const HitData& b) { return a.r < b.r; });

    // Step 3: Accumulate energy and find radius at 90%
    double cumulativeEnergy = 0.0;
    double moliereRadius = 0.0;
    for (const auto& hit : radialHits) {
      cumulativeEnergy += hit.energy;
      if (cumulativeEnergy >= 0.9 * totalEnergy) {
        moliereRadius = hit.r;
        break;
      }
    }

    info() << "---> Calculated Moliere radius: " << moliereRadius << " mm" << endmsg;

    // Step 4: Store the result in the output collection and the accumulator
    m_moliere_radius_acc += moliereRadius;
    MoliereRadiusCollection.push_back(moliereRadius);
    return std::make_tuple(std::move(MoliereRadiusCollection));
  }

  // Finalize
  StatusCode finalize() override {

    info() << "Average Moliere radius over all events: " << m_moliere_radius_acc.mean() << " mm" << endmsg;

    return StatusCode::SUCCESS;
  }

private:
  struct HitData {
    double r;      // Radius from barycentre
    double energy; // Energy of the hit
  };

  mutable Gaudi::Accumulators::AveragingCounter<double, Gaudi::Accumulators::atomicity::full> m_moliere_radius_acc;
};

DECLARE_COMPONENT(MoliereRadiusSolution)
