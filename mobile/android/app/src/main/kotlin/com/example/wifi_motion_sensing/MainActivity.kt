package com.example.wifi_motion_sensing

import android.Manifest
import android.content.Context
import android.content.pm.PackageManager
import android.net.wifi.WifiManager
import android.os.Build
import androidx.core.app.ActivityCompat
import io.flutter.embedding.android.FlutterActivity
import io.flutter.embedding.engine.FlutterEngine
import io.flutter.plugin.common.MethodChannel

class MainActivity : FlutterActivity() {
    private val channelName = "wifi_motion/wifi"
    private val permissionRequestCode = 4101

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

            if (!hasRequiredWifiPermission()) {
                requestRequiredWifiPermission()
                result.error(
                    "PERMISSION_REQUIRED",
                    "Grant the Wi-Fi/nearby permission, then try again.",
                    null
                )
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

    private fun hasRequiredWifiPermission(): Boolean {
        return if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.TIRAMISU) {
            ActivityCompat.checkSelfPermission(
                this,
                Manifest.permission.NEARBY_WIFI_DEVICES
            ) == PackageManager.PERMISSION_GRANTED
        } else {
            ActivityCompat.checkSelfPermission(
                this,
                Manifest.permission.ACCESS_FINE_LOCATION
            ) == PackageManager.PERMISSION_GRANTED
        }
    }

    private fun requestRequiredWifiPermission() {
        val permission = if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.TIRAMISU) {
            Manifest.permission.NEARBY_WIFI_DEVICES
        } else {
            Manifest.permission.ACCESS_FINE_LOCATION
        }

        ActivityCompat.requestPermissions(
            this,
            arrayOf(permission),
            permissionRequestCode
        )
    }
}
