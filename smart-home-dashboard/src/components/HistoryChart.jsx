import React from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';

export function HistoryChart({ sensor, readings }) {
  if (!readings || readings.length === 0) {
    return (
      <div className="bg-white rounded-lg p-6 shadow-sm border border-gray-200">
        <h3 className="text-gray-500 font-semibold text-center">No history data</h3>
      </div>
    );
  }

  const chartData = readings.map(reading => {
    const timestamp = new Date(reading.timestamp);
    return {
      time: timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      timestamp: reading.timestamp,
      ...reading.data,
    };
  });

  const isTemperatureHumidity = readings[0].data.temperature !== undefined;

  return (
    <div className="bg-white rounded-lg p-6 shadow-sm border border-gray-200">
      <h3 className="text-gray-700 font-semibold mb-4">
        24-Hour History - {sensor?.location || 'Sensor'}
      </h3>

      {isTemperatureHumidity ? (
        <ResponsiveContainer width="100%" height={300}>
          <LineChart data={chartData}>
            <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
            <XAxis 
              dataKey="time" 
              stroke="#9ca3af"
              tick={{ fontSize: 12 }}
            />
            <YAxis stroke="#9ca3af" tick={{ fontSize: 12 }} />
            <Tooltip 
              contentStyle={{
                backgroundColor: '#fff',
                border: '1px solid #e5e7eb',
                borderRadius: '8px',
              }}
              labelStyle={{ color: '#1f2937' }}
            />
            <Legend />
            <Line
              type="monotone"
              dataKey="temperature"
              stroke="#f97316"
              dot={false}
              strokeWidth={2}
              name="Temperature (°C)"
            />
            <Line
              type="monotone"
              dataKey="humidity"
              stroke="#3b82f6"
              dot={false}
              strokeWidth={2}
              name="Humidity (%)"
            />
          </LineChart>
        </ResponsiveContainer>
      ) : (
        <div className="text-center text-gray-500 py-8">
          Motion sensor data not suitable for chart display
        </div>
      )}
    </div>
  );
}