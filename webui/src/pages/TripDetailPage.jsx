import React, { useEffect, useState } from 'react';
import { useParams } from 'react-router-dom';
import TripMap from '../components/TripMap';
import { apiRequest } from '../services/apiClient';

export default function TripDetailPage() {
  const { tripId } = useParams();
  const [trip, setTrip] = useState(null);
  const [analysis, setAnalysis] = useState(null);
  const [violations, setViolations] = useState([]);
  const [error, setError] = useState('');

  useEffect(() => {
    Promise.all([
      apiRequest(`/trips/${tripId}`),
      apiRequest(`/trips/${tripId}/analysis`),
      apiRequest(`/trips/${tripId}/violations`),
    ])
      .then(([tripData, analysisData, violationData]) => {
        setTrip(tripData);
        setAnalysis(analysisData);
        setViolations(violationData);
      })
      .catch((err) => setError(err.message));
  }, [tripId]);

  if (error) {
    return <p>{error}</p>;
  }

  if (!trip || !analysis) {
    return <p>Loading...</p>;
  }

  return (
    <div>
      <h2>Trip #{trip.id}</h2>
      <p>Start: {trip.start_time}</p>
      <p>End: {trip.end_time || 'active'}</p>
      <p>Distance: {analysis.distance_km ?? '-'} km</p>
      <p>Driving time: {analysis.driving_time_minutes ?? '-'} minutes</p>
      <p>Break time: {analysis.break_time_minutes ?? '-'} minutes</p>
      <p>Total time: {analysis.total_time_minutes ?? '-'} minutes</p>
      <p>Average speed: {analysis.average_speed_kmh ?? '-'} km/h</p>
      <p>Max speed: {analysis.max_speed_kmh ?? '-'} km/h</p>
      <p>Speed violations: {violations.length}</p>
      <TripMap gpsPoints={trip.gps_points || []} violations={violations} />
    </div>
  );
}
