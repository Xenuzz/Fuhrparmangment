package com.trucklog

import okhttp3.MediaType.Companion.toMediaType
import okhttp3.OkHttpClient
import okhttp3.Request
import okhttp3.RequestBody.Companion.toRequestBody
import org.json.JSONArray
import org.json.JSONObject

/**
 * Thin HTTP client for backend authentication and trip API operations.
 */
class ApiClient {
    private val httpClient = OkHttpClient()
    private val jsonType = "application/json; charset=utf-8".toMediaType()

    fun login(username: String, password: String): String {
        val payload = JSONObject()
            .put("username", username)
            .put("password", password)

        val request = Request.Builder()
            .url("${AppConfig.getApiBaseUrl()}/auth/login")
            .post(payload.toString().toRequestBody(jsonType))
            .build()

        httpClient.newCall(request).execute().use { response ->
            if (!response.isSuccessful) error("Login failed: ${response.code}")
            val json = JSONObject(response.body?.string().orEmpty())
            return json.getString("access_token")
        }
    }

    fun startTrip(token: String): Int {
        val request = Request.Builder()
            .url("${AppConfig.getApiBaseUrl()}/trips/start")
            .addHeader("Authorization", "Bearer $token")
            .post("{}".toRequestBody(jsonType))
            .build()

        httpClient.newCall(request).execute().use { response ->
            if (!response.isSuccessful) error("Start trip failed: ${response.code}")
            val json = JSONObject(response.body?.string().orEmpty())
            return json.getInt("id")
        }
    }

    fun sendGpsPoint(token: String, tripId: Int, point: GpsPointEntity) {
        val payload = JSONObject()
            .put("timestamp", point.timestamp)
            .put("latitude", point.latitude)
            .put("longitude", point.longitude)
            .put("speed_kmh", point.speedKmh)

        val request = Request.Builder()
            .url("${AppConfig.getApiBaseUrl()}/trips/$tripId/gps")
            .addHeader("Authorization", "Bearer $token")
            .post(payload.toString().toRequestBody(jsonType))
            .build()

        httpClient.newCall(request).execute().use { response ->
            if (!response.isSuccessful) error("Send GPS failed: ${response.code}")
        }
    }

    fun endTrip(token: String, tripId: Int) {
        val request = Request.Builder()
            .url("${AppConfig.getApiBaseUrl()}/trips/$tripId/end")
            .addHeader("Authorization", "Bearer $token")
            .post("{}".toRequestBody(jsonType))
            .build()

        httpClient.newCall(request).execute().use { response ->
            if (!response.isSuccessful) error("End trip failed: ${response.code}")
        }
    }

    fun syncAllPoints(token: String, tripId: Int, points: List<GpsPointEntity>) {
        val payloadArray = JSONArray()
        points.forEach { point ->
            payloadArray.put(
                JSONObject()
                    .put("timestamp", point.timestamp)
                    .put("latitude", point.latitude)
                    .put("longitude", point.longitude)
                    .put("speed_kmh", point.speedKmh)
            )
        }

        points.forEach { sendGpsPoint(token, tripId, it) }
    }
}
