package com.trucklog

/**
 * In-memory debug status used by MainActivity for lightweight visibility into tracking state.
 */
object TrackingDebugState {
    @Volatile var currentTrackingState: String = "IDLE"
    @Volatile var gpsPointsRecorded: Int = 0
    @Volatile var lastSyncStatus: String = "never"
    @Volatile var unsyncedQueueCount: Int = 0
}
