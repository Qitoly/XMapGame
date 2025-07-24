import React from 'react';

const CountryTooltip = ({ countryName, position, visible }) => {
  if (!visible || !countryName) return null;

  return (
    <div
      className="fixed z-50 pointer-events-none transition-all duration-300 ease-out transform"
      style={{
        left: position.x + 15,
        top: position.y - 50,
        transform: visible ? 'translateY(0) scale(1)' : 'translateY(10px) scale(0.95)',
        opacity: visible ? 1 : 0
      }}
    >
      <div className="bg-gradient-to-r from-gray-900 via-gray-800 to-gray-900 backdrop-blur-lg text-white px-6 py-3 rounded-2xl shadow-2xl border border-gray-700/50">
        <div className="text-lg font-semibold tracking-wide">{countryName}</div>
        <div className="absolute -bottom-2 left-6 w-4 h-4 bg-gray-900 rotate-45 transform border-r border-b border-gray-700/50"></div>
      </div>
      
      {/* Дополнительное свечение */}
      <div className="absolute inset-0 bg-gradient-to-r from-blue-500/20 via-purple-500/20 to-pink-500/20 rounded-2xl blur-xl -z-10 animate-pulse"></div>
    </div>
  );
};

export default CountryTooltip;