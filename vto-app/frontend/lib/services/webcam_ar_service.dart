import 'dart:typed_data';
import 'package:camera/camera.dart';
import 'package:flutter/foundation.dart';

/// Camera lifecycle + snapshot capture. On web, MediaPipe/WebGL run in web/ar.js
/// (window.vtoAR) against the page's <video>/<canvas>, so frames never leave the device.
class WebcamArService {
  CameraController? controller;

  Future<void> init() async {
    final cams = await availableCameras();
    final cam = cams.firstWhere((c) => c.lensDirection == CameraLensDirection.front,
        orElse: () => cams.first);
    controller = CameraController(cam, ResolutionPreset.high, enableAudio: false);
    await controller!.initialize();
  }

  Future<Uint8List> captureSnapshot() async {
    final f = await controller!.takePicture();
    return await f.readAsBytes();
  }

  bool get ready => controller?.value.isInitialized ?? false;
  bool get arSupported => kIsWeb; // native AR overlay: add google_mlkit_pose_detection
  void dispose() => controller?.dispose();
}
