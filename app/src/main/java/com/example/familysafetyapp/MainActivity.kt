package com.example.familysafetyapp

import android.Manifest
import android.content.Intent
import android.content.pm.PackageManager
import android.os.Build
import android.os.Bundle
import android.view.View
import android.widget.Toast
import androidx.activity.result.contract.ActivityResultContracts
import androidx.appcompat.app.AppCompatActivity
import androidx.core.content.ContextCompat
import com.example.familysafetyapp.services.LocationForegroundService
import com.example.familysafetyapp.services.ShakeDetectorService
import com.google.android.material.button.MaterialButton
import com.google.android.material.card.MaterialCardView

class MainActivity : AppCompatActivity() {

    private val permissionLauncher = registerForActivityResult(
        ActivityResultContracts.RequestMultiplePermissions()
    ) { permissions ->
        val fineLocationGranted = permissions[Manifest.permission.ACCESS_FINE_LOCATION] ?: false
        if (fineLocationGranted) {
            startLocationService()
        }
    }

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_main)

        checkAndRequestPermissions()
        setupUI()
    }

    private fun setupUI() {
        val btnSosPill = findViewById<MaterialButton>(R.id.btnSosPill)
        val cardMiniMap = findViewById<MaterialCardView>(R.id.cardMiniMap)
        val cardGrandpaJoe = findViewById<MaterialCardView>(R.id.cardGrandpaJoe)

        val tabHome = findViewById<View>(R.id.tabHome)
        val tabMap = findViewById<View>(R.id.tabMap)
        val tabAlerts = findViewById<View>(R.id.tabAlerts)
        val tabSettings = findViewById<View>(R.id.tabSettings)

        btnSosPill?.setOnClickListener {
            startActivity(Intent(this, SOSActivity::class.java))
        }

        cardMiniMap?.setOnClickListener {
            startActivity(Intent(this, MapActivity::class.java))
        }

        cardGrandpaJoe?.setOnClickListener {
            startActivity(Intent(this, MapActivity::class.java))
        }

        tabMap?.setOnClickListener {
            startActivity(Intent(this, MapActivity::class.java))
        }

        tabAlerts?.setOnClickListener {
            Toast.makeText(this, "Safety Alerts: All 3 family members nominal and safe.", Toast.LENGTH_SHORT).show()
        }

        tabSettings?.setOnClickListener {
            startActivity(Intent(this, ContactsActivity::class.java))
        }

        startShakeService()
    }

    private fun checkAndRequestPermissions() {
        val permissionsToRequest = mutableListOf(
            Manifest.permission.ACCESS_FINE_LOCATION,
            Manifest.permission.ACCESS_COARSE_LOCATION,
            Manifest.permission.SEND_SMS,
            Manifest.permission.CALL_PHONE
        )

        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.TIRAMISU) {
            permissionsToRequest.add(Manifest.permission.POST_NOTIFICATIONS)
        }

        val missing = permissionsToRequest.filter {
            ContextCompat.checkSelfPermission(this, it) != PackageManager.PERMISSION_GRANTED
        }

        if (missing.isNotEmpty()) {
            permissionLauncher.launch(missing.toTypedArray())
        } else {
            startLocationService()
        }
    }

    private fun startLocationService() {
        val intent = Intent(this, LocationForegroundService::class.java)
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            startForegroundService(intent)
        } else {
            startService(intent)
        }
    }

    private fun startShakeService() {
        startService(Intent(this, ShakeDetectorService::class.java))
    }
}
