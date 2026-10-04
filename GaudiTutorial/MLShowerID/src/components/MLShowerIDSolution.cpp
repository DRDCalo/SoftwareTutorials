/*
 * Gaudi processor for SimpleCalo PointNet shower identification.
 *
 * The deployed ONNX model accepts raw (x, y, z, energy) hit features and
 * performs the training normalization inside the model graph.
 *
 * Model interface:
 *   points: float32 [batch, maxPoints, 4]  (x, y, z, energy)
 *   mask:   bool    [batch, maxPoints]     (true for real hits)
 *   scores: float32 [batch, 2]             (electron, hadronic probabilities)
 *
 * maxPoints is read from the fixed points tensor shape when the model loads.
 */

// Gaudi
#include "Gaudi/Property.h"
#include "GaudiKernel/EventContext.h"

// k4FWCore
#include "k4FWCore/Transformer.h"

// EDM4hep
#include "edm4hep/CalorimeterHitCollection.h"
#include "edm4hep/ClusterCollection.h"
#include "edm4hep/SimCalorimeterHitCollection.h"
#include "edm4hep/Vector3f.h"

// ONNX Runtime
#include "onnxruntime_cxx_api.h"

// STL
#include <algorithm>
#include <array>
#include <memory>
#include <stdexcept>
#include <string>
#include <tuple>
#include <vector>

