package com.example.wifi_motion_sensing

import android.Manifest
import android.content.Context
import android.content.pm.PackageManager
import android.net.wifi.WifiManager
import android.os.Build
import androidx.core.app.ActivityCompat
import androidx.core.content.ContextCompat
import io.flutter.embedding.android.FlutterActivity
import io.flutter.embedding.engine.FlutterEngine
import io.flutter.plugin.common.MethodChannel

class MainActivity : FlutterActivity() {
    private val channelName = "wifi_motion/wifi"
    private val permissionRequestCode = 4101
    private var pendingResult: MethodChannel.Result? = null

    override fun configureFlutterEngine(flutterEngine: FlutterEngine) {
        super.configureFlutterEngine(flutterEngine)

        MethodChannel(flutterEngine.dartExecutor.binaryMessenger, channelName)
            .setMethodCallHandler { call, result ->
                if (call.method != "getWifiInfo") {
                    result.notImplemented()
                    return@setMethodCallHandler
                }

                if (!hasRequiredWifiPermissions()) {
                    if (pendingResult != null) {
                        result.error("PERMISSION_PENDING", "Wi-Fi permission request is already open.", null)
                        return@setMethodCallHandler
                    }
                    pendingResult = result
                    requestRequiredWifiPermissions()
                    return@setMethodCallHandler
                }

                sendWifiInfo(result)
            }
    }

    private fun requiredPermissions(): Array<String> {
        return if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.TIRAMISU) {
            arrayOf(
                Manifest.permission.NEARBY_WIFI_DEVICES,
                Manifest.permission.ACCESS_FINE_LOCATION
            )
        } else {
            arrayOf(Manifest.permission.ACCESS_FINE_LOCATION)
        }
    }

    private fun hasRequiredWifiPermissions(): Boolean {
        return requiredPermissions().all {
            ContextCompat.checkSelfPermission(this, it) == PackageManager.PERMISSION_GRANTED
        }
    }

    private fun requestRequiredWifiPermissions() {
        ActivityCompat.requestPermissions(this, requiredPermissions(), permissionRequestCode)
    }

    override fun onRequestPermissionsResult(
        requestCode: Int,
        permissions: Array<out String>,
        grantResults: IntArray
    ) {
        super.onRequestPermissionsResult(requestCode, permissions, grantResults)
        if (requestCode != permissionRequestCode) return

        val result = pendingResult ?: return
        pendingResult = null

        if (grantResults.isNotEmpty() && grantResults.all { it == PackageManager.PERMISSION_GRANTED }) {
            sendWifiInfo(result)
        } else {
            result.error(
                "PERMISSION_DENIED",
                "Wi-Fi sensing needs Nearby devices and Location permission. Enable them in App info > Permissions.",
                null
            )
        }
    }

    @Suppress("DEPRECATION")
    private fun sendWifiInfo(result: MethodChannel.Result) {
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
        } catch (error: SecurityException) {
            result.error(
                "PERMISSION_REQUIRED",
                "Android blocked Wi-Fi information. Enable Nearby devices and Location permission, and turn Location on.",
                null
            )
        } catch (error: Exception) {
            result.error("WIFI_READ_FAILED", error.message, null)
        }
    }
}
