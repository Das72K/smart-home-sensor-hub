# Smart Home Dashboard

React front-end for the Smart Home Sensor Hub: live gauges for temperature, humidity and motion,
and 24-hour history charts (Recharts). Live updates arrive over WebSocket (`ws://localhost:8000/ws/live`);
initial state and history come from the REST API (`http://localhost:8000/api`).

```bash
npm install
npm start        # http://localhost:3000 — the backend must be running on :8000
npm run build    # production build in build/
```

| File | Role |
|---|---|
| `src/hooks/useSensorData.js` | REST fetch on load + WebSocket subscription, merges live readings into state |
| `src/components/SensorGauge.jsx` | current value per sensor (temperature / humidity / motion) |
| `src/components/HistoryChart.jsx` | 24-hour line charts |
| `src/App.jsx` | layout, connection status indicator |

See the [main README](../README.md) for the full system.
