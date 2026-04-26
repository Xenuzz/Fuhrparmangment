package com.trucklog

import android.app.Notification
import android.app.NotificationChannel
import android.app.NotificationManager
import android.app.Service
import android.content.Intent
import android.location.Location
import android.os.Build
import android.os.Handler
import android.os.IBinder
import android.os.Looper
import androidx.core.app.NotificationCompat
import com.google.android.gms.location.FusedLocationProviderClient
import com.google.android.gms.location.LocationCallback
import com.google.android.gms.location.LocationRequest
import com.google.android.gms.location.LocationResult
import com.google.android.gms.location.LocationServices
import com.google.android.gms.location.Priority
import java.time.Instant
import kotlin.concurrent.thread

/**
 * Foreground service that handles smart GPS, automated state transitions, trip lifecycle, and queued sync.
 */
class TrackingService : Service() {
    private lateinit var fusedLocationClient: FusedLocationProviderClient
    private lateinit var locationCallback: LocationCallback
    private lateinit var localDb: LocalGpsDatabase

    private val motionDetector = MotionDetector()
    private val stateManager = TripStateManager()
    private val gpsController = SmartGPSController()
    private val syncHandler = Handler(Looper.getMainLooper())

    private val apiClient = ApiClient()
    private var authToken: String? = null
    private var activeTripId: Int? = null
    private var currentState: TripTrackingState = TripTrackingState.IDLE

    private val syncRunnable = object : Runnable {
        override fun run() {
            syncQueuedPoints()
            val min = AppConfig.getSyncIntervalMinSeconds()
            val max = AppConfig.getSyncIntervalMaxSeconds().coerceAtLeast(min)
            val next = (min..max).random() * 1000L
            syncHandler.postDelayed(this, next)
        }
    }

    override fun onCreate() {
        super.onCreate()
        fusedLocationClient = LocationServices.getFusedLocationProviderClient(this)
        localDb = LocalGpsDatabase(this)
        createNotificationChannel()
        TrackingDebugState.currentTrackingState = currentState.name
        TrackingDebugState.lastSyncStatus = "service_created"
        TrackingDebugState.unsyncedQueueCount = localDb.countUnsyncedPoints()
        startForeground(NOTIFICATION_ID, buildNotification(TrackingStatus(currentState, 0.0, null)))
        initLocationCallback()
    }

    override fun onStartCommand(intent: Intent?, flags: Int, startId: Int): Int {
        when (intent?.action) {
            ACTION_START -> {
                authToken = intent.getStringExtra(EXTRA_AUTH_TOKEN)
                startGpsForState(currentState)
                startSyncLoop()
            }

            ACTION_STOP -> {
                forceStopLifecycle()
                stopSelf()
            }

            else -> {
                startGpsForState(currentState)
                startSyncLoop()
            }
        }
        TrackingDebugState.unsyncedQueueCount = localDb.countUnsyncedPoints()
        return START_STICKY
    }

    override fun onTaskRemoved(rootIntent: Intent?) {
        val restartIntent = Intent(applicationContext, TrackingService::class.java).apply {
            action = ACTION_START
            putExtra(EXTRA_AUTH_TOKEN, authToken)
        }
        startForegroundService(restartIntent)
        super.onTaskRemoved(rootIntent)
    }

    override fun onDestroy() {
        try {
            fusedLocationClient.removeLocationUpdates(locationCallback)
        } catch (_: Exception) {
        }
        syncHandler.removeCallbacksAndMessages(null)
        super.onDestroy()
    }

    override fun onBind(intent: Intent?): IBinder? = null

    private fun initLocationCallback() {
        locationCallback = object : LocationCallback() {
            override fun onLocationResult(result: LocationResult) {
                result.lastLocation?.let { location ->
                    handleLocation(location)
                }
            }
        }
    }

    private fun handleLocation(location: Location) {
        val speedKmh = motionDetector.getSpeedKmh(location)
        val previousState = currentState
        currentState = stateManager.update(speedKmh, Instant.now())

        if (previousState != currentState) {
            TrackingDebugState.currentTrackingState = currentState.name
            onStateChanged(previousState, currentState)
            startGpsForState(currentState)
        }

        val tripId = activeTripId
        if (tripId != null) {
            localDb.insertPoint(
                GpsPointEntity(
                    tripId = tripId,
                    timestamp = Instant.now().toString(),
                    latitude = location.latitude,
                    longitude = location.longitude,
                    speedKmh = speedKmh
                )
            )
            TrackingDebugState.gpsPointsRecorded += 1
            TrackingDebugState.unsyncedQueueCount = localDb.countUnsyncedPoints()
        }

        refreshNotification(speedKmh)
    }

