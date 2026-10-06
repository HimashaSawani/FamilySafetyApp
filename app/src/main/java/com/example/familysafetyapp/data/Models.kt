package com.example.familysafetyapp.data

data class UserLocation(
    val lat: Double,
    val lng: Double,
    val accuracy: Float,
    val speed: Float,
    val timestamp: String
)

data class CircleMember(
    val id: String,
    val name: String,
    val role: String,
    val phone: String,
    val avatar: String,
    val color: String,
    val battery: Int,
    val isCharging: Boolean,
    val location: UserLocation?
)

data class EmergencyContact(
    val id: String,
    val name: String,
    val phone: String,
    val relation: String,
    val isPrimary: Boolean = false
)

data class SOSAlert(
    val id: String,
    val userId: String,
    val userName: String,
    val lat: Double,
    val lng: Double,
    val battery: Int,
    val timestamp: String,
    val status: String
)
