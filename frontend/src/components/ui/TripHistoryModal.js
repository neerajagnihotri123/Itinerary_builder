import React from 'react';
import { X, Route } from 'lucide-react';
import SafeImage from './SafeImage';

const TripHistoryModal = ({ isOpen, onClose, tripHistory, onSelectTrip }) => {
  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black/70 backdrop-blur-sm z-[100] flex items-center justify-center p-4">
      <div className="bg-white rounded-2xl max-w-4xl w-full max-h-[90vh] overflow-hidden">
        {/* Header */}
        <div className="bg-gradient-to-r from-blue-500 to-blue-600 text-white p-6">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-2xl font-bold">Your Trips</h2>
              <p className="text-blue-100 text-sm mt-1">
                {tripHistory.length} saved itineraries
              </p>
            </div>
            <button onClick={onClose} className="p-2 hover:bg-blue-700 rounded-lg">
              <X className="w-6 h-6" />
            </button>
          </div>
        </div>

        {/* Content */}
        <div className="p-6">
          {tripHistory.length === 0 ? (
            <div className="text-center py-12">
              <div className="w-24 h-24 bg-slate-100 rounded-full flex items-center justify-center mx-auto mb-4">
                <Route className="w-12 h-12 text-slate-400" />
              </div>
              <h3 className="text-xl font-semibold text-slate-700 mb-2">No trips yet</h3>
              <p className="text-slate-500">Start planning your first adventure to see it here!</p>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 max-h-[60vh] overflow-y-auto">
              {tripHistory.map((trip, index) => (
                <div
                  key={trip.id || index}
                  onClick={() => onSelectTrip(trip)}
                  className="bg-slate-50 rounded-xl p-4 hover:bg-slate-100 cursor-pointer transition-colors border border-slate-200 hover:border-blue-300"
                >
                  {/* Trip Image */}
                  <div className="relative h-32 rounded-lg overflow-hidden mb-3">
                    <SafeImage
                      src={trip.image}
                      alt={trip.title}
                      className="w-full h-full object-cover"
                      destination={trip.destination}
                      category="destination"
                    />
                    <div className="absolute inset-0 bg-gradient-to-t from-black/50 to-transparent"></div>
                    <div className="absolute bottom-2 left-2 text-white">
                      <h4 className="font-semibold text-sm">{trip.title}</h4>
                      <p className="text-xs text-gray-200">{trip.destination}</p>
                    </div>
                  </div>

                  {/* Trip Details */}
                  <div className="space-y-2">
                    <div className="flex items-center justify-between text-sm">
                      <span className="text-slate-600">Duration</span>
                      <span className="font-medium">{trip.days} days</span>
                    </div>
                    <div className="flex items-center justify-between text-sm">
                      <span className="text-slate-600">Activities</span>
                      <span className="font-medium">{trip.totalActivities || 0}</span>
                    </div>
                    <div className="flex items-center justify-between text-sm">
                      <span className="text-slate-600">Total Cost</span>
                      <span className="font-medium text-green-600">₹{trip.totalCost?.toLocaleString()}</span>
                    </div>
                    <div className="flex items-center justify-between text-sm">
                      <span className="text-slate-600">Saved</span>
                      <span className="text-xs text-slate-500">{new Date(trip.savedAt).toLocaleDateString()}</span>
                    </div>
                  </div>

                  {/* Trip Status */}
                  <div className="mt-3 flex items-center gap-2">
                    <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                      trip.status === 'booked' ? 'bg-green-100 text-green-700' :
                      trip.status === 'planning' ? 'bg-blue-100 text-blue-700' :
                      'bg-gray-100 text-gray-700'
                    }`}>
                      {trip.status === 'booked' ? '✅ Booked' : 
                       trip.status === 'planning' ? '📝 Planning' : '💭 Draft'}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default TripHistoryModal;