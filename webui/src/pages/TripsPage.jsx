import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { apiRequest } from '../services/apiClient';

export default function TripsPage() {
  const [trips, setTrips] = useState([]);
  const [error, setError] = useState('');

  useEffect(() => {
    apiRequest('/trips')
      .then((data) => setTrips(data))
      .catch((err) => setError(err.message));
  }, []);

  return (
    <div>
      <h2>Trips</h2>
      {error && <p>{error}</p>}
      <ul>
        {trips.map((trip) => (
          <li key={trip.id}>
            <Link to={`/trips/${trip.id}`}>
              Trip #{trip.id} | Start: {trip.start_time} | End: {trip.end_time || 'active'} | Distance:{' '}
              {trip.distance_km ?? '-'} km
            </Link>
          </li>
        ))}
      </ul>
    </div>
  );
}
