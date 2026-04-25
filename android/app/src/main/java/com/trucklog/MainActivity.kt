package com.trucklog

import android.Manifest
import android.content.Intent
import android.content.pm.PackageManager
import android.os.Build
import android.os.Bundle
import android.widget.Button
import android.widget.EditText
import android.widget.TextView
import androidx.appcompat.app.AppCompatActivity
import androidx.core.app.ActivityCompat
import androidx.core.content.ContextCompat
import kotlin.concurrent.thread

/**
 * MVP activity that supports login and foreground tracking lifecycle controls.
 */
class MainActivity : AppCompatActivity() {
    private val apiClient = ApiClient()
    private var token: String? = null

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_main)

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
            val authToken = token ?: run {
                statusText.text = "Login first"
                return@setOnClickListener
            }

            val intent = Intent(this, TrackingService::class.java).apply {
                action = TrackingService.ACTION_START
                putExtra(TrackingService.EXTRA_AUTH_TOKEN, authToken)
            }
            startForegroundService(intent)
            statusText.text = "Background tracking started"
        }

        stopTripButton.setOnClickListener {
            val intent = Intent(this, TrackingService::class.java).apply {
                action = TrackingService.ACTION_STOP
            }
            startService(intent)
            statusText.text = "Background tracking stopped"
        }
    }

    private fun requestLocationPermissions() {
        val permissions = mutableListOf(
            Manifest.permission.ACCESS_FINE_LOCATION,
            Manifest.permission.ACCESS_COARSE_LOCATION,
            Manifest.permission.FOREGROUND_SERVICE,
            Manifest.permission.INTERNET
        )

        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.TIRAMISU) {
            permissions.add(Manifest.permission.POST_NOTIFICATIONS)
        }

        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.Q) {
            permissions.add(Manifest.permission.ACCESS_BACKGROUND_LOCATION)
        }

        val missing = permissions.filter {
            ContextCompat.checkSelfPermission(this, it) != PackageManager.PERMISSION_GRANTED
        }

        if (missing.isNotEmpty()) {
            ActivityCompat.requestPermissions(this, missing.toTypedArray(), 100)
        }
    }
}
