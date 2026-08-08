import 'dart:async';
import 'dart:math';

import 'package:flutter/material.dart';

import 'models/wifi_sample.dart';
import 'services/dataset_recorder.dart';
import 'services/wifi_service.dart';

void main() => runApp(const WifiMotionApp());

class WifiMotionApp extends StatelessWidget {
  const WifiMotionApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      debugShowCheckedModeBanner: false,
      title: 'Wi-Fi Motion Sensing',
      theme: ThemeData(
        brightness: Brightness.dark,
        colorSchemeSeed: Colors.cyan,
        useMaterial3: true,
      ),
      home: const MotionDashboard(),
    );
  }
}

class MotionDashboard extends StatefulWidget {
  const MotionDashboard({super.key});

  @override
  State<MotionDashboard> createState() => _MotionDashboardState();
}

class _MotionDashboardState extends State<MotionDashboard> {
  static const labels = <String>[
    'EMPTY',
    'PERSON_STILL',
    'PERSON_WALKING',
    'OBJECT_MOVING',
  ];

  final WifiService _wifiService = WifiService();
  final DatasetRecorder _recorder = DatasetRecorder();
  final List<int> _history = <int>[];

  StreamSubscription<WifiSample>? _subscription;
  WifiSample? _latest;
  double? _baseline;
  double _motionScore = 0;
  String? _error;
  String _selectedLabel = labels.first;
  bool _isRecording = false;
  int _recordedSamples = 0;
  String? _lastSavedPath;

  @override
  void initState() {
    super.initState();
    _startSensing();
  }

  void _startSensing() {
    _subscription = _wifiService.samples().listen(
      (sample) async {
        if (_isRecording) {
          await _recorder.append(sample);
        }

        if (!mounted) return;
        setState(() {
          _latest = sample;
          _error = null;
          _history.add(sample.rssi);
          if (_history.length > 60) _history.removeAt(0);
          if (_baseline != null) {
            final difference = (sample.rssi - _baseline!).abs();
            _motionScore = min(1, difference / 10);
          }
          if (_isRecording) {
            _recordedSamples = _recorder.sampleCount;
          }
        });
      },
      onError: (Object error) {
        if (!mounted) return;
        setState(() => _error = error.toString());
      },
    );
  }

  void _calibrate() {
    if (_history.isEmpty) return;
    final average = _history.reduce((a, b) => a + b) / _history.length;
    setState(() {
      _baseline = average;
      _motionScore = 0;
    });
  }

