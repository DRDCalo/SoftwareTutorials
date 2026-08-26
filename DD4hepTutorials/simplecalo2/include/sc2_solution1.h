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
Box Cell(CellX / 2., CellY / 2., CellZ / 2.);
Volume CellVol("CellVol", Cell, description.material(x_cell.attr<std::string>(_U(material))));
CellVol.setVisAttributes(description, x_cell.visStr());
// Make the cell sensitive
if (iscellsens)
  CellVol.setSensitiveDetector(sens);

// How many cells fit into the sensitive layer follows from the XML dimensions, so
// changing CellX/CellY or SensLayerX/SensLayerY in simplecalo2.xml is enough and
// this code does not have to be touched.
const int NCellsX = static_cast<int>(std::round(SensLayerX / CellX));
const int NCellsY = static_cast<int>(std::round(SensLayerY / CellY));

// Refuse a geometry that would be silently wrong. Cells that do not tile the layer
// leave part of it uncovered, and the cellid field of the readout is 10 bits wide
// (see <id> in simplecalo2.xml), so beyond 1024 cells two of them share an address.
if (std::abs(NCellsX * CellX - SensLayerX) > 1e-6 || std::abs(NCellsY * CellY - SensLayerY) > 1e-6)
  except("simplecalo2", "Cells do not tile the sensitive layer: %g/%g and %g/%g must be whole numbers.", SensLayerX,
         CellX, SensLayerY, CellY);
if (NCellsX * NCellsY > 1024)
  except("simplecalo2", "%d x %d cells do not fit the 10-bit cellid field, which holds 1024.", NCellsX, NCellsY);

// The outer loop runs over y and the inner one over x, hence cellid = NCellsX * iY + iX.
// The analysis has to use the same convention to turn a cellid back into a cell position.
for (int iY = 0; iY < NCellsY; iY++) {
  const double y = SensLayerY / 2. - CellY / 2. - iY * CellY;
  for (int iX = 0; iX < NCellsX; iX++) {
    const double x = -SensLayerX / 2. + CellX / 2. + iX * CellX;
    const int cellid = NCellsX * iY + iX;
    PlacedVolume CellVolPlaced = SensLayerVol.placeVolume(CellVol, cellid, Position(x, y, 0.));
    CellVolPlaced.addPhysVolID("cellid", cellid);
  }
}
