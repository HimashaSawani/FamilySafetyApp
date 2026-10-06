package com.example.familysafetyapp.services

import android.app.Service
import android.content.Context
import android.content.Intent
import android.hardware.Sensor
import android.hardware.SensorEvent
import android.hardware.SensorEventListener
import android.hardware.SensorManager
import android.os.IBinder
import android.util.Log
import com.example.familysafetyapp.SOSActivity
import kotlin.math.sqrt

class ShakeDetectorService : Service(), SensorEventListener {

    private var sensorManager: SensorManager? = null
    private var accelerometer: Sensor? = null
    private var lastShakeTime: Long = 0
    private val shakeThreshold = 18.0f // G-Force acceleration threshold

    override fun onCreate() {
        super.onCreate()
        sensorManager = getSystemService(Context.SENSOR_SERVICE) as SensorManager
        accelerometer = sensorManager?.getDefaultSensor(Sensor.TYPE_ACCELEROMETER)
        sensorManager?.registerListener(this, accelerometer, SensorManager.SENSOR_DELAY_UI)
    }

    override fun onSensorChanged(event: SensorEvent?) {
        if (event == null) return
        val x = event.values[0]
        val y = event.values[1]
        val z = event.values[2]

        val acceleration = sqrt((x * x + y * y + z * z).toDouble()).toFloat() - SensorManager.GRAVITY_EARTH

        if (acceleration > shakeThreshold) {
            val now = System.currentTimeMillis()
            if (now - lastShakeTime > 3000) { // Throttle 3 seconds
                lastShakeTime = now
                Log.w("ShakeDetector", "Emergency shake detected! Launching SOS Activity...")
                val sosIntent = Intent(this, SOSActivity::class.java).apply {
                    addFlags(Intent.FLAG_ACTIVITY_NEW_TASK or Intent.FLAG_ACTIVITY_CLEAR_TOP)
                    putExtra("TRIGGER_SOURCE", "SHAKE_GESTURE")
                }
                startActivity(sosIntent)
            }
        }
    }

    override fun onAccuracyChanged(sensor: Sensor?, accuracy: Int) {}

    override fun onDestroy() {
        super.onDestroy()
        sensorManager?.unregisterListener(this)
    }

    override fun onBind(intent: Intent?): IBinder? = null
}
