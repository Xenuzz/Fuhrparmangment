package com.trucklog

import java.time.Instant

/**
 * Request and local entities used by app networking and persistence.
 */
data class LoginRequest(val username: String, val password: String)

data class GpsPointEntity(
    val id: Long = 0,
    val tripId: Int,
    val timestamp: String,
    val latitude: Double,
    val longitude: Double,
    val speedKmh: Double,
    val synced: Boolean = false,
    val retryCount: Int = 0
)

/**
 * Break data recorded while the trip is paused.
 */
data class BreakRecord(
    val tripId: Int,
    val startTime: String,
    val endTime: String,
    val durationMinutes: Int
)

/**
 * Tracking state machine values for automated trip lifecycle.
 */
enum class TripTrackingState {
    IDLE,
    MOVING,
    DRIVING,
    PAUSED
}

/**
 * Snapshot used by the tracking notification.
 */
data class TrackingStatus(
    val state: TripTrackingState,
    val speedKmh: Double,
    val activeTripId: Int?,
    val timestamp: String = Instant.now().toString()
)
