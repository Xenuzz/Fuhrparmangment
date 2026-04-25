package com.trucklog

import android.location.Location

/**
 * Converts raw GPS samples into normalized movement information.
 */
class MotionDetector {
    fun getSpeedKmh(location: Location): Double {
        val speedMps = location.speed.toDouble().coerceAtLeast(0.0)
        return speedMps * 3.6
    }
}
