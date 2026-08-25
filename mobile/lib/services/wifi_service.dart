import 'dart:async';

import 'package:flutter/services.dart';

import '../models/wifi_sample.dart';

class WifiService {
  static const MethodChannel _channel = MethodChannel('wifi_motion/wifi');

  Future<WifiSample> readSample() async {
    final data = await _channel.invokeMapMethod<Object?, Object?>('getWifiInfo');
    if (data == null) {
      throw StateError('No Wi-Fi data returned by Android.');
    }
    return WifiSample.fromMap(data);
  }

  Stream<WifiSample> samples({Duration interval = const Duration(seconds: 1)}) async* {
    while (true) {
      try {
        yield await readSample();
      } catch (error, stackTrace) {
        // Report the error to the UI but keep the sensing loop alive. This lets
        // the app recover automatically after temporary Wi-Fi/permission issues.
        yield* Stream<WifiSample>.error(error, stackTrace);
      }

      await Future<void>.delayed(interval);
    }
  }
}