struct MLShowerIDSolution final
    : k4FWCore::MultiTransformer<std::tuple<edm4hep::CalorimeterHitCollection, edm4hep::ClusterCollection>(
          const EventContext&, const edm4hep::SimCalorimeterHitCollection&)> {
public:
  MLShowerIDSolution(const std::string& name, ISvcLocator* svcLoc)
      : MultiTransformer(name, svcLoc, {KeyValues("InputSimCaloHitCollection", {"simplecaloRO"})},
                         {KeyValues("OutputCaloHitCollection", {"simpleCaloHits"}),
                          KeyValues("OutputClusterCollection", {"CaloClustersWithID"})}) {}

  StatusCode initialize() override {
    info() << "MLShowerIDSolution will read ONNX model from: " << m_modelPath.value() << endmsg;

    try {
      m_memoryInfo =
          std::make_unique<Ort::MemoryInfo>(Ort::MemoryInfo::CreateCpu(OrtArenaAllocator, OrtMemTypeDefault));
      m_env = std::make_unique<Ort::Env>(ORT_LOGGING_LEVEL_WARNING, "MLShowerIDSolution");

      Ort::SessionOptions sessionOptions;
      sessionOptions.SetIntraOpNumThreads(1);
      sessionOptions.SetGraphOptimizationLevel(GraphOptimizationLevel::ORT_ENABLE_BASIC);

      // Support GPU execution using CUDA provider
      // OrtCUDAProviderOptions cudaOptions{};
      // cudaOptions.device_id = 0;  // Set the GPU device ID if you have multiple GPUs
      // sessionOptions.AppendExecutionProvider_CUDA(cudaOptions);

      m_session = std::make_unique<Ort::Session>(*m_env, m_modelPath.value().c_str(), sessionOptions);

      if (m_session->GetInputCount() != 2 || m_session->GetOutputCount() != 1) {
        error() << "Expected two ONNX inputs and one output" << endmsg;
        return StatusCode::FAILURE;
      }

      Ort::AllocatorWithDefaultOptions allocator;
      const auto pointsName = m_session->GetInputNameAllocated(0, allocator);
      const auto maskName = m_session->GetInputNameAllocated(1, allocator);
      const auto scoresName = m_session->GetOutputNameAllocated(0, allocator);
      if (std::string(pointsName.get()) != "points" || std::string(maskName.get()) != "mask" ||
          std::string(scoresName.get()) != "scores") {
        error() << "Expected ONNX tensor names: inputs points, mask; output scores" << endmsg;
        return StatusCode::FAILURE;
      }

      const auto pointsShape = m_session->GetInputTypeInfo(0).GetTensorTypeAndShapeInfo().GetShape();
      const auto maskShape = m_session->GetInputTypeInfo(1).GetTensorTypeAndShapeInfo().GetShape();
      const auto scoresShape = m_session->GetOutputTypeInfo(0).GetTensorTypeAndShapeInfo().GetShape();
      // Expected tensor layouts:
      //   points: [batch, maxPoints, 4], so rank is 3 and dimension 2
      //           has four features: x, y, z and energy.
      //   mask:   [batch, maxPoints], so rank is 2.
      //   scores: [batch, 2], so rank is 2 and dimension 1 contains the
      //           normalized electron and hadronic probabilities.
      if (pointsShape.size() != 3 || pointsShape[2] != 4 || maskShape.size() != 2 ||
          scoresShape.size() != 2 || scoresShape[1] != 2) {
        error() << "Unexpected ONNX tensor shapes" << endmsg;
        return StatusCode::FAILURE;
      }
      if (pointsShape[1] <= 0 || maskShape[1] <= 0) {
        error() << "The ONNX model must have a fixed maxPoints dimension" << endmsg;
        return StatusCode::FAILURE;
      }
      if (pointsShape[1] != maskShape[1]) {
        error() << "points and mask use different maxPoints dimensions" << endmsg;
        return StatusCode::FAILURE;
      }
      m_maxPoints = static_cast<std::size_t>(pointsShape[1]);
      info() << "ONNX model maxPoints: " << m_maxPoints << endmsg;
    } catch (const Ort::Exception& exception) {
      error() << "Failed to initialize ONNX Runtime: " << exception.what() << endmsg;
      return StatusCode::FAILURE;
    }

    return StatusCode::SUCCESS;
  }

  std::tuple<edm4hep::CalorimeterHitCollection, edm4hep::ClusterCollection>
  operator()(const EventContext& eventContext,
             const edm4hep::SimCalorimeterHitCollection& simHits) const override {
    edm4hep::CalorimeterHitCollection caloHits;
    edm4hep::ClusterCollection clusters;

    double hitEnergy = 0.0;
    double totalEnergy = 0.0;
    edm4hep::Vector3f hitPosition{0.0F, 0.0F, 0.0F};
    edm4hep::Vector3f weightedPosition{0.0F, 0.0F, 0.0F};

    for (const auto& simHit : simHits) {
      auto caloHit = caloHits.create();
      caloHit.setCellID(simHit.getCellID());
      caloHit.setEnergy(simHit.getEnergy());
      caloHit.setPosition(simHit.getPosition());

      hitPosition = simHit.getPosition();
      hitEnergy = simHit.getEnergy();
      totalEnergy += hitEnergy;
      weightedPosition.x += hitEnergy * hitPosition.x;
      weightedPosition.y += hitEnergy * hitPosition.y;
      weightedPosition.z += hitEnergy * hitPosition.z;
    }

    if (totalEnergy > 0.0) {
      weightedPosition.x /= totalEnergy;
      weightedPosition.y /= totalEnergy;
      weightedPosition.z /= totalEnergy;
    }

    const auto scores = runInference(caloHits);

    auto cluster = clusters.create();
    cluster.setEnergy(static_cast<float>(totalEnergy));
    cluster.setPosition(weightedPosition);
    for (const auto& hit : caloHits) {
      cluster.addToHits(hit);
    }
    // Keep this order synchronized with the ONNX scores output:
    // shapeParameters[0] = electron score, shapeParameters[1] = hadronic score.
    cluster.addToShapeParameters(scores[0]);
    cluster.addToShapeParameters(scores[1]);

    debug() << "Event ID: " << eventContext.evt() << ", cluster energy: " << cluster.getEnergy()
            << ", electron score: " << scores[0] << ", hadron score: " << scores[1] << endmsg;

    return std::make_tuple(std::move(caloHits), std::move(clusters));
  }

  StatusCode finalize() override { return StatusCode::SUCCESS; }

private:
  std::vector<float> runInference(const edm4hep::CalorimeterHitCollection& caloHits) const {
    if (caloHits.empty()) {
      return {0.5F, 0.5F};
    }

    std::vector<edm4hep::CalorimeterHit> orderedHits;
    orderedHits.reserve(caloHits.size());
    for (const auto& hit : caloHits) {
      orderedHits.push_back(hit);
    }
    std::stable_sort(orderedHits.begin(), orderedHits.end(),
                     [](const auto& lhs, const auto& rhs) { return lhs.getEnergy() > rhs.getEnergy(); });

    const auto maxPoints = m_maxPoints;
    const auto numPoints = std::min(maxPoints, orderedHits.size());
    std::vector<float> points(maxPoints * 4, 0.0F);
    auto mask = std::make_unique<bool[]>(maxPoints);
    std::fill_n(mask.get(), maxPoints, false);

    for (std::size_t index = 0; index < numPoints; ++index) {
      const auto position = orderedHits[index].getPosition();
      const auto offset = index * 4;
      points[offset] = position.x;
      points[offset + 1] = position.y;
      points[offset + 2] = position.z;
      points[offset + 3] = orderedHits[index].getEnergy();
      mask[index] = true;
    }

    const std::array<int64_t, 3> pointsShape{1, static_cast<int64_t>(maxPoints), 4};
    const std::array<int64_t, 2> maskShape{1, static_cast<int64_t>(maxPoints)};
    std::vector<Ort::Value> inputTensors;
    inputTensors.reserve(2);
    inputTensors.emplace_back(Ort::Value::CreateTensor<float>(
        *m_memoryInfo, points.data(), points.size(), pointsShape.data(), pointsShape.size()));
    inputTensors.emplace_back(
        Ort::Value::CreateTensor<bool>(*m_memoryInfo, mask.get(), maxPoints, maskShape.data(), maskShape.size()));

    constexpr std::array<const char*, 2> inputNames{"points", "mask"};
    constexpr std::array<const char*, 1> outputNames{"scores"};
    Ort::RunOptions runOptions{nullptr};
    auto outputTensors = m_session->Run(runOptions, inputNames.data(), inputTensors.data(), inputTensors.size(),
                                        outputNames.data(), outputNames.size());

    if (outputTensors.size() != 1 || !outputTensors.front().IsTensor() ||
        outputTensors.front().GetTensorTypeAndShapeInfo().GetElementCount() != 2) {
      throw std::runtime_error("ONNX model returned an invalid scores tensor");
    }

    const auto* scores = outputTensors.front().GetTensorData<float>();
    return {scores[0], scores[1]};
  }

  Gaudi::Property<std::string> m_modelPath{
      this, "ONNXModelPath", "GaudiTutorial/modeldev/pointnet_outputs/pointnet_simplecalo.onnx",
      "Path to the Tiny PointNet ONNX model"};

  std::size_t m_maxPoints{0};

  std::unique_ptr<Ort::MemoryInfo> m_memoryInfo{nullptr};
  std::unique_ptr<Ort::Env> m_env{nullptr};
  std::unique_ptr<Ort::Session> m_session{nullptr};
};

DECLARE_COMPONENT(MLShowerIDSolution)
