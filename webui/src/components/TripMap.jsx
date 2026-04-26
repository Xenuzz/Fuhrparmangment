import React from 'react';
import { CircleMarker, MapContainer, Polyline, TileLayer, Tooltip } from 'react-leaflet';

function buildViolationSegments(gpsPoints, violations) {
  if (!gpsPoints.length || !violations.length) return [];
  const sortedPoints = [...gpsPoints].sort((a, b) => new Date(a.timestamp) - new Date(b.timestamp));
  return violations
    .map((violation) => {
      const startTime = new Date(violation.start_time).getTime();
      const endTime = new Date(violation.end_time).getTime();
      return sortedPoints
        .filter((point) => {
          const pointTime = new Date(point.timestamp).getTime();
          return pointTime >= startTime && pointTime <= endTime;
        })
        .map((point) => [point.latitude, point.longitude]);
    })
    .filter((segment) => segment.length > 1);
}

export default function TripMap({ gpsPoints, violations }) {
  if (!gpsPoints.length) return <p>No GPS points available.</p>;

  const positions = gpsPoints.map((point) => [point.latitude, point.longitude]);
  const violationSegments = buildViolationSegments(gpsPoints, violations);

  return (
    <MapContainer center={positions[0]} zoom={13} style={{ height: '400px', width: '100%' }}>
      <TileLayer url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png" />
      <Polyline positions={positions} pathOptions={{ color: 'green', weight: 4 }} />
      {violationSegments.map((segment, index) => <Polyline key={`segment-${index}`} positions={segment} pathOptions={{ color: 'red', weight: 6 }} />)}
      {violations.map((violation) => (
        <CircleMarker key={`violation-${violation.id}`} center={[violation.latitude, violation.longitude]} radius={8} pathOptions={{ color: 'red', fillColor: 'red', fillOpacity: 0.85 }}>
          <Tooltip direction="top" offset={[0, -8]} opacity={1}>
            <div>
              <div>Severity: {violation.severity}</div>
              <div>Overspeed: {violation.overspeed_kmh} km/h</div>
              <div>Duration: {violation.duration_seconds} sec</div>
              <div>Measured: {violation.measured_speed_kmh} km/h</div>
              <div>Allowed: {violation.allowed_speed_kmh} km/h</div>
            </div>
          </Tooltip>
        </CircleMarker>
      ))}
    </MapContainer>
  );
}
