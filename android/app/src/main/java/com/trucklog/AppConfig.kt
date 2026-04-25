package com.trucklog

import org.json.JSONObject
import java.io.File

/**
 * Reads shared system configuration from the mounted JSON file path.
 */
object AppConfig {
    private const val CONFIG_PATH = "/sdcard/Download/system_config.json"

    private fun readRoot(): JSONObject {
        val configContent = File(CONFIG_PATH).readText()
        return JSONObject(configContent)
    }

    fun getApiBaseUrl(): String = readRoot().getJSONObject("webui").getString("api_base_url")

    fun getGpsIntervalSeconds(): Long = readRoot().getJSONObject("gps").getLong("send_interval_seconds")

    fun getSyncIntervalMinSeconds(): Long = readRoot().getJSONObject("gps").optLong("sync_interval_min_seconds", 30L)

    fun getSyncIntervalMaxSeconds(): Long = readRoot().getJSONObject("gps").optLong("sync_interval_max_seconds", 60L)
}
