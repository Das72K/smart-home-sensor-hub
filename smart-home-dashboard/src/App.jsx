import React from 'react';
import { SensorGauge } from './components/SensorGauge';
import { HistoryChart } from './components/HistoryChart';
import { useSensorData } from './hooks/useSensorData';
import './App.css';

function App() {
  const { sensors, latestReadings, historyData, loading, error, wsConnected, refetch } = useSensorData();

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100">
      <header className="bg-white shadow-sm border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <div className="flex justify-between items-center">
            <div>
              <h1 className="text-3xl font-bold text-gray-900">Smart Home Sensor Hub</h1>
              <p className="text-gray-600 text-sm mt-1">Real-time environmental monitoring</p>
            </div>
            
            <div className="flex items-center gap-4">
              <div className="flex items-center gap-2">
                <div className={`w-3 h-3 rounded-full ${wsConnected ? 'bg-green-500' : 'bg-red-500'}`}></div>
                <span className="text-sm text-gray-600">
                  {wsConnected ? 'Live' : 'Offline'}
                </span>
              </div>
              
              <button
                onClick={refetch}
                className="px-4 py-2 bg-blue-600 text-white rounded-lg text-sm font-medium hover:bg-blue-700 transition-colors"
              >
                Refresh
              </button>
            </div>
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {error && (
          <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-lg">
            <p className="text-red-700 text-sm">{error}</p>
          </div>
        )}

        {loading && latestReadings.length === 0 ? (
          <div className="flex justify-center items-center py-12">
            <div className="text-center">
              <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
              <p className="text-gray-600">Loading sensor data...</p>
            </div>
          </div>
        ) : latestReadings.length === 0 ? (
          <div className="text-center py-12">
            <p className="text-gray-600">No sensors registered or no data available</p>
          </div>
        ) : (
          <>
            <section className="mb-8">
              <h2 className="text-xl font-bold text-gray-900 mb-4">Current Status</h2>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {latestReadings.map((reading) => {
                  const sensor = sensors[reading.sensor_id];
                  return (
                    <SensorGauge
                      key={reading.sensor_id}
                      sensor={sensor}
                      reading={reading}
                    />
                  );
                })}
              </div>
            </section>

            <section>
              <h2 className="text-xl font-bold text-gray-900 mb-4">24-Hour History</h2>
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                {Object.entries(historyData).map(([sensorId, readings]) => {
                  const sensor = sensors[parseInt(sensorId)];
                  if (readings.length > 0 && readings[0].data.temperature !== undefined) {
                    return (
                      <HistoryChart
                        key={sensorId}
                        sensor={sensor}
                        readings={readings}
                      />
                    );
                  }
                  return null;
                })}
              </div>
            </section>
          </>
        )}
      </main>

      <footer className="bg-white border-t border-gray-200 mt-12">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6 text-center text-gray-600 text-sm">
          <p>Smart Home Sensor Hub Dashboard • Real-time updates via WebSocket</p>
        </div>
      </footer>
    </div>
  );
}

export default App;