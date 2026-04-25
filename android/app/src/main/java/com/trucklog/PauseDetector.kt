package com.trucklog

import java.time.Duration
import java.time.Instant

/**
 * Encapsulates pause timing and break duration calculations.
 */
class PauseDetector {
    private var pauseCandidateStartedAt: Instant? = null
    private var pausedAt: Instant? = null

    fun markPauseCandidate(now: Instant) {
        if (pauseCandidateStartedAt == null) {
            pauseCandidateStartedAt = now
        }
    }

    fun clearPauseCandidate() {
        pauseCandidateStartedAt = null
    }

    fun hasReachedPauseThreshold(now: Instant, thresholdMinutes: Long): Boolean {
        val started = pauseCandidateStartedAt ?: return false
        return Duration.between(started, now).toMinutes() >= thresholdMinutes
    }

    fun startPause(now: Instant) {
        pausedAt = now
    }

    fun endPause(now: Instant): Pair<Instant, Int>? {
        val start = pausedAt ?: return null
        pausedAt = null
        pauseCandidateStartedAt = null
        val minutes = Duration.between(start, now).toMinutes().toInt().coerceAtLeast(0)
        return start to minutes
    }

    fun reset() {
        pauseCandidateStartedAt = null
        pausedAt = null
    }
}
