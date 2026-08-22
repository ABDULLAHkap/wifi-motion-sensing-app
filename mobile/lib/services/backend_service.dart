import 'dart:convert';
import 'dart:io';

import '../models/wifi_sample.dart';

class BackendService {
  BackendService({required this.baseUrl, this.deviceId = 'android-1', this.roomId = 'default-room'});

  final String baseUrl;
  final String deviceId;
  final String roomId;

  Future<bool> sendSample(
    WifiSample sample, {
    double? motionScore,
    String? motionState,
  }) async {
    final uri = Uri.parse('${baseUrl.replaceAll(RegExp(r'/$'), '')}/samples');
    final client = HttpClient();
    try {
      final request = await client.postUrl(uri);
      request.headers.contentType = ContentType.json;
      request.write(jsonEncode({
        'device_id': deviceId,
        'room_id': roomId,
        'timestamp': sample.timestamp.toUtc().toIso8601String(),
        'rssi': sample.rssi,
        'frequency_mhz': sample.frequencyMhz,
        'link_speed_mbps': sample.linkSpeedMbps,
        'motion_score': motionScore,
        'motion_state': motionState,
      }));
      final response = await request.close().timeout(const Duration(seconds: 5));
      await response.drain<void>();
      return response.statusCode >= 200 && response.statusCode < 300;
    } catch (_) {
      return false;
    } finally {
      client.close(force: true);
    }
  }
}
