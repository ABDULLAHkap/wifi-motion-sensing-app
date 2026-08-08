import 'dart:math';

class MotionAnalysis {
  const MotionAnalysis({
    required this.score,
    required this.standardDeviation,
    required this.meanDeviation,
  });

  final double score;
  final double standardDeviation;
  final double meanDeviation;

  bool get motionDetected => score >= 0.35;
}

class MotionAnalyzer {
  const MotionAnalyzer({
    this.deviationScale = 6.0,
    this.varianceScale = 3.0,
  });

  final double deviationScale;
  final double varianceScale;

  MotionAnalysis analyze({
    required List<int> recentRssi,
    required double baseline,
  }) {
    if (recentRssi.isEmpty) {
      return const MotionAnalysis(
        score: 0,
        standardDeviation: 0,
        meanDeviation: 0,
      );
    }

    final mean = recentRssi.reduce((a, b) => a + b) / recentRssi.length;
    final variance = recentRssi
            .map((value) => pow(value - mean, 2).toDouble())
            .reduce((a, b) => a + b) /
        recentRssi.length;
    final stdDev = sqrt(variance);
    final meanDeviation = (mean - baseline).abs();

    final deviationComponent = (meanDeviation / deviationScale).clamp(0.0, 1.0);
    final varianceComponent = (stdDev / varianceScale).clamp(0.0, 1.0);

    // Blend baseline drift and short-term variation. This is a heuristic for
    // phase 1 and will be replaced/tuned using labelled real-room data.
    final score = (0.55 * deviationComponent + 0.45 * varianceComponent)
        .clamp(0.0, 1.0);

    return MotionAnalysis(
      score: score,
      standardDeviation: stdDev,
      meanDeviation: meanDeviation,
    );
  }
}
