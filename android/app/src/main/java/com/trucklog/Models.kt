package com.trucklog

/**
 * Request and local entities used by app networking and persistence.
 */
data class LoginRequest(val username: String, val password: String)
data class GpsPointEntity(
    val tripId: Int,
    val timestamp: String,
    val latitude: Double,
    val longitude: Double,
    val speedKmh: Double
)
