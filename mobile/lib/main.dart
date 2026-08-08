import 'dart:async';
import 'dart:math';

import 'package:flutter/material.dart';

import 'models/wifi_sample.dart';
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
  final WifiService _wifiService = WifiService();
  final List<int> _history = <int>[];

  StreamSubscription<WifiSample>? _subscription;
  WifiSample? _latest;
  double? _baseline;
  double _motionScore = 0;
  String? _error;

  @override
  void initState() {
    super.initState();
    _startSensing();
  }

  void _startSensing() {
    _subscription = _wifiService.samples().listen(
      (sample) {
        setState(() {
          _latest = sample;
          _error = null;
          _history.add(sample.rssi);
          if (_history.length > 30) _history.removeAt(0);
          if (_baseline != null) {
            final difference = (sample.rssi - _baseline!).abs();
            _motionScore = min(1, difference / 10);
          }
        });
      },
      onError: (Object error) {
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
            if (_error != null) ...[
              const SizedBox(height: 12),
              Card(
                child: Padding(
                  padding: const EdgeInsets.all(16),
                  child: Text(
                    'Android Wi-Fi bridge error: $_error\n\nGenerate the Flutter Android platform files and add the Kotlin MethodChannel implementation from docs/android-wifi-bridge.md.',
                  ),
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
              'People count is intentionally not shown yet. It will be added only after labelled real-room data proves that the available Wi-Fi measurements can support a useful estimate.',
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
