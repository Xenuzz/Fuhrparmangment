package com.trucklog

import android.Manifest
import android.content.Intent
import android.content.pm.PackageManager
import android.os.Bundle
import android.widget.Button
import android.widget.EditText
import android.widget.TextView
import androidx.appcompat.app.AppCompatActivity
import androidx.core.app.ActivityCompat
import androidx.core.content.ContextCompat
import kotlin.concurrent.thread

/**
 * MVP activity that supports login, trip start/stop, local storage, and backend synchronization.
 */
class MainActivity : AppCompatActivity() {
    private val apiClient = ApiClient()
    private lateinit var localDb: LocalGpsDatabase

    private var token: String? = null
    private var currentTripId: Int? = null

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_main)

        localDb = LocalGpsDatabase(this)
        requestLocationPermissions()

        val usernameInput = findViewById<EditText>(R.id.usernameInput)
        val passwordInput = findViewById<EditText>(R.id.passwordInput)
        val statusText = findViewById<TextView>(R.id.statusText)
        val loginButton = findViewById<Button>(R.id.loginButton)
        val startTripButton = findViewById<Button>(R.id.startTripButton)
        val stopTripButton = findViewById<Button>(R.id.stopTripButton)

        loginButton.setOnClickListener {
            thread {
                try {
                    val jwt = apiClient.login(usernameInput.text.toString(), passwordInput.text.toString())
                    token = jwt
                    runOnUiThread { statusText.text = "Login successful" }
                } catch (ex: Exception) {
                    runOnUiThread { statusText.text = "Login failed: ${ex.message}" }
                }
            }
        }

        startTripButton.setOnClickListener {
            val authToken = token ?: return@setOnClickListener
            thread {
                try {
                    val tripId = apiClient.startTrip(authToken)
                    currentTripId = tripId
                    val intent = Intent(this, TrackingService::class.java).putExtra(TrackingService.EXTRA_TRIP_ID, tripId)
                    startForegroundService(intent)
                    runOnUiThread { statusText.text = "Trip started: $tripId" }
                } catch (ex: Exception) {
                    runOnUiThread { statusText.text = "Start trip failed: ${ex.message}" }
                }
            }
        }

        stopTripButton.setOnClickListener {
            val authToken = token ?: return@setOnClickListener
            val tripId = currentTripId ?: return@setOnClickListener
            stopService(Intent(this, TrackingService::class.java))

            thread {
                try {
                    val points = localDb.getPointsByTrip(tripId)
                    apiClient.syncAllPoints(authToken, tripId, points)
                    apiClient.endTrip(authToken, tripId)
                    localDb.deletePointsByTrip(tripId)
                    currentTripId = null
                    runOnUiThread { statusText.text = "Trip stopped and synced" }
                } catch (ex: Exception) {
                    runOnUiThread { statusText.text = "Stop trip failed: ${ex.message}" }
                }
            }
        }
    }

    private fun requestLocationPermissions() {
        val permissions = arrayOf(
            Manifest.permission.ACCESS_FINE_LOCATION,
            Manifest.permission.ACCESS_COARSE_LOCATION,
            Manifest.permission.POST_NOTIFICATIONS
        )

        val missing = permissions.filter {
            ContextCompat.checkSelfPermission(this, it) != PackageManager.PERMISSION_GRANTED
        }

        if (missing.isNotEmpty()) {
            ActivityCompat.requestPermissions(this, missing.toTypedArray(), 100)
        }
    }
}
