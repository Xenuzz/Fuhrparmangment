import React from 'react';
import { CircleMarker, MapContainer, Polyline, TileLayer, Tooltip } from 'react-leaflet';

/**
 * Build route segments to highlight violation ranges in red.
 * Segments are selected by violation time overlap against route points.
 */
function buildViolationSegments(gpsPoints, violations) {
  if (!gpsPoints.length || !violations.length) {
    return [];
  }

  const sortedPoints = [...gpsPoints].sort((a, b) => new Date(a.timestamp) - new Date(b.timestamp));
  return violations
    .map((violation) => {
      const startTime = new Date(violation.start_time).getTime();
      const endTime = new Date(violation.end_time).getTime();
      const segment = sortedPoints
        .filter((point) => {
          const pointTime = new Date(point.timestamp).getTime();
          return pointTime >= startTime && pointTime <= endTime;
        })
        .map((point) => [point.latitude, point.longitude]);
      return segment;
    })
    .filter((segment) => segment.length > 1);
}

function formatDurationMinutes(startTime, endTime) {
  const start = new Date(startTime).getTime();
  const end = new Date(endTime).getTime();
  const durationMinutes = Math.max(Math.round((end - start) / 60000), 0);
  return `${durationMinutes} min`;
}

export default function TripMap({ gpsPoints, violations }) {
  if (!gpsPoints.length) {
    return <p>No GPS points available.</p>;
  }

  const positions = gpsPoints.map((point) => [point.latitude, point.longitude]);
  const violationSegments = buildViolationSegments(gpsPoints, violations);

  return (
    <MapContainer center={positions[0]} zoom={13} style={{ height: '400px', width: '100%' }}>
      <TileLayer url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png" />

      <Polyline positions={positions} pathOptions={{ color: 'green', weight: 4 }} />

      {violationSegments.map((segment, index) => (
        <Polyline key={`segment-${index + 1}`} positions={segment} pathOptions={{ color: 'red', weight: 6 }} />
      ))}

      {violations.map((violation) => (
        <CircleMarker
          key={`violation-${violation.id}`}
          center={[violation.latitude, violation.longitude]}
          radius={8}
          pathOptions={{ color: 'red', fillColor: 'red', fillOpacity: 0.85 }}
        >
          <Tooltip direction="top" offset={[0, -8]} opacity={1}>
            <div>
              <div>Measured: {violation.measured_speed_kmh} km/h</div>
              <div>Allowed: {violation.allowed_speed_kmh} km/h</div>
              <div>Duration: {formatDurationMinutes(violation.start_time, violation.end_time)}</div>
            </div>
          </Tooltip>
        </CircleMarker>
      ))}
    </MapContainer>
  );
}
