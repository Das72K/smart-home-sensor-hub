import React from 'react';

export function SensorGauge({ sensor, reading }) {
  if (!reading || !reading.data) {
    return (
      <div className="bg-white rounded-lg p-6 shadow-sm border border-gray-200">
        <h3 className="text-gray-500 font-semibold text-center">No data</h3>
      </div>
    );
  }

  const data = reading.data;
  const isTemperatureHumidity = data.temperature !== undefined;

  if (isTemperatureHumidity) {
    const temp = data.temperature;
    const humidity = data.humidity;

    return (
      <div className="bg-white rounded-lg p-6 shadow-sm border border-gray-200">
        <h3 className="text-gray-700 font-semibold mb-4">{sensor?.location || 'Sensor'}</h3>
        
        <div className="grid grid-cols-2 gap-4">
          <div className="flex flex-col items-center">
            <div className="relative w-24 h-24 rounded-full bg-gradient-to-br from-red-100 to-orange-100 flex items-center justify-center mb-2">
              <div className="text-center">
                <div className="text-2xl font-bold text-orange-600">{temp}°</div>
                <div className="text-xs text-gray-500">C</div>
              </div>
            </div>
            <div className="text-sm text-gray-600">Temperature</div>
          </div>

          <div className="flex flex-col items-center">
            <div className="relative w-24 h-24 rounded-full bg-gradient-to-br from-blue-100 to-cyan-100 flex items-center justify-center mb-2">
              <div className="text-center">
                <div className="text-2xl font-bold text-blue-600">{humidity}%</div>
              </div>
            </div>
            <div className="text-sm text-gray-600">Humidity</div>
          </div>
        </div>

        <div className="mt-4 text-xs text-gray-400 text-center">
          {new Date(reading.timestamp).toLocaleTimeString()}
        </div>
      </div>
    );
  }

  const motion = data.motion;
  const motionColor = motion ? 'bg-red-100 border-red-300' : 'bg-green-100 border-green-300';
  const motionText = motion ? 'Motion Detected' : 'No Motion';
  const motionBg = motion ? 'bg-red-500' : 'bg-green-500';

  return (
    <div className={`rounded-lg p-6 shadow-sm border-2 ${motionColor}`}>
      <h3 className="text-gray-700 font-semibold mb-4">{sensor?.location || 'Motion Sensor'}</h3>
      
      <div className="flex items-center gap-4">
        <div className={`w-16 h-16 rounded-full ${motionBg} flex items-center justify-center`}>
          <span className="text-white text-2xl">{motion ? '🚨' : '✓'}</span>
        </div>
        <div>
          <div className={`text-xl font-bold ${motion ? 'text-red-600' : 'text-green-600'}`}>
            {motionText}
          </div>
          <div className="text-xs text-gray-500 mt-1">
            {new Date(reading.timestamp).toLocaleTimeString()}
          </div>
        </div>
      </div>
    </div>
  );
}