  Future<void> _toggleRecording() async {
    if (_isRecording) {
      final summary = await _recorder.stop();
      if (!mounted) return;
      setState(() {
        _isRecording = false;
        _recordedSamples = summary?.sampleCount ?? 0;
        _lastSavedPath = summary?.path;
      });
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text(
            summary == null
                ? 'Recording stopped.'
                : 'Saved ${summary.sampleCount} samples for ${summary.label}.',
          ),
        ),
      );
      return;
    }

    if (_latest == null) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Wait for Wi-Fi data before recording.')),
      );
      return;
    }

    try {
      final path = await _recorder.start(_selectedLabel);
      if (!mounted) return;
      setState(() {
        _isRecording = true;
        _recordedSamples = 0;
        _lastSavedPath = path;
      });
    } catch (error) {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('Could not start recording: $error')),
      );
    }
  }

  @override
  void dispose() {
    _subscription?.cancel();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final connected = _latest != null;
    final calibrated = _baseline != null;
    final moving = calibrated && _motionScore >= 0.3;

    return Scaffold(
      appBar: AppBar(
        title: const Text('Wi-Fi Motion Sensing'),
        actions: [
          Padding(
            padding: const EdgeInsets.only(right: 16),
            child: Icon(
              connected ? Icons.wifi : Icons.wifi_off,
              color: connected ? Colors.greenAccent : Colors.orangeAccent,
            ),
          ),
        ],
      ),
      body: SafeArea(
        child: ListView(
          padding: const EdgeInsets.all(16),
          children: [
            Card(
              child: Padding(
                padding: const EdgeInsets.all(24),
                child: Column(
                  children: [
                    Icon(
                      moving ? Icons.directions_run : Icons.sensors,
                      size: 76,
                    ),
                    const SizedBox(height: 12),
                    Text(
                      !connected
                          ? 'Waiting for Wi-Fi data'
                          : !calibrated
                              ? 'Calibration required'
                              : moving
                                  ? 'Motion detected'
                                  : 'Room stable',
                      style: Theme.of(context).textTheme.headlineSmall,
                      textAlign: TextAlign.center,
                    ),
                    const SizedBox(height: 8),
                    Text(
                      calibrated
                          ? 'Motion confidence ${(100 * _motionScore).round()}%'
                          : 'Collect samples, keep the phone fixed, then calibrate the room.',
                      textAlign: TextAlign.center,
                    ),
                  ],
                ),
              ),
            ),
            const SizedBox(height: 12),
            Row(
              children: [
                Expanded(
                  child: _MetricCard(
                    label: 'RSSI',
                    value: _latest == null ? '--' : '${_latest!.rssi} dBm',
                    icon: Icons.network_wifi,
                  ),
                ),
                const SizedBox(width: 12),
                Expanded(
                  child: _MetricCard(
                    label: 'Motion',
                    value: '${(_motionScore * 100).round()}%',
                    icon: Icons.motion_photos_on,
                  ),
                ),
              ],
            ),
            const SizedBox(height: 12),
            Row(
              children: [
                Expanded(
                  child: _MetricCard(
                    label: 'Frequency',
                    value: _latest?.frequencyMhz == null
                        ? '--'
                        : '${_latest!.frequencyMhz} MHz',
                    icon: Icons.cell_tower,
                  ),
                ),
                const SizedBox(width: 12),
                Expanded(
                  child: _MetricCard(
                    label: 'Link speed',
                    value: _latest?.linkSpeedMbps == null
                        ? '--'
                        : '${_latest!.linkSpeedMbps} Mbps',
                    icon: Icons.speed,
                  ),
                ),
              ],
            ),
            const SizedBox(height: 12),
            Card(
              child: Padding(
                padding: const EdgeInsets.all(16),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text('Signal history', style: Theme.of(context).textTheme.titleMedium),
                    const SizedBox(height: 12),
                    SizedBox(
                      height: 90,
                      child: CustomPaint(
                        painter: _SignalPainter(_history),
                        child: const SizedBox.expand(),
                      ),
                    ),
                  ],
                ),
              ),
            ),
            const SizedBox(height: 12),
            Card(
              child: Padding(
                padding: const EdgeInsets.all(16),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text('Experiment recorder', style: Theme.of(context).textTheme.titleLarge),
                    const SizedBox(height: 8),
                    const Text('Choose what is happening in the room, then record a labelled dataset.'),
                    const SizedBox(height: 16),
                    DropdownButtonFormField<String>(
                      initialValue: _selectedLabel,
                      decoration: const InputDecoration(
                        labelText: 'Experiment label',
                        border: OutlineInputBorder(),
                      ),
                      items: labels
                          .map((label) => DropdownMenuItem(value: label, child: Text(label)))
                          .toList(),
                      onChanged: _isRecording
                          ? null
                          : (value) {
                              if (value != null) setState(() => _selectedLabel = value);
                            },
                    ),
                    const SizedBox(height: 12),
                    Row(
                      children: [
                        Expanded(
                          child: Text(
                            _isRecording
                                ? 'Recording $_selectedLabel • $_recordedSamples samples'
                                : 'Recorder ready',
                          ),
                        ),
                        if (_isRecording)
                          const Padding(
                            padding: EdgeInsets.only(left: 8),
                            child: Icon(Icons.fiber_manual_record, color: Colors.redAccent),
                          ),
                      ],
                    ),
                    const SizedBox(height: 12),
                    SizedBox(
                      width: double.infinity,
                      child: FilledButton.icon(
                        onPressed: connected ? _toggleRecording : null,
                        icon: Icon(_isRecording ? Icons.stop : Icons.fiber_manual_record),
                        label: Text(_isRecording ? 'Stop & Save Dataset' : 'Start Recording'),
                      ),
                    ),
                    if (_lastSavedPath != null) ...[
                      const SizedBox(height: 12),
                      Text(
                        'Saved locally as CSV:\n$_lastSavedPath',
                        style: Theme.of(context).textTheme.bodySmall,
                      ),
                    ],
                  ],
                ),
              ),
            ),
            if (_error != null) ...[
              const SizedBox(height: 12),
              Card(
                child: Padding(
                  padding: const EdgeInsets.all(16),
                  child: Text('Android Wi-Fi bridge error: $_error'),
                ),
              ),
            ],
            const SizedBox(height: 20),
            FilledButton.icon(
              onPressed: _history.isEmpty ? null : _calibrate,
              icon: const Icon(Icons.tune),
              label: const Text('Calibrate Room'),
            ),
            const SizedBox(height: 12),
            const Text(
              'Recommended first dataset: record at least 2–5 minutes for each label while keeping the phone and router fixed. Human-count estimation will be added only after we evaluate the recorded data.',
              textAlign: TextAlign.center,
            ),
          ],
        ),
      ),
    );
  }
}

class _MetricCard extends StatelessWidget {
  const _MetricCard({required this.label, required this.value, required this.icon});

  final String label;
  final String value;
  final IconData icon;

  @override
  Widget build(BuildContext context) {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Icon(icon),
            const SizedBox(height: 14),
            Text(value, style: Theme.of(context).textTheme.titleLarge),
            Text(label),
          ],
        ),
      ),
    );
  }
}

class _SignalPainter extends CustomPainter {
  _SignalPainter(this.values);

  final List<int> values;

  @override
  void paint(Canvas canvas, Size size) {
    if (values.length < 2) return;
    final paint = Paint()
      ..color = Colors.cyanAccent
      ..strokeWidth = 2
      ..style = PaintingStyle.stroke;

    final minValue = values.reduce(min).toDouble();
    final maxValue = values.reduce(max).toDouble();
    final range = max(1, maxValue - minValue);
    final path = Path();

    for (var i = 0; i < values.length; i++) {
      final x = i * size.width / (values.length - 1);
      final normalized = (values[i] - minValue) / range;
      final y = size.height - normalized * size.height;
      if (i == 0) {
        path.moveTo(x, y);
      } else {
        path.lineTo(x, y);
      }
    }

    canvas.drawPath(path, paint);
  }

  @override
  bool shouldRepaint(covariant _SignalPainter oldDelegate) => oldDelegate.values != values;
}
