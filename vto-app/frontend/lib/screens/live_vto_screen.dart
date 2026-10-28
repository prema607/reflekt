import 'dart:typed_data';
import 'package:camera/camera.dart';
import 'package:flutter/material.dart';
import 'package:firebase_auth/firebase_auth.dart';
import '../services/api_service.dart';
import '../services/webcam_ar_service.dart';

const categories = ['All', 'top', 'dress', 'saree', 'lehenga', 'anarkali', 'kurti'];

class LiveVtoScreen extends StatefulWidget {
  const LiveVtoScreen({super.key});
  @override
  State<LiveVtoScreen> createState() => _S();
}

class _S extends State<LiveVtoScreen> {
  final cam = WebcamArService(), api = ApiService();
  List<Garment> items = [];
  Garment? selected;
  String category = 'All';
  bool arOn = true, busy = false;
  String? resultUrl, error;
  double split = 0.5;
  Uint8List? snap;

  @override
  void initState() {
    super.initState();
    cam.init().then((_) => setState(() {})).catchError((e) => setState(() => error = 'Camera: $e'));
    _load();
  }

  Future<void> _load() async {
    try {
      items = await api.garments(category: category == 'All' ? null : category);
    } catch (e) {
      error = '$e';
    }
    if (mounted) setState(() {});
  }

  Future<void> _capture() async {
    if (selected == null) return setState(() => error = 'Pick a garment first');
    setState(() { busy = true; error = null; });
    try {
      ApiService.token = await FirebaseAuth.instance.currentUser?.getIdToken();
      snap = await cam.captureSnapshot();
      final id = await api.submitSnapshot(snap!, [selected!.id]);
      resultUrl = await api.waitForResult(id);
    } catch (e) {
      error = '$e'.replaceFirst('Exception: ', '');
    }
    if (mounted) setState(() => busy = false);
  }

  @override
  void dispose() { cam.dispose(); super.dispose(); }

  @override
  Widget build(BuildContext c) {
    return Scaffold(
      appBar: AppBar(title: const Text('Virtual Try-On'), actions: [
        Switch(value: arOn, onChanged: (v) => setState(() => arOn = v)),
        const Padding(padding: EdgeInsets.only(right: 12), child: Center(child: Text('Live AR'))),
      ]),
      body: Column(children: [
        SizedBox(height: 48, child: ListView(scrollDirection: Axis.horizontal, children: [
          for (final k in categories)
            Padding(padding: const EdgeInsets.all(6), child: ChoiceChip(
              label: Text(k), selected: category == k,
              onSelected: (_) { category = k; _load(); })),
        ])),
        Expanded(child: _preview()),
        if (error != null) Padding(padding: const EdgeInsets.all(8),
            child: Text(error!, style: const TextStyle(color: Colors.red))),
        SizedBox(height: 96, child: ListView(scrollDirection: Axis.horizontal, children: [
          for (final g in items) GestureDetector(
            onTap: () => setState(() => selected = g),
            child: Container(width: 76, margin: const EdgeInsets.all(6),
              decoration: BoxDecoration(border: Border.all(width: 2,
                  color: selected?.id == g.id ? Colors.pink : Colors.transparent)),
              child: Image.network(g.imageUrl, fit: BoxFit.cover,
                  errorBuilder: (_, __, ___) => const Icon(Icons.checkroom)))),
        ])),
        Padding(padding: const EdgeInsets.all(12), child: SizedBox(width: double.infinity,
          child: FilledButton.icon(
            onPressed: busy ? null : _capture,
            icon: busy ? const SizedBox(width: 16, height: 16,
                child: CircularProgressIndicator(strokeWidth: 2)) : const Icon(Icons.auto_awesome),
            label: Text(busy ? 'Rendering…' : 'Capture High-Res AI Fit')))),
      ]),
    );
  }

  Widget _preview() {
    if (!cam.ready) return const Center(child: CircularProgressIndicator());
    final live = CameraPreview(cam.controller!);
    if (resultUrl == null || snap == null) return Center(child: live);
    // Side-by-side slider: left = live/snapshot, right = AI render
    return LayoutBuilder(builder: (_, box) => Stack(children: [
      Positioned.fill(child: Image.network(resultUrl!, fit: BoxFit.contain)),
      Positioned.fill(child: ClipRect(clipper: _Clip(split),
          child: Image.memory(snap!, fit: BoxFit.contain))),
      Positioned.fill(child: Slider(value: split, onChanged: (v) => setState(() => split = v))),
      Positioned(top: 8, right: 8, child: IconButton(icon: const Icon(Icons.close),
          onPressed: () => setState(() => resultUrl = null))),
    ]));
  }
}

class _Clip extends CustomClipper<Rect> {
  final double f; _Clip(this.f);
  @override Rect getClip(Size s) => Rect.fromLTWH(0, 0, s.width * f, s.height);
  @override bool shouldReclip(_Clip o) => o.f != f;
}
