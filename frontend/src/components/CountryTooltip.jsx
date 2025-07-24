import React from 'react';

const CountryTooltip = ({ countryName, position, visible }) => {
  if (!visible || !countryName) return null;

  return (
    <div
      className="fixed z-50 bg-gray-900/95 backdrop-blur-sm text-white px-4 py-2 rounded-lg shadow-xl pointer-events-none transition-all duration-200 ease-out transform"
      style={{
        left: position.x + 15,
        top: position.y - 40,
        transform: visible ? 'translateY(0) scale(1)' : 'translateY(10px) scale(0.95)',
        opacity: visible ? 1 : 0
      }}
    >
      <div className="text-sm font-medium">{countryName}</div>
      <div className="absolute -bottom-1 left-4 w-2 h-2 bg-gray-900/95 rotate-45 transform"></div>
    </div>
  );
};

export default CountryTooltip;