import 'package:flutter_test/flutter_test.dart';
import 'package:wifi_motion_sensing/services/signal_analyzer.dart';

void main() {
  group('SignalAnalyzer', () {
    test('requires enough samples before calibration', () {
      final analyzer = SignalAnalyzer(windowSize: 20);

      for (var i = 0; i < 9; i++) {
        analyzer.add(-60);
      }

      expect(analyzer.hasEnoughSamples, isFalse);
      analyzer.calibrate();
      expect(analyzer.isCalibrated, isFalse);
    });

    test('stable RSSI remains no motion after calibration', () {
      final analyzer = SignalAnalyzer(windowSize: 20);

      for (var i = 0; i < 20; i++) {
        analyzer.add(-60);
      }
      analyzer.calibrate();

      expect(analyzer.isCalibrated, isTrue);
      expect(analyzer.motionScore, closeTo(0, 0.001));
      expect(analyzer.motionDetected, isFalse);
    });

    test('strong alternating RSSI changes trigger motion', () {
      final analyzer = SignalAnalyzer(windowSize: 20);

      for (var i = 0; i < 20; i++) {
        analyzer.add(-60);
      }
      analyzer.calibrate();

      for (var i = 0; i < 20; i++) {
        analyzer.add(i.isEven ? -50 : -70);
      }

      expect(analyzer.currentStd, greaterThan(5));
      expect(analyzer.meanAbsoluteChange, greaterThan(10));
      expect(analyzer.motionScore, greaterThanOrEqualTo(0.45));
      expect(analyzer.motionDetected, isTrue);
    });
  });
}
