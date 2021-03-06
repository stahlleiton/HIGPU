import FWCore.ParameterSet.Config as cms

# customisation for running on CPUs, common parts
def customise_cpu_common(process):

    # Services

    process.CUDAService = cms.Service("CUDAService",
        enabled = cms.untracked.bool(False)
    )


    # done
    return process


# customisation for offloading to GPUs, common parts
def customise_gpu_common(process):

    # Services

    process.CUDAService = cms.Service("CUDAService",
        enabled = cms.untracked.bool(True),
        allocator = cms.untracked.PSet(
            devicePreallocate = cms.untracked.vuint32(),
        ),
        limits = cms.untracked.PSet(
            cudaLimitDevRuntimePendingLaunchCount = cms.untracked.int32(-1),
            cudaLimitDevRuntimeSyncDepth = cms.untracked.int32(-1),
            cudaLimitMallocHeapSize = cms.untracked.int32(-1),
            cudaLimitPrintfFifoSize = cms.untracked.int32(-1),
            cudaLimitStackSize = cms.untracked.int32(-1)
        )
    )

    process.load("HeterogeneousCore.CUDAServices.NVProfilerService_cfi")

    # done
    return process


# customisation for running the "Patatrack" pixel track reconstruction on CPUs
def customise_cpu_pixel(process):

    # FIXME replace the Sequences with empty ones to avoid exanding them during the (re)definition of Modules and EDAliases

    process.HLTRecoPixelTracksPPOnAASequence = cms.Sequence()
    process.HLTRecopixelvertexingSequencePPOnAA = cms.Sequence()


    # Event Setup

    process.load("RecoLocalTracker.SiPixelRecHits.PixelCPEFastESProducer_cfi")
    process.PixelCPEFastESProducer.DoLorentz = True


    # Modules and EDAliases

    # referenced in process.HLTRecoPixelTracksSequence

    from RecoLocalTracker.SiPixelRecHits.siPixelRecHitHostSoA_cfi import siPixelRecHitHostSoA as _siPixelRecHitHostSoA
    process.hltSiPixelRecHitSoAPPOnAA = _siPixelRecHitHostSoA.clone(
        beamSpot = "hltOnlineBeamSpot",
        src = "hltSiPixelClustersPPOnAA",
        convertToLegacy = True
    )

    from RecoPixelVertexing.PixelTriplets.caHitNtupletCUDA_cfi import caHitNtupletCUDA as _caHitNtupletCUDA
    process.hltPixelTracksHitQuadrupletsPPOnAA = _caHitNtupletCUDA.clone(
        idealConditions = False,
        pixelRecHitSrc = "hltSiPixelRecHitSoAPPOnAA",
        onGPU = False
    )

    process.hltPixelTracksSoAPPOnAA = cms.EDAlias(
        hltPixelTracksHitQuadrupletsPPOnAA = cms.VPSet(
            cms.PSet(
                type = cms.string("32768TrackSoATHeterogeneousSoA")
            )
        )
    )

    from RecoPixelVertexing.PixelTrackFitting.pixelTrackProducerFromSoA_cfi import pixelTrackProducerFromSoA as _pixelTrackProducerFromSoA
    process.hltPixelTracksPPOnAA = _pixelTrackProducerFromSoA.clone(
        beamSpot = "hltOnlineBeamSpot",
        pixelRecHitLegacySrc = "hltSiPixelRecHitsPPOnAA",
        trackSrc = "hltPixelTracksSoAPPOnAA"
    )


    # referenced in process.HLTRecopixelvertexingSequence

    from RecoPixelVertexing.PixelVertexFinding.pixelVertexCUDA_cfi import pixelVertexCUDA as _pixelVertexCUDA
    process.hltPixelVerticesSoAPPOnAA = _pixelVertexCUDA.clone(
        pixelTrackSrc = "hltPixelTracksSoAPPOnAA",
        onGPU = False
    )

    from RecoPixelVertexing.PixelVertexFinding.pixelVertexFromSoA_cfi import pixelVertexFromSoA as _pixelVertexFromSoA
    process.hltPixelVerticesPPOnAA = _pixelVertexFromSoA.clone(
        TrackCollection = "hltPixelTracksPPOnAA",
        beamSpot = "hltOnlineBeamSpot",
        src = "hltPixelVerticesSoAPPOnAA"
    )


    # Sequences

    process.HLTRecoPixelTracksSequencePPOnAA = cms.Sequence(
          process.hltPixelTracksFitter                      # not used here, kept for compatibility with legacy sequences
        + process.hltPixelTracksFilter                      # not used here, kept for compatibility with legacy sequences
        + process.hltPixelTracksTrackingRegionsPPOnAA       # from the original sequence
        + process.hltSiPixelRecHitSoAPPOnAA                 # pixel rechits on cpu, converted to SoA
        + process.hltPixelTracksHitQuadrupletsPPOnAA        # pixel ntuplets on cpu, in SoA format
	# process.hltPixelTracksSoA                         # alias for hltPixelTracksHitQuadruplets
        + process.hltPixelTracksPPOnAA)                     # pixel tracks on cpu, with transfer and conversion to legacy
    process.HLTRecoPixelTracksPPOnAASequence = cms.Sequence(process.HLTRecoPixelTracksSequencePPOnAA)

    process.HLTRecopixelvertexingSequencePPOnAA = cms.Sequence(
         process.HLTRecoPixelTracksSequencePPOnAA
       + process.hltPixelVerticesSoAPPOnAA                  # pixel vertices on cpu, in SoA format
       + process.hltPixelVerticesPPOnAA                     # pixel vertices on cpu, in legacy format
       + process.hltTrimmedPixelVerticesPPOnAA)             # from the original sequence
    process.HLTPixelVertexingPPOnAASequence = cms.Sequence(process.HLTRecopixelvertexingSequencePPOnAA)
    process.HLTPixelVertexingSequencePPOnAA = cms.Sequence(process.HLTRecopixelvertexingSequencePPOnAA)

    # done
    return process


