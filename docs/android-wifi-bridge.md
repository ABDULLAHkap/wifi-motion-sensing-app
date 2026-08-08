# Android Wi-Fi bridge

The Flutter app uses the MethodChannel `wifi_motion/wifi` and calls `getWifiInfo` once per second.

## Why a native bridge?

Flutter does not expose every Android Wi-Fi field directly. The native Android layer can read connection information from `WifiManager` and return the measurements to Dart.

## Android permissions

The generated Android project should declare the Wi-Fi permissions required by the Android version being targeted. Wi-Fi information can also be restricted unless the user grants the relevant nearby/location permission and location services are enabled on some Android versions.

## Kotlin MethodChannel outline

Add this logic to the generated Flutter Android `MainActivity.kt` after running `flutter create .` inside `mobile/` if the Android platform folder is missing.

```kotlin
package com.example.wifi_motion_sensing

import android.content.Context
import android.net.wifi.WifiManager
import io.flutter.embedding.android.FlutterActivity
import io.flutter.embedding.engine.FlutterEngine
import io.flutter.plugin.common.MethodChannel

class MainActivity : FlutterActivity() {
    private val channelName = "wifi_motion/wifi"

    override fun configureFlutterEngine(flutterEngine: FlutterEngine) {
        super.configureFlutterEngine(flutterEngine)

        MethodChannel(
            flutterEngine.dartExecutor.binaryMessenger,
            channelName
        ).setMethodCallHandler { call, result ->
            if (call.method != "getWifiInfo") {
                result.notImplemented()
                return@setMethodCallHandler
            }

            try {
                val wifiManager = applicationContext
                    .getSystemService(Context.WIFI_SERVICE) as WifiManager
                val info = wifiManager.connectionInfo

                result.success(
                    mapOf(
                        "rssi" to info.rssi,
                        "frequencyMhz" to info.frequency,
                        "linkSpeedMbps" to info.linkSpeed
                    )
                )
            } catch (error: Exception) {
                result.error("WIFI_READ_FAILED", error.message, null)
            }
        }
    }
}
```

## First real-device experiment

1. Keep the router, phone and furniture fixed.
2. Open the app and collect at least 30 RSSI samples.
3. Leave the room empty and press **Calibrate Room**.
4. Record the RSSI history while nobody moves.
5. Repeat while one person walks between different parts of the room.
6. Compare false positives and true motion events before attempting occupancy estimation.

RSSI is coarse and can change for reasons unrelated to human motion. Do not treat the initial motion score as a person detector until it has been validated experimentally.
