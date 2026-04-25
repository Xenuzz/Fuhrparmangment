package com.trucklog

import android.content.ContentValues
import android.content.Context
import android.database.sqlite.SQLiteDatabase
import android.database.sqlite.SQLiteOpenHelper

/**
 * SQLite database for storing GPS queue and retry metadata before backend synchronization.
 */
class LocalGpsDatabase(context: Context) : SQLiteOpenHelper(context, DB_NAME, null, DB_VERSION) {
    override fun onCreate(db: SQLiteDatabase) {
        db.execSQL(
            """
            CREATE TABLE gps_points (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                trip_id INTEGER NOT NULL,
                timestamp TEXT NOT NULL,
                latitude REAL NOT NULL,
                longitude REAL NOT NULL,
                speed_kmh REAL NOT NULL,
                synced INTEGER NOT NULL DEFAULT 0,
                retry_count INTEGER NOT NULL DEFAULT 0,
                last_error TEXT
            )
            """.trimIndent()
        )
    }

    override fun onUpgrade(db: SQLiteDatabase, oldVersion: Int, newVersion: Int) {
        db.execSQL("DROP TABLE IF EXISTS gps_points")
        onCreate(db)
    }

    fun insertPoint(point: GpsPointEntity) {
        val values = ContentValues().apply {
            put("trip_id", point.tripId)
            put("timestamp", point.timestamp)
            put("latitude", point.latitude)
            put("longitude", point.longitude)
            put("speed_kmh", point.speedKmh)
            put("synced", if (point.synced) 1 else 0)
            put("retry_count", point.retryCount)
        }
        writableDatabase.insert("gps_points", null, values)
    }

    fun getQueuedPointsByTrip(tripId: Int, limit: Int = 250): List<GpsPointEntity> {
        val result = mutableListOf<GpsPointEntity>()
        val cursor = readableDatabase.query(
            "gps_points",
            arrayOf("id", "trip_id", "timestamp", "latitude", "longitude", "speed_kmh", "synced", "retry_count"),
            "trip_id = ? AND synced = 0",
            arrayOf(tripId.toString()),
            null,
            null,
            "id ASC",
            limit.toString()
        )

        cursor.use {
            while (it.moveToNext()) {
                result.add(
                    GpsPointEntity(
                        id = it.getLong(0),
                        tripId = it.getInt(1),
                        timestamp = it.getString(2),
                        latitude = it.getDouble(3),
                        longitude = it.getDouble(4),
                        speedKmh = it.getDouble(5),
                        synced = it.getInt(6) == 1,
                        retryCount = it.getInt(7)
                    )
                )
            }
        }
        return result
    }

    fun markPointsSynced(pointIds: List<Long>) {
        if (pointIds.isEmpty()) return
        val idsCsv = pointIds.joinToString(",")
        writableDatabase.execSQL("UPDATE gps_points SET synced = 1 WHERE id IN ($idsCsv)")
    }

    fun incrementRetry(pointId: Long, error: String) {
        val values = ContentValues().apply {
            put("last_error", error.take(255))
        }
        writableDatabase.update(
            "gps_points",
            values,
            "id = ?",
            arrayOf(pointId.toString())
        )
        writableDatabase.execSQL("UPDATE gps_points SET retry_count = retry_count + 1 WHERE id = $pointId")
    }

    fun deletePointsByTrip(tripId: Int) {
        writableDatabase.delete("gps_points", "trip_id = ?", arrayOf(tripId.toString()))
    }

    companion object {
        private const val DB_NAME = "trucklog.db"
        private const val DB_VERSION = 2
    }
}