# customisation for offloading the Pixel local reconstruction to GPUs
def customise_gpu_pixel(process):

    # FIXME replace the Sequences with empty ones to avoid exanding them during the (re)definition of Modules and EDAliases

    process.HLTDoLocalPixelSequencePPOnAA = cms.Sequence()
    process.HLTRecoPixelTracksPPOnAASequence = cms.Sequence()
    process.HLTRecopixelvertexingSequencePPOnAA = cms.Sequence()
    process.HLTDoLocalPixelSequencePPOnAAForLowPt = cms.Sequence()


    # Event Setup

    process.load("CalibTracker.SiPixelESProducers.siPixelGainCalibrationForHLTGPU_cfi")
    process.load("RecoLocalTracker.SiPixelClusterizer.siPixelFedCablingMapGPUWrapper_cfi")
    process.load("RecoLocalTracker.SiPixelRecHits.PixelCPEFastESProducer_cfi")
    process.PixelCPEFastESProducer.DoLorentz = True


    # Modules and EDAliases

    # referenced in process.HLTDoLocalPixelSequence

    process.hltOnlineBeamSpotCUDA = cms.EDProducer("BeamSpotToCUDA",
        src = cms.InputTag("hltOnlineBeamSpot")
    )

    from RecoLocalTracker.SiPixelClusterizer.siPixelRawToClusterCUDA_cfi import siPixelRawToClusterCUDA as _siPixelRawToClusterCUDA
    process.hltSiPixelClustersCUDA = _siPixelRawToClusterCUDA.clone()

    process.hltSiPixelRecHitsCUDA = cms.EDProducer("SiPixelRecHitCUDA",
        CPE = cms.string("PixelCPEFast"),
        beamSpot = cms.InputTag("hltOnlineBeamSpotCUDA"),
        src = cms.InputTag("hltSiPixelClustersCUDA")
    )

    process.hltSiPixelDigisSoA = cms.EDProducer("SiPixelDigisSoAFromCUDA",
        src = cms.InputTag("hltSiPixelClustersCUDA")
    )

    process.hltSiPixelDigisClusters = cms.EDProducer("SiPixelDigisClustersFromSoA",
        src = cms.InputTag("hltSiPixelDigisSoA")
    )

    process.hltSiPixelDigiErrorsSoA = cms.EDProducer("SiPixelDigiErrorsSoAFromCUDA",
        src = cms.InputTag("hltSiPixelClustersCUDA")
    )

    from EventFilter.SiPixelRawToDigi.siPixelDigiErrorsFromSoA_cfi import siPixelDigiErrorsFromSoA as _siPixelDigiErrorsFromSoA
    process.hltSiPixelDigiErrors = _siPixelDigiErrorsFromSoA.clone(
        UsePhase1 = True,
        digiErrorSoASrc = "hltSiPixelDigiErrorsSoA"
    )

    process.hltSiPixelRecHitsPPOnAA = cms.EDProducer("SiPixelRecHitFromSOA",
        pixelRecHitSrc = cms.InputTag("hltSiPixelRecHitsCUDA"),
        src = cms.InputTag("hltSiPixelDigisClusters")
    )
    process.hltSiPixelRecHitsPPOnAAForLowPt = process.hltSiPixelRecHitsPPOnAA.clone()

    process.hltSiPixelDigis = cms.EDAlias(
	hltSiPixelDigisClusters = cms.VPSet(
            cms.PSet(
                type = cms.string("PixelDigiedmDetSetVector")
            )
        ),
        hltSiPixelDigiErrors = cms.VPSet(
            cms.PSet(
                type = cms.string("DetIdedmEDCollection")
            ),
            cms.PSet(
                type = cms.string("SiPixelRawDataErroredmDetSetVector")
            ),
            cms.PSet(
                type = cms.string("PixelFEDChanneledmNewDetSetVector")
            )
        )
    )

    process.hltSiPixelClustersPPOnAA = cms.EDAlias(
        hltSiPixelDigisClusters = cms.VPSet(
            cms.PSet(
                type = cms.string("SiPixelClusteredmNewDetSetVector")
            )
        )
    )
    process.hltSiPixelClustersPPOnAAForLowPt = process.hltSiPixelClustersPPOnAA.clone()

    # referenced in process.HLTRecoPixelTracksSequence

    from RecoPixelVertexing.PixelTriplets.caHitNtupletCUDA_cfi import caHitNtupletCUDA as _caHitNtupletCUDA
    process.hltPixelTracksHitQuadrupletsPPOnAA = _caHitNtupletCUDA.clone(
        idealConditions = False,
        pixelRecHitSrc = "hltSiPixelRecHitsCUDA",
        onGPU = True
    )

    process.hltPixelTracksSoAPPOnAA = cms.EDProducer("PixelTrackSoAFromCUDA",
        src = cms.InputTag("hltPixelTracksHitQuadrupletsPPOnAA")
    )

    process.hltPixelTracksPPOnAA = cms.EDProducer("PixelTrackProducerFromSoA",
        beamSpot = cms.InputTag("hltOnlineBeamSpot"),
        minNumberOfHits = cms.int32(0),
        pixelRecHitLegacySrc = cms.InputTag("hltSiPixelRecHitsPPOnAA"),
        trackSrc = cms.InputTag("hltPixelTracksSoAPPOnAA")
    )

    # referenced in process.HLTRecopixelvertexingSequence

    from RecoPixelVertexing.PixelVertexFinding.pixelVertexCUDA_cfi import pixelVertexCUDA as _pixelVertexCUDA
    process.hltPixelVerticesCUDAPPOnAA = _pixelVertexCUDA.clone(
        pixelTrackSrc = "hltPixelTracksHitQuadrupletsPPOnAA",
        onGPU = True
    )

    process.hltPixelVerticesSoAPPOnAA = cms.EDProducer("PixelVertexSoAFromCUDA",
        src = cms.InputTag("hltPixelVerticesCUDAPPOnAA")
    )

    process.hltPixelVerticesPPOnAA = cms.EDProducer("PixelVertexProducerFromSoA",
        src = cms.InputTag("hltPixelVerticesSoAPPOnAA"),
        beamSpot = cms.InputTag("hltOnlineBeamSpot"),
        TrackCollection = cms.InputTag("hltPixelTracksPPOnAA")
    )


    # Sequences

    HLTLocalPixelGPUSequence = cms.Sequence(
	process.hltOnlineBeamSpotCUDA			    # transfer the beamspot to the gpu
        + process.hltSiPixelClustersCUDA                    # digis and clusters on gpu
        + process.hltSiPixelRecHitsCUDA                     # rechits on gpu
        + process.hltSiPixelDigisSoA                        # copy to host
        + process.hltSiPixelDigisClusters                   # convert to legacy
        + process.hltSiPixelDigiErrorsSoA                   # copy to host
        + process.hltSiPixelDigiErrors)                     # convert to legacy

    process.HLTDoLocalPixelSequencePPOnAA = cms.Sequence(
	  HLTLocalPixelGPUSequence
        # process.hltSiPixelDigis                           # replaced by an alias
        # process.hltSiPixelClustersPPOnAA                  # replaced by an alias
        + process.hltSiPixelClustersCachePPOnAA             # not used here, kept for compatibility with legacy sequences
        + process.hltSiPixelRecHitsPPOnAA)                  # convert to legacy

    process.HLTDoLocalPixelSequencePPOnAAForLowPt = cms.Sequence(
          HLTLocalPixelGPUSequence
        # process.hltSiPixelDigis                           # replaced by an alias
        # process.hltSiPixelClustersPPOnAAForLowPt          # replaced by an alias
        + process.hltSiPixelClustersCachePPOnAAForLowPt     # not used here, kept for compatibility with legacy sequences
        + process.hltSiPixelRecHitsPPOnAAForLowPt)

    process.HLTRecoPixelTracksSequencePPOnAA = cms.Sequence(
	  process.hltPixelTracksFitter                      # not used here, kept for compatibility with legacy sequences
        + process.hltPixelTracksFilter                      # not used here, kept for compatibility with legacy sequences
        + process.hltPixelTracksTrackingRegionsPPOnAA       # from the original sequence
        + process.hltPixelTracksHitQuadrupletsPPOnAA        # pixel ntuplets on gpu, in SoA format
        + process.hltPixelTracksSoAPPOnAA                   # pixel ntuplets on cpu, in SoA format
        + process.hltPixelTracksPPOnAA)                     # pixel tracks on gpu, with transfer and conversion to legacy
    process.HLTRecoPixelTracksPPOnAASequence = cms.Sequence(process.HLTRecoPixelTracksSequencePPOnAA)

    process.HLTRecopixelvertexingSequencePPOnAA = cms.Sequence(
       	 process.HLTRecoPixelTracksSequencePPOnAA
       + process.hltPixelVerticesCUDAPPOnAA                 # pixel vertices on gpu, in SoA format
       + process.hltPixelVerticesSoAPPOnAA                  # pixel vertices on cpu, in SoA format
       + process.hltPixelVerticesPPOnAA                     # pixel vertices on cpu, in legacy format
       + process.hltTrimmedPixelVerticesPPOnAA)             # from the original sequence
    process.HLTPixelVertexingPPOnAASequence = cms.Sequence(process.HLTRecopixelvertexingSequencePPOnAA)
    process.HLTPixelVertexingSequencePPOnAA = cms.Sequence(process.HLTRecopixelvertexingSequencePPOnAA)


    # done

    return process