    private fun onStateChanged(from: TripTrackingState, to: TripTrackingState) {
        val token = authToken ?: return
        thread {
            try {
                if (to == TripTrackingState.DRIVING && activeTripId == null) {
                    activeTripId = apiClient.startTrip(token, autoStarted = true)
                }

                if (from == TripTrackingState.PAUSED && to == TripTrackingState.DRIVING) {
                    val tripId = activeTripId
                    val pause = stateManager.completePause(Instant.now())
                    if (tripId != null && pause != null) {
                        apiClient.postBreak(
                            token,
                            BreakRecord(
                                tripId = tripId,
                                startTime = pause.first.toString(),
                                endTime = Instant.now().toString(),
                                durationMinutes = pause.second
                            )
                        )
                    }
                }

                if (from == TripTrackingState.DRIVING && to == TripTrackingState.IDLE) {
                    activeTripId?.let { tripId ->
                        syncQueuedPoints(tripIdOverride = tripId)
                        apiClient.endTrip(token, tripId, autoEnded = true)
                        localDb.deletePointsByTrip(tripId)
                        activeTripId = null
                    }
                }
            } catch (_: Exception) {
                // Keep service alive on lifecycle network errors.
            }
            TrackingDebugState.unsyncedQueueCount = localDb.countUnsyncedPoints()
        }
    }

    private fun startGpsForState(state: TripTrackingState) {
        val intervalMs = gpsController.getIntervalMillis(state)
        val request = LocationRequest.Builder(Priority.PRIORITY_HIGH_ACCURACY, intervalMs)
            .setMinUpdateIntervalMillis(intervalMs)
            .build()

        try {
            fusedLocationClient.removeLocationUpdates(locationCallback)
            fusedLocationClient.requestLocationUpdates(request, locationCallback, mainLooper)
        } catch (_: SecurityException) {
            // Keep foreground service running; permission can be re-granted by user.
        }
    }

    private fun startSyncLoop() {
        syncHandler.removeCallbacks(syncRunnable)
        syncHandler.post(syncRunnable)
    }

    private fun syncQueuedPoints(tripIdOverride: Int? = null) {
        val token = authToken ?: return
        val tripId = tripIdOverride ?: activeTripId ?: return

        thread {
            val pendingPoints = localDb.getQueuedPointsByTrip(tripId)
            if (pendingPoints.isEmpty()) {
                TrackingDebugState.lastSyncStatus = "no_pending"
                TrackingDebugState.unsyncedQueueCount = localDb.countUnsyncedPoints()
                return@thread
            }

            pendingPoints.forEach { point ->
                try {
                    apiClient.sendGpsPoint(token, tripId, point)
                    localDb.markPointsSynced(listOf(point.id))
                    TrackingDebugState.lastSyncStatus = "sync_ok"
                } catch (ex: Exception) {
                    localDb.incrementRetry(point.id, ex.message ?: "sync_error")
                    TrackingDebugState.lastSyncStatus = "sync_error"
                }
            }
            TrackingDebugState.unsyncedQueueCount = localDb.countUnsyncedPoints()
        }
    }

    private fun forceStopLifecycle() {
        val token = authToken
        val tripId = activeTripId
        if (token != null && tripId != null) {
            thread {
                try {
                    syncQueuedPoints(tripIdOverride = tripId)
                    apiClient.endTrip(token, tripId, autoEnded = false)
                } catch (_: Exception) {
                } finally {
                    localDb.deletePointsByTrip(tripId)
                    TrackingDebugState.unsyncedQueueCount = localDb.countUnsyncedPoints()
                }
            }
        }

        activeTripId = null
        stateManager.reset()
        currentState = TripTrackingState.IDLE
        TrackingDebugState.currentTrackingState = currentState.name
        syncHandler.removeCallbacksAndMessages(null)
    }

    private fun refreshNotification(speedKmh: Double) {
        val manager = getSystemService(NotificationManager::class.java)
        manager.notify(
            NOTIFICATION_ID,
            buildNotification(TrackingStatus(currentState, speedKmh, activeTripId))
        )
    }

    private fun buildNotification(status: TrackingStatus): Notification {
        val tripPart = status.activeTripId?.let { "Trip #$it" } ?: "No active trip"
        val text = "State: ${status.state.name} | Speed: ${"%.1f".format(status.speedKmh)} km/h | $tripPart"

        return NotificationCompat.Builder(this, CHANNEL_ID)
            .setContentTitle("TruckLog Background Tracking")
            .setContentText(text)
            .setSmallIcon(android.R.drawable.ic_menu_mylocation)
            .setOngoing(true)
            .build()
    }

    private fun createNotificationChannel() {
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            val channel = NotificationChannel(CHANNEL_ID, "TruckLog Tracking", NotificationManager.IMPORTANCE_LOW)
            channel.setShowBadge(false)
            getSystemService(NotificationManager::class.java).createNotificationChannel(channel)
        }
    }

    companion object {
        const val ACTION_START = "com.trucklog.action.START"
        const val ACTION_STOP = "com.trucklog.action.STOP"
        const val EXTRA_AUTH_TOKEN = "extra_auth_token"
        private const val CHANNEL_ID = "trucklog_tracking"
        private const val NOTIFICATION_ID = 101
    }
}
