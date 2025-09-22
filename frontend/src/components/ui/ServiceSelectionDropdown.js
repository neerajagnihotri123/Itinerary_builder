import React, { useState, useEffect } from 'react';

const ServiceSelectionDropdown = ({ serviceType, location, currentService, onServiceChange, travelerProfile, sessionId, API }) => {
  const [services, setServices] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [isOpen, setIsOpen] = useState(false);

  useEffect(() => {
    if (isOpen && services.length === 0) {
      fetchServiceOptions();
    }
  }, [isOpen]);

  const fetchServiceOptions = async () => {
    setIsLoading(true);
    try {
      const response = await fetch(`${API}/service-recommendations`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          session_id: sessionId,
          service_type: serviceType,
          location: location,
          traveler_profile: travelerProfile || {},
          activity_context: {}
        })
      });
      
      const data = await response.json();
      setServices(data.services || []);
    } catch (error) {
      console.error('Service fetch error:', error);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="relative">
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="flex items-center justify-between w-full p-2 bg-white border border-slate-300 rounded-lg hover:border-orange-400 transition-colors"
      >
        <div className="flex items-center gap-2">
          <span className="text-sm font-medium">{currentService?.name || 'Select Service'}</span>
          {currentService?.rating && (
            <span className="text-xs text-slate-500">⭐ {currentService.rating}</span>
          )}
        </div>
        <span className="text-slate-400">▼</span>
      </button>

      {isOpen && (
        <div className="absolute top-full left-0 right-0 mt-1 bg-white border border-slate-300 rounded-lg shadow-lg z-50 max-h-80 overflow-y-auto">
          {isLoading ? (
            <div className="p-4 text-center text-slate-500">Loading options...</div>
          ) : (
            services.map((service, index) => (
              <div
                key={service.id}
                onClick={() => {
                  onServiceChange(service);
                  setIsOpen(false);
                }}
                className={`p-3 hover:bg-orange-50 cursor-pointer border-b border-slate-100 ${
                  index === 0 ? 'bg-orange-25 border-l-4 border-l-orange-500' : ''
                }`}
              >
                <div className="flex items-center justify-between">
                  <div className="flex-1">
                    <div className="flex items-center gap-2">
                      <h4 className="font-semibold text-sm text-slate-800">{service.name}</h4>
                      {index === 0 && (
                        <span className="bg-orange-500 text-white text-xs px-2 py-0.5 rounded-full">Auto-Selected</span>
                      )}
                    </div>
                    <p className="text-xs text-slate-600 mt-1">{service.description}</p>
                    <div className="flex items-center gap-3 mt-2">
                      <span className="text-xs bg-slate-100 px-2 py-1 rounded">⭐ {service.rating}</span>
                      <span className="text-xs bg-green-100 text-green-700 px-2 py-1 rounded">₹{service.price}</span>
                      <span className="text-xs bg-blue-100 text-blue-700 px-2 py-1 rounded">Match: {(service.similarity_score * 100).toFixed(0)}%</span>
                    </div>
                  </div>
                </div>
                {service.match_reasons && (
                  <div className="mt-2">
                    <div className="flex flex-wrap gap-1">
                      {service.match_reasons.slice(0, 2).map((reason, idx) => (
                        <span key={idx} className="text-xs text-slate-500 bg-slate-50 px-2 py-0.5 rounded">
                          {reason}
                        </span>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            ))
          )}
        </div>
      )}
    </div>
  );
};

export default ServiceSelectionDropdown;