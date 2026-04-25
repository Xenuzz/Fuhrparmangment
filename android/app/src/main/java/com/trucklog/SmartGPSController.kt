package com.trucklog

/**
 * Returns dynamic GPS polling intervals according to state machine status.
 */
class SmartGPSController {
    fun getIntervalMillis(state: TripTrackingState): Long {
        return when (state) {
            TripTrackingState.IDLE -> 30_000L
            TripTrackingState.MOVING -> 5_000L
            TripTrackingState.DRIVING -> 2_000L
            TripTrackingState.PAUSED -> 15_000L
        }
    }
}