# customisation for offloading the ECAL local reconstruction to GPUs
# TODO find automatically the list of Sequences to be updated
def customise_gpu_ecal(process):

    # FIXME replace the Sequences with empty ones to avoid exanding them during the (re)definition of Modules and EDAliases

    process.HLTDoFullUnpackingEgammaEcalMFSequence = cms.Sequence()
    process.HLTDoFullUnpackingEgammaEcalWithoutPreshowerSequence = cms.Sequence()
    process.HLTDoFullUnpackingEgammaEcalSequence = cms.Sequence()


    # Event Setup

    process.load("EventFilter.EcalRawToDigi.ecalElectronicsMappingGPUESProducer_cfi")
    process.load("RecoLocalCalo.EcalRecProducers.ecalGainRatiosGPUESProducer_cfi")
    process.load("RecoLocalCalo.EcalRecProducers.ecalPedestalsGPUESProducer_cfi")
    process.load("RecoLocalCalo.EcalRecProducers.ecalPulseCovariancesGPUESProducer_cfi")
    process.load("RecoLocalCalo.EcalRecProducers.ecalPulseShapesGPUESProducer_cfi")
    process.load("RecoLocalCalo.EcalRecProducers.ecalSamplesCorrelationGPUESProducer_cfi")
    process.load("RecoLocalCalo.EcalRecProducers.ecalTimeBiasCorrectionsGPUESProducer_cfi")
    process.load("RecoLocalCalo.EcalRecProducers.ecalTimeCalibConstantsGPUESProducer_cfi")


    # Modules and EDAliases

    process.hltEcalDigisGPU = cms.EDProducer("EcalRawToDigiGPU",
        InputLabel = cms.InputTag("rawDataCollector"),
        FEDs = cms.vint32(
            601, 602, 603, 604, 605,
            606, 607, 608, 609, 610,
            611, 612, 613, 614, 615,
            616, 617, 618, 619, 620,
            621, 622, 623, 624, 625,
            626, 627, 628, 629, 630,
            631, 632, 633, 634, 635,
            636, 637, 638, 639, 640,
            641, 642, 643, 644, 645,
            646, 647, 648, 649, 650,
            651, 652, 653, 654
        ),
        digisLabelEB = cms.string('ebDigis'),
        digisLabelEE = cms.string('eeDigis'),
        maxChannels = cms.uint32(4 * 20000)
    )

    process.hltEcalDigis = cms.EDProducer("EcalCPUDigisProducer",
        digisInLabelEB = cms.InputTag("hltEcalDigisGPU", "ebDigis"),
        digisInLabelEE = cms.InputTag("hltEcalDigisGPU", "eeDigis"),
        digisOutLabelEB = cms.string('ebDigis'),
        digisOutLabelEE = cms.string('eeDigis'),
        produceDummyIntegrityCollections = cms.bool(True)
    )

    process.hltEcalUncalibRecHitGPU = cms.EDProducer("EcalUncalibRecHitProducerGPU",
        digisLabelEB = cms.InputTag("hltEcalDigisGPU", "ebDigis"),
        digisLabelEE = cms.InputTag("hltEcalDigisGPU", "eeDigis"),
        recHitsLabelEB = cms.string("EcalUncalibRecHitsEB"),
        recHitsLabelEE = cms.string("EcalUncalibRecHitsEE"),
        EBamplitudeFitParameters = cms.vdouble(1.138, 1.652),
        EBtimeConstantTerm = cms.double(0.6),
        EBtimeFitLimits_Lower = cms.double(0.2),
        EBtimeFitLimits_Upper = cms.double(1.4),
        EBtimeFitParameters = cms.vdouble(-2.015452, 3.130702, -12.3473, 41.88921, -82.83944, 91.01147, -50.35761, 11.05621),
        EBtimeNconst = cms.double(28.5),
        EEamplitudeFitParameters = cms.vdouble(1.89, 1.4),
        EEtimeConstantTerm = cms.double(1.0),
        EEtimeFitLimits_Lower = cms.double(0.2),
        EEtimeFitLimits_Upper = cms.double(1.4),
        EEtimeFitParameters = cms.vdouble(-2.390548, 3.553628, -17.62341, 67.67538, -133.213, 140.7432, -75.41106, 16.20277),
        EEtimeNconst = cms.double(31.8),
        amplitudeThresholdEB = cms.double(10.0),
        amplitudeThresholdEE = cms.double(10.0),
        outOfTimeThresholdGain12mEB = cms.double(5.0),
        outOfTimeThresholdGain12mEE = cms.double(1000.0),
        outOfTimeThresholdGain12pEB = cms.double(5.0),
        outOfTimeThresholdGain12pEE = cms.double(1000.0),
        outOfTimeThresholdGain61mEB = cms.double(5.0),
        outOfTimeThresholdGain61mEE = cms.double(1000.0),
        outOfTimeThresholdGain61pEB = cms.double(5.0),
        outOfTimeThresholdGain61pEE = cms.double(1000.0),
        kernelMinimizeThreads = cms.vuint32(32, 1, 1),
        maxNumberHits = cms.uint32(4 * 20000),
        shouldRunTimingComputation = cms.bool(False)
    )

    process.hltEcalUncalibRecHitSoA = cms.EDProducer("EcalCPUUncalibRecHitProducer",
        containsTimingInformation = cms.bool(False),
        recHitsInLabelEB = cms.InputTag("hltEcalUncalibRecHitGPU", "EcalUncalibRecHitsEB"),
        recHitsInLabelEE = cms.InputTag("hltEcalUncalibRecHitGPU", "EcalUncalibRecHitsEE"),
        recHitsOutLabelEB = cms.string('EcalUncalibRecHitsEB'),
        recHitsOutLabelEE = cms.string('EcalUncalibRecHitsEE')
    )

    process.hltEcalUncalibRecHit = cms.EDProducer("EcalUncalibRecHitConvertGPU2CPUFormat",
        recHitsLabelGPUEB = cms.InputTag("hltEcalUncalibRecHitSoA", "EcalUncalibRecHitsEB"),
        recHitsLabelGPUEE = cms.InputTag("hltEcalUncalibRecHitSoA", "EcalUncalibRecHitsEE"),
        recHitsLabelCPUEB = cms.string("EcalUncalibRecHitsEB"),
        recHitsLabelCPUEE = cms.string("EcalUncalibRecHitsEE")
    )


    # Sequences

    process.HLTDoFullUnpackingEgammaEcalMFSequence = cms.Sequence(
        process.hltEcalDigisGPU
      + process.hltEcalDigis
      + process.hltEcalPreshowerDigis
      + process.hltEcalUncalibRecHitGPU
      + process.hltEcalUncalibRecHitSoA
      + process.hltEcalUncalibRecHit
      + process.hltEcalDetIdToBeRecovered
      + process.hltEcalRecHit
      + process.hltEcalPreshowerRecHit)

    process.HLTDoFullUnpackingEgammaEcalWithoutPreshowerSequence = cms.Sequence(
        process.hltEcalDigisGPU
      + process.hltEcalDigis
      + process.hltEcalUncalibRecHitGPU
      + process.hltEcalUncalibRecHitSoA
      + process.hltEcalUncalibRecHit
      + process.hltEcalDetIdToBeRecovered
      + process.hltEcalRecHit)

    process.HLTDoFullUnpackingEgammaEcalSequence = cms.Sequence(
        process.hltEcalDigisGPU
      + process.hltEcalDigis
      + process.hltEcalPreshowerDigis
      + process.hltEcalUncalibRecHitGPU
      + process.hltEcalUncalibRecHitSoA
      + process.hltEcalUncalibRecHit
      + process.hltEcalDetIdToBeRecovered
      + process.hltEcalRecHit
      + process.hltEcalPreshowerRecHit)


    # done
    return process


# customisation for running on CPUs
def customise_for_Patatrack_on_cpu(process):
    process = customise_cpu_common(process)
    process = customise_cpu_pixel(process)
    return process


# customisation for offloading to GPUs
def customise_for_Patatrack_on_gpu(process):
    process = customise_gpu_common(process)
    process = customise_gpu_pixel(process)
    process = customise_gpu_ecal(process)
    return process

