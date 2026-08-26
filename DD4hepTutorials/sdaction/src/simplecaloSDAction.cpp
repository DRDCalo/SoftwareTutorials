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

#include "DD4hep/Segmentations.h"
#include "DDG4/Factories.h"
#include "DDG4/Geant4GeneratorAction.h"
#include "DDG4/Geant4Mapping.h"
#include "DDG4/Geant4SensDetAction.inl"

#include "CLHEP/Units/SystemOfUnits.h"
#include "G4ThreeVector.hh"
#include "G4TouchableHandle.hh"
#include <cmath>

// #define DEBUG

namespace dd4hep {
namespace sim {
  class simplecaloSDData {
    // Constructor and destructor
    //
  public:
    simplecaloSDData() = default;
    ~simplecaloSDData() = default;

  public:
    Geant4Sensitive* sensitive{};
  };
} // namespace sim
} // namespace dd4hep

namespace dd4hep {
namespace sim {

  // Function template specialization of Geant4SensitiveAction class.
  // Define actions
  template <>
  void Geant4SensitiveAction<simplecaloSDData>::initialize() {
    m_userData.sensitive = this;
    m_hitCreationMode = HitCreationFlags::DETAILED_MODE;
  }

  // Function template specialization of Geant4SensitiveAction class.
  // Define collections created by this sensitivie action object
  template <>
  void Geant4SensitiveAction<simplecaloSDData>::defineCollections() {
    std::string ROname = m_sensitive.readout().name();
    m_collectionID = defineCollection<Geant4Calorimeter::Hit>(ROname);
  }

