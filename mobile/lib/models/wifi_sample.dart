class WifiSample {
  const WifiSample({
    required this.timestamp,
    required this.rssi,
    this.frequencyMhz,
    this.linkSpeedMbps,
  });

  final DateTime timestamp;
  final int rssi;
  final int? frequencyMhz;
  final int? linkSpeedMbps;

  factory WifiSample.fromMap(Map<Object?, Object?> map) {
    return WifiSample(
      timestamp: DateTime.now(),
      rssi: (map['rssi'] as num?)?.toInt() ?? -100,
      frequencyMhz: (map['frequencyMhz'] as num?)?.toInt(),
      linkSpeedMbps: (map['linkSpeedMbps'] as num?)?.toInt(),
    );
  }
}
