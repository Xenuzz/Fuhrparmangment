import React from 'react';
import { Link, Navigate, Route, Routes } from 'react-router-dom';
import LoginPage from './pages/LoginPage';
import ReportsPage from './pages/ReportsPage';
import TripDetailPage from './pages/TripDetailPage';
import TripsPage from './pages/TripsPage';

export default function App() {
  const token = localStorage.getItem('trucklog_token');

  return (
    <div style={{ padding: '16px', fontFamily: 'Arial, sans-serif' }}>
      <h1>TruckLog</h1>
      <nav style={{ display: 'flex', gap: '12px', marginBottom: '16px' }}>
        <Link to="/login">Login</Link>
        <Link to="/trips">Trips</Link>
        <Link to="/reports">Reports</Link>
      </nav>
      <Routes>
        <Route path="/login" element={<LoginPage />} />
        <Route path="/trips" element={token ? <TripsPage /> : <Navigate to="/login" />} />
        <Route path="/trips/:tripId" element={token ? <TripDetailPage /> : <Navigate to="/login" />} />
        <Route path="/reports" element={token ? <ReportsPage /> : <Navigate to="/login" />} />
        <Route path="*" element={<Navigate to="/login" />} />
      </Routes>
    </div>
  );
}
