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
#include "Gaudi/Property.h"
#include <GaudiKernel/SmartIF.h>

// k4FWCore
#include "k4FWCore/Transformer.h"

// k4Interface
#include <k4Interface/IUniqueIDGenSvc.h>

// edm4hep
#include "edm4hep/CalorimeterHitCollection.h"
#include "edm4hep/SimCalorimeterHitCollection.h"

// dd4hep
#include <DD4hep/DD4hepUnits.h>

// STL
#include <random>
#include <string>

struct RandomNoiseDigitizer final
    : k4FWCore::MultiTransformer<std::tuple<edm4hep::CalorimeterHitCollection>(
          const edm4hep::SimCalorimeterHitCollection&, const edm4hep::EventHeaderCollection&)> {

public:
  // Constructor
  RandomNoiseDigitizer(const std::string& name, ISvcLocator* svcLoc)
      : MultiTransformer(
            name, svcLoc,
            // Input collections for the transformer
            {KeyValues("InputCaloSimHitCollection", {"simplecaloRO"}), KeyValues("HeaderName", {"EventHeader"})},
            // Output collections for the transformer
            {KeyValues("OutputCaloDigiHitCollection", {"RndNoiseCaloDigiHits"})}) {}

  // Initialize
  StatusCode initialize() override {

    // Retrieve the UniqueIDGenSvc for generating reproducable random seed
    m_uniqueIDSvc =
        serviceLocator()->service(""); // TODO: replace with the value from the property for the UniqueIDGenSvc name
    if (!m_uniqueIDSvc) {
      error() << "Unable to locate UniqueIDGenSvc with name: " << /* PROPERTY.value() << */ endmsg;  // TODO: replace with the value from the property for the UniqueIDGenSvc name
      return StatusCode::FAILURE;
    }

    return StatusCode::SUCCESS;
  }

  // Operator: transforms a SimCalorimeterHitCollection into digitized CalorimeterHitCollection
  std::tuple<edm4hep::CalorimeterHitCollection>
  operator()(const edm4hep::SimCalorimeterHitCollection& InputCaloSimHitCollection,
             const edm4hep::EventHeaderCollection& header) const override {

    // Define a UserDataCollections for digitized output
    auto CaloDigiHits = edm4hep::CalorimeterHitCollection();

    // Initialise and seed random engine for noise generation
    std::mt19937_64 random_engine;
    auto engine_seed = m_uniqueIDSvc->getUniqueID(header, this->name());
    random_engine.seed(engine_seed);

    // Create the random distributions for smearing the hit energy
    // [[maybe_unused]] used to avoid downstream build failures due to unused variables
    [[maybe_unused]] std::normal_distribution<double> gaussian_noise{
        0.0, 0.0}; // TODO: Replace with mean and width from properties

    // Loop over the input hits
    for (const auto& hit : InputCaloSimHitCollection) {
      auto digihit = CaloDigiHits.create();

      [[maybe_unused]] double noise = gaussian_noise(random_engine);

      digihit.setCellID(hit.getCellID());
      // TODO: Use the EDM4hep yaml file to "guess" the names of the getter and setter functions
      // to define the remaining members of the CalorimeterHit class
    }

    // Store the result in the output collection
    return std::make_tuple(std::move(CaloDigiHits));
  }

private:
  SmartIF<IUniqueIDGenSvc> m_uniqueIDSvc{nullptr};
  // TODO: Create a Gaudi::Property for the UniqueIDGenSvc name (specified in the steering file)

  // TODO: Create two Gaudi::Property members for the noise mean and width
};

DECLARE_COMPONENT(RandomNoiseDigitizer)
