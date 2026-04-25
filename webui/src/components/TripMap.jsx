import React from 'react';
import { MapContainer, Polyline, TileLayer } from 'react-leaflet';

export default function TripMap({ gpsPoints }) {
  if (!gpsPoints.length) {
    return <p>No GPS points available.</p>;
  }

  const positions = gpsPoints.map((p) => [p.latitude, p.longitude]);

  return (
    <MapContainer center={positions[0]} zoom={13} style={{ height: '400px', width: '100%' }}>
      <TileLayer url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png" />
      <Polyline positions={positions} />
    </MapContainer>
  );
}
