package com.trucklog

import android.content.ContentValues
import android.content.Context
import android.database.sqlite.SQLiteDatabase
import android.database.sqlite.SQLiteOpenHelper

/**
 * SQLite database for temporarily storing GPS points before backend synchronization.
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
                speed_kmh REAL NOT NULL
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
        }
        writableDatabase.insert("gps_points", null, values)
    }

    fun getPointsByTrip(tripId: Int): List<GpsPointEntity> {
        val result = mutableListOf<GpsPointEntity>()
        val cursor = readableDatabase.query(
            "gps_points",
            arrayOf("trip_id", "timestamp", "latitude", "longitude", "speed_kmh"),
            "trip_id = ?",
            arrayOf(tripId.toString()),
            null,
            null,
            "id ASC"
        )

        cursor.use {
            while (it.moveToNext()) {
                result.add(
                    GpsPointEntity(
                        tripId = it.getInt(0),
                        timestamp = it.getString(1),
                        latitude = it.getDouble(2),
                        longitude = it.getDouble(3),
                        speedKmh = it.getDouble(4)
                    )
                )
            }
        }
        return result
    }

    fun deletePointsByTrip(tripId: Int) {
        writableDatabase.delete("gps_points", "trip_id = ?", arrayOf(tripId.toString()))
    }

    companion object {
        private const val DB_NAME = "trucklog.db"
        private const val DB_VERSION = 1
    }
}
