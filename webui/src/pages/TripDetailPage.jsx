import React, { useEffect, useState } from 'react';
import { useParams } from 'react-router-dom';
import TripMap from '../components/TripMap';
import { apiRequest } from '../services/apiClient';

export default function TripDetailPage() {
  const { tripId } = useParams();
  const [trip, setTrip] = useState(null);
  const [error, setError] = useState('');

  useEffect(() => {
    apiRequest(`/trips/${tripId}`)
      .then((data) => setTrip(data))
      .catch((err) => setError(err.message));
  }, [tripId]);

  if (error) {
    return <p>{error}</p>;
  }

  if (!trip) {
    return <p>Loading...</p>;
  }

  return (
    <div>
      <h2>Trip #{trip.id}</h2>
      <p>Start: {trip.start_time}</p>
      <p>End: {trip.end_time || 'active'}</p>
      <p>Distance: {trip.distance_km ?? '-'} km</p>
      <TripMap gpsPoints={trip.gps_points || []} />
    </div>
  );
}
