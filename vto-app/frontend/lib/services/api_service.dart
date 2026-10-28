import 'dart:convert';
import 'dart:typed_data';
import 'package:http/http.dart' as http;

const apiBase = String.fromEnvironment('API_BASE', defaultValue: 'http://localhost:8000');

class Garment {
  final String id, name, category, slot, imageUrl;
  final double opacity;
  Garment(this.id, this.name, this.category, this.slot, this.imageUrl, this.opacity);
  factory Garment.fromJson(Map<String, dynamic> j) {
    final c = (j['components'] as List).first as Map<String, dynamic>;
    return Garment(j['_id'], j['name'], j['category'], c['slot'], c['image_url'],
        (c['opacity'] as num).toDouble());
  }
}

class ApiService {
  /// Set to the Firebase ID token after sign-in.
  static String? token;
  Map<String, String> get _h => token == null ? {} : {'Authorization': 'Bearer $token'};
  Future<List<Garment>> garments({String? category}) async {
    final q = {'target_audience': 'women', if (category != null) 'category': category};
    final r = await http.get(Uri.parse('$apiBase/api/v1/garments').replace(queryParameters: q));
    if (r.statusCode != 200) throw Exception('Catalog failed (${r.statusCode})');
    return (jsonDecode(r.body) as List).map((e) => Garment.fromJson(e)).toList();
  }

  Future<String> submitSnapshot(Uint8List jpeg, List<String> garmentIds) async {
    final req = http.MultipartRequest('POST', Uri.parse('$apiBase/api/v1/try-on/snapshot'))
      ..headers.addAll(_h)
      ..fields['garment_ids'] = jsonEncode(garmentIds)
      ..files.add(http.MultipartFile.fromBytes('image', jpeg, filename: 'snap.jpg'));
    final res = await http.Response.fromStream(await req.send());
    if (res.statusCode == 429) throw Exception('Too many requests, wait a minute');
    if (res.statusCode != 202) throw Exception('Upload failed (${res.statusCode})');
    return jsonDecode(res.body)['job_id'];
  }

  /// Polls until COMPLETED/FAILED; returns result URL.
  Future<String> waitForResult(String jobId) async {
    for (var i = 0; i < 90; i++) {
      await Future.delayed(const Duration(seconds: 2));
      final r = await http.get(Uri.parse('$apiBase/api/v1/try-on/status/$jobId'), headers: _h);
      final j = jsonDecode(r.body);
      if (j['status'] == 'COMPLETED') return j['result_url'];
      if (j['status'] == 'FAILED') throw Exception(j['error'] ?? 'Render failed');
    }
    throw Exception('Timed out');
  }
}
