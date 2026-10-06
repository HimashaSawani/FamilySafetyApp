package com.example.familysafetyapp.utils

import android.content.Context
import android.telephony.SmsManager
import android.util.Log

object SmsHelper {
    private const val TAG = "SmsHelper"

    fun sendEmergencySms(
        context: Context,
        phoneNumber: String,
        userName: String,
        lat: Double,
        lng: Double,
        batteryPercent: Int
    ): Boolean {
        return try {
            val smsManager: SmsManager = context.getSystemService(SmsManager::class.java)
                ?: @Suppress("DEPRECATION") SmsManager.getDefault()

            val mapLink = "https://maps.google.com/?q=$lat,$lng"
            val message = "🚨 [EMERGENCY SOS ALERT]\n" +
                    "This is an automated distress message from $userName.\n" +
                    "I am in immediate distress. My live location:\n" +
                    "$mapLink\n" +
                    "Battery: $batteryPercent%"

            val parts = smsManager.divideMessage(message)
            smsManager.sendMultipartTextMessage(phoneNumber, null, parts, null, null)
            Log.i(TAG, "Emergency SMS dispatched to $phoneNumber")
            true
        } catch (e: Exception) {
            Log.e(TAG, "Failed to send emergency SMS: ${e.message}", e)
            false
        }
    }
}
