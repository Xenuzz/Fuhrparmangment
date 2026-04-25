package com.trucklog

import android.app.Notification
import android.app.NotificationChannel
import android.app.NotificationManager
import android.app.Service
import android.content.Intent
import android.location.Location
import android.os.Build
import android.os.IBinder
import androidx.core.app.NotificationCompat
import com.google.android.gms.location.*
import java.time.Instant

/**
 * Foreground service that records location updates and stores them in SQLite.
 */
class TrackingService : Service() {
    private lateinit var fusedLocationClient: FusedLocationProviderClient
    private lateinit var locationCallback: LocationCallback
    private lateinit var localDb: LocalGpsDatabase

    override fun onCreate() {
        super.onCreate()
        fusedLocationClient = LocationServices.getFusedLocationProviderClient(this)
        localDb = LocalGpsDatabase(this)
        createNotificationChannel()
        startForeground(NOTIFICATION_ID, buildNotification())
    }

    override fun onStartCommand(intent: Intent?, flags: Int, startId: Int): Int {
        val tripId = intent?.getIntExtra(EXTRA_TRIP_ID, -1) ?: -1
        if (tripId <= 0) {
            stopSelf()
            return START_NOT_STICKY
        }

        val intervalMs = AppConfig.getGpsIntervalSeconds() * 1000
        val request = LocationRequest.Builder(Priority.PRIORITY_HIGH_ACCURACY, intervalMs)
            .setMinUpdateIntervalMillis(intervalMs)
            .build()

        locationCallback = object : LocationCallback() {
            override fun onLocationResult(result: LocationResult) {
                result.lastLocation?.let { location -> savePoint(tripId, location) }
            }
        }

        try {
            fusedLocationClient.requestLocationUpdates(request, locationCallback, mainLooper)
        } catch (_: SecurityException) {
            stopSelf()
        }

        return START_STICKY
    }

    override fun onDestroy() {
        fusedLocationClient.removeLocationUpdates(locationCallback)
        super.onDestroy()
    }

    override fun onBind(intent: Intent?): IBinder? = null

    private fun savePoint(tripId: Int, location: Location) {
        val point = GpsPointEntity(
            tripId = tripId,
            timestamp = Instant.now().toString(),
            latitude = location.latitude,
            longitude = location.longitude,
            speedKmh = location.speed * 3.6
        )
        localDb.insertPoint(point)
    }

    private fun buildNotification(): Notification {
        return NotificationCompat.Builder(this, CHANNEL_ID)
            .setContentTitle("TruckLog Tracking")
            .setContentText("GPS tracking in progress")
            .setSmallIcon(android.R.drawable.ic_menu_mylocation)
            .setOngoing(true)
            .build()
    }

    private fun createNotificationChannel() {
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            val channel = NotificationChannel(CHANNEL_ID, "TruckLog Tracking", NotificationManager.IMPORTANCE_LOW)
            getSystemService(NotificationManager::class.java).createNotificationChannel(channel)
        }
    }

    companion object {
        const val EXTRA_TRIP_ID = "extra_trip_id"
        private const val CHANNEL_ID = "trucklog_tracking"
        private const val NOTIFICATION_ID = 101
    }
}
