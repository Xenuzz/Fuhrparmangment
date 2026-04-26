import React, { useEffect, useState } from 'react';
import { useParams } from 'react-router-dom';
import TripMap from '../components/TripMap';
import { apiRequest } from '../services/apiClient';

export default function TripDetailPage() {
  const { tripId } = useParams();
  const [trip, setTrip] = useState(null);
  const [analysis, setAnalysis] = useState(null);
  const [quality, setQuality] = useState(null);
  const [violations, setViolations] = useState([]);
  const [error, setError] = useState('');

  useEffect(() => {
    Promise.all([
      apiRequest(`/trips/${tripId}`),
      apiRequest(`/trips/${tripId}/analysis`),
      apiRequest(`/trips/${tripId}/quality`),
      apiRequest(`/trips/${tripId}/violations`),
    ])
      .then(([tripData, analysisData, qualityData, violationData]) => {
        setTrip(tripData);
        setAnalysis(analysisData);
        setQuality(qualityData);
        setViolations(violationData);
      })
      .catch((err) => setError(err.message));
  }, [tripId]);

  const downloadTripPdf = async () => {
    const blob = await apiRequest(`/trips/${tripId}/timesheet.pdf`, 'GET', null, true, 'blob');
    const url = URL.createObjectURL(blob);
    window.open(url, '_blank');
  };

  if (error) return <p>{error}</p>;
  if (!trip || !analysis || !quality) return <p>Loading...</p>;

  return (
    <div>
      <h2>Trip #{trip.id}</h2>
      <button onClick={downloadTripPdf}>Export Timesheet PDF</button>
      <p>Start: {trip.start_time}</p>
      <p>End: {trip.end_time || 'active'}</p>
      <p>Distance: {analysis.distance_km ?? '-'} km</p>
      <p>Driving time: {analysis.driving_time_minutes ?? '-'} minutes</p>
      <p>Break time: {analysis.break_time_minutes ?? '-'} minutes</p>
      <p>Total time: {analysis.total_time_minutes ?? '-'} minutes</p>
      <p>Average speed: {analysis.average_speed_kmh ?? '-'} km/h</p>
      <p>Max speed: {analysis.max_speed_kmh ?? '-'} km/h</p>
      <p>Speed violations: {violations.length}</p>

      <h3>Data Quality</h3>
      <p>GPS total: {quality.gps_points_total}</p>
      <p>GPS valid: {quality.gps_points_valid}</p>
      <p>GPS filtered: {quality.gps_points_filtered}</p>
      <p>Filter rate: {quality.filter_rate_percent}%</p>
      <p>Analysis quality: {quality.analysis_quality}</p>
      <p>Violations total: {quality.violations_total}</p>
      <p>Breaks total: {quality.breaks_total}</p>

      <h3>Violations</h3>
      <ul>
        {violations.map((v) => (
          <li key={v.id}>
            {v.severity.toUpperCase()} | overspeed {v.overspeed_kmh} km/h | duration {v.duration_seconds}s | measured {v.measured_speed_kmh} / allowed {v.allowed_speed_kmh}
          </li>
        ))}
      </ul>

      <TripMap gpsPoints={trip.gps_points || []} violations={violations} />
    </div>
  );
}
