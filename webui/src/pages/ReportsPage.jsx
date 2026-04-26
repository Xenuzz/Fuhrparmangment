import React, { useState } from 'react';
import { apiRequest } from '../services/apiClient';

export default function ReportsPage() {
  const [date, setDate] = useState('');
  const [weekStart, setWeekStart] = useState('');
  const [driverId, setDriverId] = useState('');
  const [vehicleId, setVehicleId] = useState('');
  const [daily, setDaily] = useState(null);
  const [weekly, setWeekly] = useState(null);
  const [error, setError] = useState('');

  const buildQuery = (base) => {
    const params = new URLSearchParams();
    if (driverId) params.append('driver_id', driverId);
    if (vehicleId) params.append('vehicle_id', vehicleId);
    Object.entries(base).forEach(([k, v]) => {
      if (v) params.append(k, v);
    });
    return params.toString();
  };

  const loadDaily = async () => {
    try {
      setError('');
      const data = await apiRequest(`/reports/daily?${buildQuery({ date })}`);
      setDaily(data);
    } catch (err) {
      setError(err.message);
    }
  };

  const loadWeekly = async () => {
    try {
      setError('');
      const data = await apiRequest(`/reports/weekly?${buildQuery({ week_start: weekStart })}`);
      setWeekly(data);
    } catch (err) {
      setError(err.message);
    }
  };

  const downloadWeeklyPdf = async () => {
    const blob = await apiRequest(`/reports/weekly/timesheet.pdf?${buildQuery({ week_start: weekStart })}`, 'GET', null, true, 'blob');
    const url = URL.createObjectURL(blob);
    window.open(url, '_blank');
  };

  const renderRows = (rows) => (
    <table border="1" cellPadding="6" style={{ borderCollapse: 'collapse', width: '100%' }}>
      <thead>
        <tr>
          <th>Date</th><th>Driver</th><th>Vehicle</th><th>Job</th><th>Distance km</th><th>Driving min</th><th>Break min</th><th>Work min</th><th>Violations</th><th>Trips</th>
        </tr>
      </thead>
      <tbody>
        {rows.map((r, idx) => <tr key={idx}><td>{r.date}</td><td>{r.driver_id}</td><td>{r.vehicle}</td><td>{r.job_name}</td><td>{r.total_distance_km}</td><td>{r.total_driving_time_minutes}</td><td>{r.total_break_time_minutes}</td><td>{r.total_work_time_minutes}</td><td>{r.total_violations}</td><td>{r.total_trips}</td></tr>)}
      </tbody>
    </table>
  );

  return (
    <div>
      <h2>Reports</h2>
      {error && <p>{error}</p>}
      <div style={{ display: 'grid', gap: 8, maxWidth: 420 }}>
        <input type="date" value={date} onChange={(e) => setDate(e.target.value)} />
        <input type="date" value={weekStart} onChange={(e) => setWeekStart(e.target.value)} />
        <input placeholder="Driver ID (optional)" value={driverId} onChange={(e) => setDriverId(e.target.value)} />
        <input placeholder="Vehicle (optional)" value={vehicleId} onChange={(e) => setVehicleId(e.target.value)} />
        <button onClick={loadDaily}>Load Daily Summary</button>
        <button onClick={loadWeekly}>Load Weekly Summary</button>
        <button onClick={downloadWeeklyPdf} disabled={!weekStart}>Download Weekly PDF</button>
      </div>

      {daily && <div><h3>Daily Summary</h3>{renderRows(daily.rows)}</div>}
      {weekly && <div><h3>Weekly Summary</h3>{renderRows(weekly.rows)}</div>}
    </div>
  );
}