  // Function template specialization of Geant4SensitiveAction class.
  // Method that accesses the G4Step object at each track step.
  template <>
  bool Geant4SensitiveAction<simplecaloSDData>::process(const G4Step* aStep, G4TouchableHistory* /*history*/) {

#ifdef DEBUG
    std::cout << "-------------------------------" << std::endl;
    std::cout << "--> simplecalo: track info: " << std::endl;
    std::cout << "----> Track #: " << aStep->GetTrack()->GetTrackID() << " "
              << "Step #: " << aStep->GetTrack()->GetCurrentStepNumber() << " "
              << "Volume: " << aStep->GetPreStepPoint()->GetTouchableHandle()->GetVolume()->GetName() << " "
              << std::endl;
    std::cout << "--> simplecalo:: position info(mm): " << std::endl;
    std::cout << "----> x: " << aStep->GetPreStepPoint()->GetPosition().x()
              << " y: " << aStep->GetPreStepPoint()->GetPosition().y()
              << " z: " << aStep->GetPreStepPoint()->GetPosition().z() << std::endl;
    std::cout << "--> simplecalo: particle info: " << std::endl;
    std::cout << "----> Particle " << aStep->GetTrack()->GetParticleDefinition()->GetParticleName() << " "
              << "Dep(MeV) " << aStep->GetTotalEnergyDeposit() << " "
              << "Mat " << aStep->GetPreStepPoint()->GetMaterial()->GetName() << " "
              << "Vol " << aStep->GetPreStepPoint()->GetTouchableHandle()->GetVolume()->GetName() << " " << std::endl;
#endif

    auto VolID = volumeID(aStep);
#ifdef DEBUG
    // Parsing the encoding string is not free, so keep it out of the per-step
    // path: the decoder is only needed for the printout below. The string has to
    // match the <id> element of the <readout> block in simplecalo2.xml.
    static const dd4hep::BitFieldCoder decoder("calolayer:5,abslayer:1,cellid:10");
    auto CaloLayerID = decoder.get(VolID, "calolayer");
    auto AbsLayerID = decoder.get(VolID, "abslayer");
    auto CellID = decoder.get(VolID, "cellid");
    std::cout << "--> CaloLayerID: " << CaloLayerID << " AbsLayerID " << AbsLayerID << " CellID " << CellID
              << std::endl;
#endif

    G4TouchableHandle theTouchable = aStep->GetPreStepPoint()->GetTouchableHandle();
    G4ThreeVector origin(0., 0., 0.);
    // Centre of the cell this step happened in, in global coordinates
    G4ThreeVector CellPos = theTouchable->GetHistory()->GetTopTransform().Inverse().TransformPoint(origin);
    // Where the step actually started, in global coordinates
    G4ThreeVector StepPos = aStep->GetPreStepPoint()->GetPosition();
#ifdef DEBUG
    std::cout << "--> Cell global pos(mm) " << CellPos.x() << " " << CellPos.y() << " " << CellPos.z() << std::endl;
#endif

    // Hands-on 5: apply a very short time cut (10 ns) to record the signals
    // and consider the cell border (2 cm) along x and y completely inefficient,
    // i.e. no signal is recorded from that area.
    // Hint: the x,y,z position of the step in the local volume reference frame is
    // G4ThreeVector localPosition =
    //     theTouchable->GetHistory()->GetTopTransform().TransformPoint(StepPos);
    //

    // Hands-on 5: solution
    //
    /*
    // Geant4 works in mm and ns, so CLHEP::ns and CLHEP::cm are the units to use
    // here. Careful: inside namespace dd4hep, a bare `ns` or `cm` would resolve to
    // dd4hep's own units, where the native length unit is cm and not mm.
    constexpr double TIME_CUT = 10. * CLHEP::ns;
    constexpr double CELL_HALF_SIZE = 5. * CLHEP::cm;   // cells are 10 cm x 10 cm
    constexpr double DEAD_BORDER = 2. * CLHEP::cm;      // inefficient rim around each cell
    constexpr double ACTIVE_HALF_SIZE = CELL_HALF_SIZE - DEAD_BORDER;

    if (aStep->GetPreStepPoint()->GetGlobalTime() > TIME_CUT) {
      return true;
    }
    G4ThreeVector localPosition = theTouchable->GetHistory()->GetTopTransform().TransformPoint(StepPos);
    if (std::abs(localPosition.x()) > ACTIVE_HALF_SIZE || std::abs(localPosition.y()) > ACTIVE_HALF_SIZE) {
      return true;
    }
    // end of Hands-on 5
    */

    // Describe this step as a contribution to the cell it happened in.
    //
    // Units: everything below stays in Geant4's internal units, i.e. MeV, mm and
    // ns. Nothing is converted here, and nothing should be: DDG4's EDM4hep writer
    // (Geant4Output2EDM4hep) divides by CLHEP::GeV, CLHEP::mm and CLHEP::ns when
    // it serialises the hits, so the file ends up with the GeV, mm and ns that
    // EDM4hep specifies. Converting here as well would apply the factor twice.
    // Do not confuse either with dd4hep's own unit system, whose native length
    // unit is cm.
    Geant4Calorimeter::Hit::Contribution contrib;
    contrib.trackID = aStep->GetTrack()->GetTrackID();
    contrib.pdgID = aStep->GetTrack()->GetParticleDefinition()->GetPDGEncoding();
    contrib.deposit = aStep->GetTotalEnergyDeposit();
    contrib.time = aStep->GetPreStepPoint()->GetGlobalTime();
    contrib.length = aStep->GetStepLength();
    // A contribution is a snapshot of a single step, so it carries the position of
    // that step. EDM4hep stores this member as CaloHitContribution::stepPosition.
    contrib.setPosition(StepPos.x(), StepPos.y(), StepPos.z());

    // Create the hits and accumulate contributions from multiple steps
    //
    Geant4HitCollection* coll = collection(m_collectionID);
    Geant4Calorimeter::Hit* hit = coll->findByKey<Geant4Calorimeter::Hit>(VolID); // the hit

    if (!hit) { // if the hit does not exist yet, create it
      hit = new Geant4Calorimeter::Hit();
      // cellID and position identify the readout element, so they are assigned
      // exactly once: the hit sits at the centre of its cell.
      hit->cellID = VolID;
      hit->position = Position(CellPos.x(), CellPos.y(), CellPos.z());
      hit->energyDeposit = 0.;
      coll->add(VolID, hit); // add the hit to the hit collection
    }

    // Every step adds to the hit energy and appends its own contribution
    hit->energyDeposit += aStep->GetTotalEnergyDeposit();
    hit->truth.emplace_back(contrib);

    return true;
  } // end of Geant4SensitiveAction::process() method specialization

} // namespace sim
} // namespace dd4hep

//--- Factory declaration
namespace dd4hep {
namespace sim {
  typedef Geant4SensitiveAction<simplecaloSDData> SimpleCaloSDAction;
}
} // namespace dd4hep
DECLARE_GEANT4SENSITIVE(SimpleCaloSDAction)

//**************************************************************************
