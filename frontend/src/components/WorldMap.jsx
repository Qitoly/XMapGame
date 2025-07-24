import React, { useState, useCallback } from 'react';
import CountryTooltip from './CountryTooltip';
import { getCountryData } from '../mock';

const WorldMap = () => {
  const [hoveredCountry, setHoveredCountry] = useState(null);
  const [tooltipPosition, setTooltipPosition] = useState({ x: 0, y: 0 });

  const handleCountryHover = useCallback((event, countryCode) => {
    const countryData = getCountryData(countryCode);
    setHoveredCountry(countryData.name);
    setTooltipPosition({ x: event.clientX, y: event.clientY });
  }, []);

  const handleCountryLeave = useCallback(() => {
    setHoveredCountry(null);
  }, []);

  const handleMouseMove = useCallback((event) => {
    if (hoveredCountry) {
      setTooltipPosition({ x: event.clientX, y: event.clientY });
    }
  }, [hoveredCountry]);

  return (
    <div className="w-full h-screen bg-gradient-to-br from-slate-50 to-slate-100 flex items-center justify-center p-4">
      <div className="relative w-full max-w-6xl">
        <div className="text-center mb-8">
          <h1 className="text-4xl font-bold text-gray-800 mb-2">Интерактивная карта мира</h1>
          <p className="text-gray-600">Наведите курсор на любую страну</p>
        </div>
        
        <div className="bg-white rounded-2xl shadow-2xl p-8 overflow-hidden">
          <svg
            viewBox="0 0 1000 500"
            className="w-full h-auto cursor-pointer"
            onMouseMove={handleMouseMove}
          >
            {/* Определения для градиентов и эффектов */}
            <defs>
              <filter id="glow">
                <feGaussianBlur stdDeviation="3" result="coloredBlur"/>
                <feMerge> 
                  <feMergeNode in="coloredBlur"/>
                  <feMergeNode in="SourceGraphic"/>
                </feMerge>
              </filter>
              <linearGradient id="countryGradient" x1="0%" y1="0%" x2="100%" y2="100%">
                <stop offset="0%" stopColor="#3b82f6"/>
                <stop offset="100%" stopColor="#1d4ed8"/>
              </linearGradient>
              <linearGradient id="hoverGradient" x1="0%" y1="0%" x2="100%" y2="100%">
                <stop offset="0%" stopColor="#ef4444"/>
                <stop offset="50%" stopColor="#f97316"/>
                <stop offset="100%" stopColor="#eab308"/>
              </linearGradient>
            </defs>

            {/* Северная Америка */}
            <path
              d="M150 100 L200 80 L280 90 L300 120 L280 150 L200 140 L150 130 Z"
              className="country-path transition-all duration-300 ease-out cursor-pointer hover:filter hover:drop-shadow-lg"
              onMouseEnter={(e) => handleCountryHover(e, 'US')}
              onMouseLeave={handleCountryLeave}
            />
            
            <path
              d="M150 70 L250 50 L280 90 L200 80 L150 100 Z"
              className="country-path transition-all duration-300 ease-out cursor-pointer hover:filter hover:drop-shadow-lg"
              onMouseEnter={(e) => handleCountryHover(e, 'CA')}
              onMouseLeave={handleCountryLeave}
            />

            <path
              d="M150 130 L200 140 L280 150 L260 180 L180 170 L150 160 Z"
              className="country-path transition-all duration-300 ease-out cursor-pointer hover:filter hover:drop-shadow-lg"
              onMouseEnter={(e) => handleCountryHover(e, 'MX')}
              onMouseLeave={handleCountryLeave}
            />

            {/* Южная Америка */}
            <path
              d="M200 220 L250 210 L280 240 L270 300 L230 320 L200 280 Z"
              className="country-path transition-all duration-300 ease-out cursor-pointer hover:filter hover:drop-shadow-lg"
              onMouseEnter={(e) => handleCountryHover(e, 'BR')}
              onMouseLeave={handleCountryLeave}
            />

            <path
              d="M180 280 L230 320 L210 380 L160 360 L170 320 Z"
              className="country-path transition-all duration-300 ease-out cursor-pointer hover:filter hover:drop-shadow-lg"
              onMouseEnter={(e) => handleCountryHover(e, 'AR')}
              onMouseLeave={handleCountryLeave}
            />

            <path
              d="M160 320 L210 300 L230 320 L200 350 L170 340 Z"
              className="country-path transition-all duration-300 ease-out cursor-pointer hover:filter hover:drop-shadow-lg"
              onMouseEnter={(e) => handleCountryHover(e, 'CL')}
              onMouseLeave={handleCountryLeave}
            />

            {/* Европа */}
            <path
              d="M420 90 L450 85 L460 110 L440 120 L420 115 Z"
              className="country-path transition-all duration-300 ease-out cursor-pointer hover:filter hover:drop-shadow-lg"
              onMouseEnter={(e) => handleCountryHover(e, 'GB')}
              onMouseLeave={handleCountryLeave}
            />

            <path
              d="M460 110 L490 105 L500 130 L480 135 L460 125 Z"
              className="country-path transition-all duration-300 ease-out cursor-pointer hover:filter hover:drop-shadow-lg"
              onMouseEnter={(e) => handleCountryHover(e, 'FR')}
              onMouseLeave={handleCountryLeave}
            />

            <path
              d="M500 100 L530 95 L540 120 L520 125 L500 115 Z"
              className="country-path transition-all duration-300 ease-out cursor-pointer hover:filter hover:drop-shadow-lg"
              onMouseEnter={(e) => handleCountryHover(e, 'DE')}
              onMouseLeave={handleCountryLeave}
            />

            <path
              d="M480 135 L520 130 L530 160 L500 165 L480 150 Z"
              className="country-path transition-all duration-300 ease-out cursor-pointer hover:filter hover:drop-shadow-lg"
              onMouseEnter={(e) => handleCountryHover(e, 'IT')}
              onMouseLeave={handleCountryLeave}
            />

            <path
              d="M440 140 L480 135 L490 165 L450 170 L440 155 Z"
              className="country-path transition-all duration-300 ease-out cursor-pointer hover:filter hover:drop-shadow-lg"
              onMouseEnter={(e) => handleCountryHover(e, 'ES')}
              onMouseLeave={handleCountryLeave}
            />

            {/* Россия */}
            <path
              d="M540 60 L750 50 L760 120 L550 130 L540 80 Z"
              className="country-path transition-all duration-300 ease-out cursor-pointer hover:filter hover:drop-shadow-lg"
              onMouseEnter={(e) => handleCountryHover(e, 'RU')}
              onMouseLeave={handleCountryLeave}
            />

            {/* Азия */}
            <path
              d="M650 150 L750 140 L760 220 L650 230 L640 180 Z"
              className="country-path transition-all duration-300 ease-out cursor-pointer hover:filter hover:drop-shadow-lg"
              onMouseEnter={(e) => handleCountryHover(e, 'CN')}
              onMouseLeave={handleCountryLeave}
            />

            <path
              d="M600 180 L650 170 L660 240 L610 250 L600 210 Z"
              className="country-path transition-all duration-300 ease-out cursor-pointer hover:filter hover:drop-shadow-lg"
              onMouseEnter={(e) => handleCountryHover(e, 'IN')}
              onMouseLeave={handleCountryLeave}
            />

            <path
              d="M750 140 L800 135 L810 180 L760 185 L750 160 Z"
              className="country-path transition-all duration-300 ease-out cursor-pointer hover:filter hover:drop-shadow-lg"
              onMouseEnter={(e) => handleCountryHover(e, 'JP')}
              onMouseLeave={handleCountryLeave}
            />

            {/* Африка */}
            <path
              d="M480 200 L580 190 L590 300 L480 310 L470 250 Z"
              className="country-path transition-all duration-300 ease-out cursor-pointer hover:filter hover:drop-shadow-lg"
              onMouseEnter={(e) => handleCountryHover(e, 'NG')}
              onMouseLeave={handleCountryLeave}
            />

            <path
              d="M500 320 L580 310 L590 380 L500 390 L490 350 Z"
              className="country-path transition-all duration-300 ease-out cursor-pointer hover:filter hover:drop-shadow-lg"
              onMouseEnter={(e) => handleCountryHover(e, 'ZA')}
              onMouseLeave={handleCountryLeave}
            />

            <path
              d="M520 180 L580 170 L590 200 L530 210 L520 190 Z"
              className="country-path transition-all duration-300 ease-out cursor-pointer hover:filter hover:drop-shadow-lg"
              onMouseEnter={(e) => handleCountryHover(e, 'EG')}
              onMouseLeave={handleCountryLeave}
            />

            {/* Австралия */}
            <path
              d="M750 350 L850 340 L860 390 L750 400 L740 370 Z"
              className="country-path transition-all duration-300 ease-out cursor-pointer hover:filter hover:drop-shadow-lg"
              onMouseEnter={(e) => handleCountryHover(e, 'AU')}
              onMouseLeave={handleCountryLeave}
            />

            {/* Другие страны */}
            <path
              d="M600 240 L650 230 L660 270 L610 280 L600 255 Z"
              className="country-path transition-all duration-300 ease-out cursor-pointer hover:filter hover:drop-shadow-lg"
              onMouseEnter={(e) => handleCountryHover(e, 'TH')}
              onMouseLeave={handleCountryLeave}
            />

            <path
              d="M660 270 L720 260 L730 320 L660 330 L650 295 Z"
              className="country-path transition-all duration-300 ease-out cursor-pointer hover:filter hover:drop-shadow-lg"
              onMouseEnter={(e) => handleCountryHover(e, 'ID')}
              onMouseLeave={handleCountryLeave}
            />
          </svg>
        </div>
      </div>
      
      <CountryTooltip
        countryName={hoveredCountry}
        position={tooltipPosition}
        visible={!!hoveredCountry}
      />
    </div>
  );
};

export default WorldMap;