import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { apiRequest } from '../services/apiClient';

export default function LoginPage() {
  const navigate = useNavigate();
  const [username, setUsername] = useState('driver');
  const [password, setPassword] = useState('driver123');
  const [error, setError] = useState('');

  const onSubmit = async (event) => {
    event.preventDefault();
    setError('');

    try {
      const data = await apiRequest('/auth/login', 'POST', { username, password }, false);
      localStorage.setItem('trucklog_token', data.access_token);
      navigate('/trips');
    } catch (err) {
      setError(`Login failed: ${err.message}`);
    }
  };

  return (
    <form onSubmit={onSubmit}>
      <h2>Login</h2>
      <div>
        <label>Username</label>
        <input value={username} onChange={(e) => setUsername(e.target.value)} />
      </div>
      <div>
        <label>Password</label>
        <input type="password" value={password} onChange={(e) => setPassword(e.target.value)} />
      </div>
      <button type="submit">Login</button>
      {error && <p>{error}</p>}
    </form>
  );
}
