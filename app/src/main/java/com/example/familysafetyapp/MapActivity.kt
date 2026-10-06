package com.example.familysafetyapp

import android.annotation.SuppressLint
import android.content.Intent
import android.net.Uri
import android.os.Bundle
import android.view.View
import android.webkit.WebSettings
import android.webkit.WebView
import android.webkit.WebViewClient
import android.widget.Toast
import androidx.appcompat.app.AppCompatActivity
import com.google.android.material.button.MaterialButton

/**
 * MapActivity
 * 
 * Supports real Turn-by-Turn GPS Navigation & Direct Calling:
 * - Directions Button: Launches Google Maps Navigation (`google.navigation:q=lat,lng`)
 * - Call Button: Opens phone dialer (`tel:+94705550192`)
 */
class MapActivity : AppCompatActivity() {

    private var mapWebView: WebView? = null
    private val targetLat = 6.8950
    private val targetLng = 79.8560
    private val targetPhone = "+94705550192"
    private val targetName = "Grandpa Joe"

    @SuppressLint("SetJavaScriptEnabled")
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_map)

        setupWebViewMap()
        setupUI()
    }

    @SuppressLint("SetJavaScriptEnabled")
    private fun setupWebViewMap() {
        mapWebView = findViewById(R.id.mapWebView)
        mapWebView?.apply {
            settings.javaScriptEnabled = true
            settings.domStorageEnabled = true
            settings.cacheMode = WebSettings.LOAD_DEFAULT
            webViewClient = WebViewClient()

            // Free Standard OpenStreetMap (No API Key Required)
            val htmlContent = """
                <!DOCTYPE html>
                <html>
                <head>
                    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
                    <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css"/>
                    <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
                    <style>
                        body, html, #map { margin: 0; padding: 0; width: 100%; height: 100%; }
                        .marker-pin {
                            width: 38px; height: 38px; border-radius: 50%; border: 3px solid #fff;
                            box-shadow: 0 4px 10px rgba(0,0,0,0.3); background-size: cover; background-position: center;
                        }
                    </style>
                </head>
                <body>
                    <div id="map"></div>
                    <script>
                        var map = L.map('map', { zoomControl: false }).setView([6.9271, 79.8612], 13);
                        
                        // Standard OpenStreetMap Tiles (100% Free)
                        L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
                            maxZoom: 19,
                            attribution: '&copy; OpenStreetMap contributors'
                        }).addTo(map);

                        // Grandpa Joe Safe Zone Circle
                        L.circle([6.8950, 79.8560], {
                            radius: 300,
                            color: '#3B82F6',
                            fillColor: '#3B82F6',
                            fillOpacity: 0.15,
                            weight: 2
                        }).addTo(map);

                        // Sarah Marker
                        var sarahIcon = L.divIcon({
                            className: 'custom-pin',
                            html: '<div class="marker-pin" style="background-image: url(https://images.unsplash.com/photo-1494790108377-be9c29b29330?w=150); border-color: #3B82F6;"></div>',
                            iconSize: [38, 38], iconAnchor: [19, 19]
                        });
                        L.marker([6.9360, 79.8450], { icon: sarahIcon }).addTo(map);

                        // Leo Marker
                        var leoIcon = L.divIcon({
                            className: 'custom-pin',
                            html: '<div class="marker-pin" style="background-image: url(https://images.unsplash.com/photo-1543610892-0b1f7e6d8ac1?w=150); border-color: #10B981;"></div>',
                            iconSize: [38, 38], iconAnchor: [19, 19]
                        });
                        L.marker([6.9200, 79.8700], { icon: leoIcon }).addTo(map);

                        // Grandpa Joe Marker
                        var joeIcon = L.divIcon({
                            className: 'custom-pin',
                            html: '<div class="marker-pin" style="background-image: url(https://images.unsplash.com/photo-1472099645785-5658abf4ff4e?w=150); border-color: #F59E0B;"></div>',
                            iconSize: [38, 38], iconAnchor: [19, 19]
                        });
                        L.marker([6.8950, 79.8560], { icon: joeIcon }).addTo(map);

                        // Live Route to Grandpa Joe
                        var route = [
                            [6.9360, 79.8450],
                            [6.9271, 79.8480],
                            [6.9150, 79.8510],
                            [6.8950, 79.8560]
                        ];
                        L.polyline(route, { color: '#2563EB', weight: 4, opacity: 0.8, dashArray: '6, 6' }).addTo(map);
                    </script>
                </body>
                </html>
            """.trimIndent()

            loadDataWithBaseURL("https://openstreetmap.org", htmlContent, "text/html", "UTF-8", null)
        }
    }

    private fun setupUI() {
        // Direct Phone Call
        findViewById<MaterialButton>(R.id.btnMapCall)?.setOnClickListener {
            val callIntent = Intent(Intent.ACTION_DIAL, Uri.parse("tel:$targetPhone"))
            try {
                startActivity(callIntent)
            } catch (e: Exception) {
                Toast.makeText(this, "Calling $targetName ($targetPhone)", Toast.LENGTH_SHORT).show()
            }
        }

        // Live Turn-by-Turn GPS Navigation
        findViewById<MaterialButton>(R.id.btnMapDirections)?.setOnClickListener {
            launchTurnByTurnNavigation()
        }

        findViewById<View>(R.id.mapNavHome)?.setOnClickListener {
            finish()
        }
    }

    private fun launchTurnByTurnNavigation() {
        // 1. Try launching Google Maps Turn-by-Turn navigation mode
        val gmmIntentUri = Uri.parse("google.navigation:q=$targetLat,$targetLng&mode=d")
        val mapIntent = Intent(Intent.ACTION_VIEW, gmmIntentUri).apply {
            setPackage("com.google.android.apps.maps")
        }

        try {
            startActivity(mapIntent)
        } catch (e: Exception) {
            // 2. Fallback to generic map URI or browser
            val webNavUri = Uri.parse("https://www.google.com/maps/dir/?api=1&destination=$targetLat,$targetLng")
            val webIntent = Intent(Intent.ACTION_VIEW, webNavUri)
            startActivity(webIntent)
        }
    }
}
