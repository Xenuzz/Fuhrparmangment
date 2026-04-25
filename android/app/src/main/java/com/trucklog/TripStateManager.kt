package com.trucklog

import java.time.Duration
import java.time.Instant

/**
 * Central state machine implementation for trip auto detection.
 */
class TripStateManager(
    private val pauseDetector: PauseDetector = PauseDetector()
) {
    private var state: TripTrackingState = TripTrackingState.IDLE
    private var movingSince: Instant? = null
    private var idleSince: Instant? = null

    fun getState(): TripTrackingState = state

    fun reset() {
        state = TripTrackingState.IDLE
        movingSince = null
        idleSince = null
        pauseDetector.reset()
    }

    fun update(speedKmh: Double, now: Instant = Instant.now()): TripTrackingState {
        when (state) {
            TripTrackingState.IDLE -> {
                if (speedKmh > 5.0) {
                    state = TripTrackingState.MOVING
                    movingSince = now
                }
            }

            TripTrackingState.MOVING -> {
                if (speedKmh <= 5.0) {
                    state = TripTrackingState.IDLE
                    movingSince = null
                } else if (speedKmh > 10.0) {
                    if (movingSince == null) {
                        movingSince = now
                    }
                    if (Duration.between(movingSince, now).seconds >= 60) {
                        state = TripTrackingState.DRIVING
                        movingSince = null
                    }
                } else {
                    movingSince = now
                }
            }

            TripTrackingState.DRIVING -> {
                if (speedKmh < 3.0) {
                    pauseDetector.markPauseCandidate(now)
                    if (pauseDetector.hasReachedPauseThreshold(now, thresholdMinutes = 5)) {
                        state = TripTrackingState.PAUSED
                        pauseDetector.startPause(now)
                    }
                } else {
                    pauseDetector.clearPauseCandidate()
                }

                if (speedKmh < 1.0) {
                    if (idleSince == null) {
                        idleSince = now
                    }
                    if (Duration.between(idleSince, now).toMinutes() >= 30) {
                        state = TripTrackingState.IDLE
                        pauseDetector.reset()
                        movingSince = null
                    }
                } else {
                    idleSince = null
                }
            }

            TripTrackingState.PAUSED -> {
                if (speedKmh > 10.0) {
                    state = TripTrackingState.DRIVING
                    pauseDetector.clearPauseCandidate()
                }
                if (speedKmh > 1.0) {
                    idleSince = null
                }
            }
        }
        return state
    }

    fun completePause(now: Instant = Instant.now()): Pair<Instant, Int>? = pauseDetector.endPause(now)
}
