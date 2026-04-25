package com.trucklog

import org.json.JSONObject
import java.io.File

/**
 * Reads shared system configuration from the mounted JSON file path.
 */
object AppConfig {
    private const val CONFIG_PATH = "/sdcard/Download/system_config.json"

    fun getApiBaseUrl(): String {
        val configContent = File(CONFIG_PATH).readText()
        val root = JSONObject(configContent)
        return root.getJSONObject("webui").getString("api_base_url")
    }

    fun getGpsIntervalSeconds(): Long {
        val configContent = File(CONFIG_PATH).readText()
        val root = JSONObject(configContent)
        return root.getJSONObject("gps").getLong("send_interval_seconds")
    }
}
