package com.example.familysafetyapp.services

import android.app.*
import android.content.Context
import android.content.Intent
import android.location.Location
import android.location.LocationListener
import android.location.LocationManager
import android.os.BatteryManager
import android.os.Build
import android.os.IBinder
import android.util.Log
import androidx.core.app.NotificationCompat
import com.example.familysafetyapp.MainActivity
import com.example.familysafetyapp.R
import org.json.JSONObject
import java.io.OutputStreamWriter
import java.net.HttpURLConnection
import java.net.URL
import kotlin.concurrent.thread

class LocationForegroundService : Service(), LocationListener {

    private var locationManager: LocationManager? = null
    private val channelId = "family_safety_tracking_channel"
    private val notificationId = 1001
    private val backendUrl = "http://10.0.2.2:8000/api/location/update" // Default Android Emulator to Host IP

    override fun onCreate() {
        super.onCreate()
        createNotificationChannel()
        startForeground(notificationId, createNotification("AegisSafe Active: Real-Time Shield Enabled"))
        startLocationUpdates()
    }

    private fun createNotificationChannel() {
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            val channel = NotificationChannel(
                channelId,
                "Family Safety Protection Service",
                NotificationManager.IMPORTANCE_LOW
            ).apply {
                description = "Monitors real-time location and safety telemetry for your family circle."
            }
            val manager = getSystemService(NotificationManager::class.java)
            manager?.createNotificationChannel(channel)
        }
    }

    private fun createNotification(contentText: String): Notification {
        val intent = Intent(this, MainActivity::class.java)
        val pendingIntent = PendingIntent.getActivity(
            this, 0, intent,
            PendingIntent.FLAG_IMMUTABLE or PendingIntent.FLAG_UPDATE_CURRENT
        )

        return NotificationCompat.Builder(this, channelId)
            .setContentTitle("Family Safety Shield")
            .setContentText(contentText)
            .setSmallIcon(android.R.drawable.ic_menu_mylocation)
            .setContentIntent(pendingIntent)
            .setOngoing(true)
            .build()
    }

    @Suppress("MissingPermission")
    private fun startLocationUpdates() {
        try {
            locationManager = getSystemService(Context.LOCATION_SERVICE) as LocationManager
            locationManager?.requestLocationUpdates(
                LocationManager.GPS_PROVIDER,
                10000L, // 10 seconds
                5f,    // 5 meters
                this
            )
            locationManager?.requestLocationUpdates(
                LocationManager.NETWORK_PROVIDER,
                10000L,
                5f,
                this
            )
        } catch (e: Exception) {
            Log.e("LocationService", "Error requesting location updates: ${e.message}")
        }
    }

    override fun onLocationChanged(location: Location) {
        val batteryLevel = getBatteryLevel()
        dispatchLocationToBackend(location.latitude, location.longitude, location.accuracy, location.speed, batteryLevel)
    }

    private fun getBatteryLevel(): Int {
        val bm = getSystemService(Context.BATTERY_SERVICE) as? BatteryManager
        return bm?.getIntProperty(BatteryManager.BATTERY_PROPERTY_CAPACITY) ?: 85
    }

    private fun dispatchLocationToBackend(lat: Double, lng: Double, accuracy: Float, speed: Float, battery: Int) {
        thread {
            try {
                val url = URL(backendUrl)
                val conn = url.openConnection() as HttpURLConnection
                conn.requestMethod = "POST"
                conn.setRequestProperty("Content-Type", "application/json; utf-8")
                conn.doOutput = true
                conn.connectTimeout = 3000
                conn.readTimeout = 3000

                val json = JSONObject().apply {
                    put("user_id", "usr_child")
                    put("lat", lat)
                    put("lng", lng)
                    put("accuracy", accuracy.toDouble())
                    put("speed", speed.toDouble())
                    put("battery", battery)
                    put("is_charging", false)
                    put("status", "online")
                }

                OutputStreamWriter(conn.outputStream).use { it.write(json.toString()) }
                val responseCode = conn.responseCode
                Log.d("LocationService", "Telemetry push response: $responseCode")
                conn.disconnect()
            } catch (e: Exception) {
                Log.w("LocationService", "Telemetry sync skip: ${e.message}")
            }
        }
    }

    override fun onDestroy() {
        super.onDestroy()
        locationManager?.removeUpdates(this)
    }

    override fun onBind(intent: Intent?): IBinder? = null
}
