import React, { useState, useCallback } from 'react';
import { 
  ComposableMap, 
  Geographies, 
  Geography 
} from 'react-simple-maps';
import CountryTooltip from './CountryTooltip';
import { getCountryData } from '../mock';

// URL для карты мира (TopoJSON формат)
const geoUrl = "https://cdn.jsdelivr.net/npm/world-atlas@2/countries-110m.json";

const WorldMap = () => {
  const [hoveredCountry, setHoveredCountry] = useState(null);
  const [tooltipPosition, setTooltipPosition] = useState({ x: 0, y: 0 });

  const handleCountryHover = useCallback((event, geo) => {
    const countryCode = geo.properties.ISO_A2;
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
    <div className="w-full h-screen bg-gradient-to-br from-slate-50 via-blue-50 to-indigo-50 flex items-center justify-center p-4 overflow-hidden">
      <div className="relative w-full max-w-7xl">
        <div className="text-center mb-8 animate-fade-in">
          <h1 className="text-5xl font-bold bg-gradient-to-r from-blue-600 via-purple-600 to-blue-800 bg-clip-text text-transparent mb-4">
            Интерактивная карта мира
          </h1>
          <p className="text-xl text-gray-600 font-medium">
            Наведите курсор на любую страну для получения информации
          </p>
          <div className="w-24 h-1 bg-gradient-to-r from-blue-500 to-purple-500 mx-auto mt-4 rounded-full"></div>
        </div>
        
        <div 
          className="bg-white/80 backdrop-blur-sm rounded-3xl shadow-2xl p-8 border border-white/20 map-container"
          onMouseMove={handleMouseMove}
        >
          <ComposableMap
            projectionConfig={{
              scale: 150,
              center: [0, 20]
            }}
            style={{
              width: "100%",
              height: "500px"
            }}
          >
            <Geographies geography={geoUrl}>
              {({ geographies }) =>
                geographies.map((geo) => (
                  <Geography
                    key={geo.rsmKey}
                    geography={geo}
                    onMouseEnter={(event) => handleCountryHover(event, geo)}
                    onMouseLeave={handleCountryLeave}
                    style={{
                      default: {
                        fill: "#e2e8f0",
                        stroke: "#cbd5e1",
                        strokeWidth: 0.5,
                        outline: "none",
                        transition: "all 0.3s cubic-bezier(0.4, 0, 0.2, 1)"
                      },
                      hover: {
                        fill: "url(#hoverGradient)",
                        stroke: "#ef4444",
                        strokeWidth: 2,
                        outline: "none",
                        transform: "scale(1.02)",
                        filter: "drop-shadow(0 10px 20px rgba(239, 68, 68, 0.3))",
                        transition: "all 0.2s cubic-bezier(0.4, 0, 0.2, 1)"
                      },
                      pressed: {
                        fill: "#dc2626",
                        stroke: "#b91c1c",
                        strokeWidth: 2,
                        outline: "none"
                      }
                    }}
                    className="country-geography cursor-pointer"
                  />
                ))
              }
            </Geographies>
            
            {/* Определения градиентов */}
            <defs>
              <linearGradient id="hoverGradient" x1="0%" y1="0%" x2="100%" y2="100%">
                <stop offset="0%" stopColor="#ef4444" stopOpacity="0.9"/>
                <stop offset="30%" stopColor="#f97316" stopOpacity="0.8"/>
                <stop offset="70%" stopColor="#eab308" stopOpacity="0.9"/>
                <stop offset="100%" stopColor="#22c55e" stopOpacity="0.8"/>
              </linearGradient>
              
              <filter id="glow">
                <feGaussianBlur stdDeviation="4" result="coloredBlur"/>
                <feMerge> 
                  <feMergeNode in="coloredBlur"/>
                  <feMergeNode in="SourceGraphic"/>
                </feMerge>
              </filter>
            </defs>
          </ComposableMap>
        </div>
        
        {/* Декоративные элементы */}
        <div className="absolute -top-20 -left-20 w-40 h-40 bg-gradient-to-br from-blue-400/20 to-purple-400/20 rounded-full blur-3xl animate-pulse"></div>
        <div className="absolute -bottom-20 -right-20 w-60 h-60 bg-gradient-to-br from-purple-400/20 to-pink-400/20 rounded-full blur-3xl animate-pulse delay-1000"></div>
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