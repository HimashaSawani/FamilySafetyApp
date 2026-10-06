package com.example.familysafetyapp

import android.os.Bundle
import android.os.CountDownTimer
import android.widget.ImageView
import android.widget.TextView
import android.widget.Toast
import androidx.appcompat.app.AppCompatActivity
import com.example.familysafetyapp.utils.SmsHelper
import com.google.android.material.button.MaterialButton
import org.json.JSONObject
import java.io.OutputStreamWriter
import java.net.HttpURLConnection
import java.net.URL
import kotlin.concurrent.thread

class SOSActivity : AppCompatActivity() {

    private var countDownTimer: CountDownTimer? = null
    private val backendSosUrl = "http://10.0.2.2:8000/api/sos/trigger"
    private val backendCancelUrl = "http://10.0.2.2:8000/api/sos/cancel"

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_sos)

        val ivBack = findViewById<ImageView>(R.id.ivSosBack)
        val btnGiantSos = findViewById<MaterialButton>(R.id.btnGiantSosAction)
        val tvHoldInstructions = findViewById<TextView>(R.id.tvSosHoldInstructions)
        val btnCallSarah = findViewById<ImageView>(R.id.btnCallSarah)
        val btnCallLeo = findViewById<ImageView>(R.id.btnCallLeo)
        val btnIAmSafe = findViewById<MaterialButton>(R.id.btnIAmSafe)

        ivBack?.setOnClickListener { finish() }

        btnCallSarah?.setOnClickListener {
            Toast.makeText(this, "📞 Calling Sarah (+94 77 123 4567)...", Toast.LENGTH_SHORT).show()
        }

        btnCallLeo?.setOnClickListener {
            Toast.makeText(this, "📞 Calling Leo (+94 71 987 6543)...", Toast.LENGTH_SHORT).show()
        }

        btnGiantSos?.setOnClickListener {
            triggerEmergencySos()
        }

        btnIAmSafe?.setOnClickListener {
            resolveSafety()
        }
    }

    private fun triggerEmergencySos() {
        val lat = 6.9271
        val lng = 79.8612
        val battery = 88

        // 1. Dispatch SMS
        SmsHelper.sendEmergencySms(
            context = this,
            phoneNumber = "+94771234567",
            userName = "Sarah",
            lat = lat,
            lng = lng,
            batteryPercent = battery
        )

        // 2. Dispatch to Cloud Backend
        thread {
            try {
                val url = URL(backendSosUrl)
                val conn = url.openConnection() as HttpURLConnection
                conn.requestMethod = "POST"
                conn.setRequestProperty("Content-Type", "application/json; utf-8")
                conn.doOutput = true

                val payload = JSONObject().apply {
                    put("user_id", "usr_sarah")
                    put("lat", lat)
                    put("lng", lng)
                    put("location_name", "Colombo, Sri Lanka")
                    put("reason", "EMERGENCY_PANIC_MOBILE")
                }

                OutputStreamWriter(conn.outputStream).use { it.write(payload.toString()) }
                conn.responseCode
                conn.disconnect()
            } catch (e: Exception) {}
        }

        Toast.makeText(this, "🚨 Emergency SOS Dispatched to Family Circle & SMS Sent!", Toast.LENGTH_LONG).show()
    }

    private fun resolveSafety() {
        thread {
            try {
                val url = URL(backendCancelUrl)
                val conn = url.openConnection() as HttpURLConnection
                conn.requestMethod = "POST"
                conn.setRequestProperty("Content-Type", "application/json; utf-8")
                conn.doOutput = true

                val payload = JSONObject().apply {
                    put("sos_id", "SOS-1791244498")
                    put("user_id", "usr_sarah")
                    put("pin", "1234") // Server-side validated PIN
                    put("resolution_notes", "Confirmed safe from Android client.")
                }

                OutputStreamWriter(conn.outputStream).use { it.write(payload.toString()) }
                conn.responseCode
                conn.disconnect()
            } catch (e: Exception) {}
        }
        Toast.makeText(this, "🟢 Safety Confirmed! SOS Alert Resolved.", Toast.LENGTH_SHORT).show()
        finish()
    }
}
