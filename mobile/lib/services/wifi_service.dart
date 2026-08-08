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
      yield await readSample();
      await Future<void>.delayed(interval);
    }
  }
}
