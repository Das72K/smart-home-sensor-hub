import { useState, useEffect } from 'react';

const API_BASE = 'http://localhost:8000/api';
const WS_URL = 'ws://localhost:8000/ws/live';

export function useSensorData() {
  const [sensors, setSensors] = useState({});
  const [latestReadings, setLatestReadings] = useState([]);
  const [historyData, setHistoryData] = useState({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [wsConnected, setWsConnected] = useState(false);

  useEffect(() => {
    fetchLatestReadings();
    fetchSensors();
    fetchHistory();
  }, []);

  const fetchSensors = async () => {
    try {
      const res = await fetch(`${API_BASE}/sensors`);
      const data = await res.json();
      const sensorMap = {};
      data.forEach(sensor => {
        sensorMap[sensor.id] = sensor;
      });
      setSensors(sensorMap);
    } catch (err) {
      console.error('Failed to fetch sensors:', err);
      setError('Failed to load sensors');
    }
  };

  const fetchLatestReadings = async () => {
    try {
      setLoading(true);
      const res = await fetch(`${API_BASE}/sensors/latest`);
      const data = await res.json();
      setLatestReadings(data);
      setError(null);
    } catch (err) {
      console.error('Failed to fetch latest readings:', err);
      setError('Failed to load sensor data');
    } finally {
      setLoading(false);
    }
  };

  const fetchHistory = async () => {
    try {
      const res = await fetch(`${API_BASE}/sensors`);
      const sensors = await res.json();
      
      const history = {};
      for (const sensor of sensors) {
        try {
          const histRes = await fetch(`${API_BASE}/sensors/${sensor.id}/history?hours=24`);
          const histData = await histRes.json();
          history[sensor.id] = histData;
        } catch (err) {
          console.error(`Failed to fetch history for sensor ${sensor.id}:`, err);
        }
      }
      setHistoryData(history);
    } catch (err) {
      console.error('Failed to fetch history:', err);
    }
  };

  useEffect(() => {
    let ws;
    let reconnectTimeout;

    const connectWebSocket = () => {
      try {
        ws = new WebSocket(WS_URL);

        ws.onopen = () => {
          console.log('WebSocket connected');
          setWsConnected(true);
          setError(null);
        };

        ws.onmessage = (event) => {
          try {
            const message = JSON.parse(event.data);
            
            if (message.type === 'reading_update') {
              setLatestReadings(prev => {
                const updated = [...prev];
                const idx = updated.findIndex(r => r.sensor_id === message.sensor_id);
                if (idx >= 0) {
                  updated[idx] = {
                    ...updated[idx],
                    data: message.data,
                    timestamp: message.timestamp,
                  };
                } else {
                  updated.push({
                    sensor_id: message.sensor_id,
                    data: message.data,
                    timestamp: message.timestamp,
                  });
                }
                return updated;
              });

              setHistoryData(prev => ({
                ...prev,
                [message.sensor_id]: [
                  ...(prev[message.sensor_id] || []),
                  {
                    data: message.data,
                    timestamp: message.timestamp,
                  },
                ],
              }));
            }
          } catch (err) {
            console.error('Failed to parse WebSocket message:', err);
          }
        };

        ws.onerror = (error) => {
          console.error('WebSocket error:', error);
          setWsConnected(false);
          setError('WebSocket connection error');
        };

        ws.onclose = () => {
          console.log('WebSocket disconnected');
          setWsConnected(false);
          reconnectTimeout = setTimeout(connectWebSocket, 3000);
        };
      } catch (err) {
        console.error('Failed to connect WebSocket:', err);
        setError('Failed to connect to real-time updates');
      }
    };

    connectWebSocket();

    return () => {
      if (ws) ws.close();
      if (reconnectTimeout) clearTimeout(reconnectTimeout);
    };
  }, []);

  return {
    sensors,
    latestReadings,
    historyData,
    loading,
    error,
    wsConnected,
    refetch: () => {
      fetchLatestReadings();
      fetchHistory();
    },
  };
}