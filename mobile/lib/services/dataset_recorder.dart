import 'dart:io';

import 'package:path_provider/path_provider.dart';

import '../models/wifi_sample.dart';

class DatasetRecorder {
  File? _file;
  int _sampleCount = 0;
  DateTime? _startedAt;
  String? _label;

  bool get isRecording => _file != null;
  int get sampleCount => _sampleCount;
  String? get label => _label;
  DateTime? get startedAt => _startedAt;

  Future<String> start(String label) async {
    if (isRecording) {
      throw StateError('A recording session is already active.');
    }

    final directory = await getApplicationDocumentsDirectory();
    final datasetDirectory = Directory('${directory.path}/wifi_motion_datasets');
    await datasetDirectory.create(recursive: true);

    final now = DateTime.now();
    final safeTime = now.toIso8601String().replaceAll(':', '-');
    final file = File('${datasetDirectory.path}/${label}_$safeTime.csv');

    await file.writeAsString(
      'timestamp,label,rssi_dbm,frequency_mhz,link_speed_mbps\n',
      flush: true,
    );

    _file = file;
    _sampleCount = 0;
    _startedAt = now;
    _label = label;
    return file.path;
  }

  Future<void> append(WifiSample sample) async {
    final file = _file;
    final label = _label;
    if (file == null || label == null) return;

    final line = <Object?>[
      sample.timestamp.toIso8601String(),
      label,
      sample.rssi,
      sample.frequencyMhz ?? '',
      sample.linkSpeedMbps ?? '',
    ].join(',');

    await file.writeAsString('$line\n', mode: FileMode.append, flush: false);
    _sampleCount += 1;
  }

  Future<RecordingSummary?> stop() async {
    if (_file == null || _label == null || _startedAt == null) return null;

    final summary = RecordingSummary(
      path: _file!.path,
      label: _label!,
      sampleCount: _sampleCount,
      startedAt: _startedAt!,
      endedAt: DateTime.now(),
    );

    _file = null;
    _sampleCount = 0;
    _startedAt = null;
    _label = null;
    return summary;
  }
}

class RecordingSummary {
  const RecordingSummary({
    required this.path,
    required this.label,
    required this.sampleCount,
    required this.startedAt,
    required this.endedAt,
  });

  final String path;
  final String label;
  final int sampleCount;
  final DateTime startedAt;
  final DateTime endedAt;
}
