import 'dart:math';

class SignalAnalyzer {
  SignalAnalyzer({this.windowSize = 20});

  final int windowSize;
  final List<int> _samples = <int>[];

  double? _baselineMean;
  double? _baselineStd;

  bool get isCalibrated => _baselineMean != null && _baselineStd != null;
  double? get baselineMean => _baselineMean;
  double? get baselineStd => _baselineStd;

  void add(int rssi) {
    _samples.add(rssi);
    if (_samples.length > windowSize) {
      _samples.removeAt(0);
    }
  }

  bool get hasEnoughSamples => _samples.length >= max(10, windowSize ~/ 2);

  void calibrate() {
    if (!hasEnoughSamples) return;
    _baselineMean = _mean(_samples);
    _baselineStd = max(0.8, _std(_samples));
  }

  double get currentMean => _samples.isEmpty ? 0 : _mean(_samples);
  double get currentStd => _samples.isEmpty ? 0 : _std(_samples);

  double get meanAbsoluteChange {
    if (_samples.length < 2) return 0;
    var total = 0.0;
    for (var i = 1; i < _samples.length; i++) {
      total += (_samples[i] - _samples[i - 1]).abs();
    }
    return total / (_samples.length - 1);
  }

  double get motionScore {
    if (!isCalibrated || _samples.length < 4) return 0;

    final baselineStd = _baselineStd!;
    final meanShift = (currentMean - _baselineMean!).abs();
    final volatility = max(0.0, currentStd - baselineStd);
    final changeRate = meanAbsoluteChange;

    // Blend three independent indicators so a single noisy RSSI sample does not
    // immediately produce a high motion score.
    final shiftScore = (meanShift / max(3.0, baselineStd * 3.0)).clamp(0.0, 1.0);
    final volatilityScore = (volatility / max(2.5, baselineStd * 2.5)).clamp(0.0, 1.0);
    final changeScore = (changeRate / max(3.0, baselineStd * 2.0)).clamp(0.0, 1.0);

    final score = (shiftScore * 0.40) +
        (volatilityScore * 0.35) +
        (changeScore * 0.25);
    return score.clamp(0.0, 1.0);
  }

  bool get motionDetected => isCalibrated && motionScore >= 0.45;

  static double _mean(List<int> values) {
    return values.reduce((a, b) => a + b) / values.length;
  }

  static double _std(List<int> values) {
    if (values.length < 2) return 0;
    final mean = _mean(values);
    var sum = 0.0;
    for (final value in values) {
      final difference = value - mean;
      sum += difference * difference;
    }
    return sqrt(sum / values.length);
  }
}
