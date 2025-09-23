import React from 'react';
import { motion } from 'framer-motion';
import { X, MapPin, Camera, Calendar, Users } from 'lucide-react';
import SafeImage from './SafeImage';

const DestinationModal = ({ destination, isOpen, onClose, onPlanTrip, onViewAllImages }) => {
  if (!isOpen || !destination) return null;

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      className="fixed inset-0 bg-black/70 backdrop-blur-sm z-[60] flex items-center justify-center p-4"
      onClick={onClose}
    >
      <motion.div
        initial={{ scale: 0.9, y: 20 }}
        animate={{ scale: 1, y: 0 }}
        exit={{ scale: 0.9, y: 20 }}
        className="bg-white rounded-2xl max-w-4xl w-full max-h-[90vh] overflow-hidden shadow-2xl"
        onClick={e => e.stopPropagation()}
      >
        {/* Hero Image */}
        <div className="relative h-64 overflow-hidden">
          <SafeImage
            src={destination.image}
            alt={destination.name}
            className="w-full h-full object-cover"
            destination={destination.name}
            category="destination"
          />
          <div className="absolute inset-0 bg-gradient-to-t from-black/50 to-transparent" />
          
          <button
            onClick={onClose}
            className="absolute top-4 right-4 p-2 bg-black/20 backdrop-blur-sm text-white rounded-full hover:bg-black/40 transition-colors"
          >
            <X className="w-5 h-5" />
          </button>

          <div className="absolute bottom-4 left-4 text-white">
            <h2 className="text-3xl font-bold mb-2">{destination.name}</h2>
            <div className="flex items-center gap-2 text-sm opacity-90">
              <MapPin className="w-4 h-4" />
              <span>{destination.country}</span>
            </div>
          </div>
        </div>

        <div className="p-6">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {/* Main Info */}
            <div className="md:col-span-2">
              <p className="text-slate-600 text-lg leading-relaxed mb-6">
                {destination.description}
              </p>

              {/* Highlights */}
              {destination.highlights && (
                <div className="mb-6">
                  <h3 className="text-xl font-bold text-slate-900 mb-3">Highlights</h3>
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                    {destination.highlights.map((highlight, index) => (
                      <div key={index} className="flex items-start gap-3 p-3 bg-slate-50 rounded-lg">
                        <div className="w-2 h-2 bg-orange-500 rounded-full mt-2 flex-shrink-0" />
                        <span className="text-slate-700">{highlight}</span>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Best Time to Visit */}
              {destination.bestTime && (
                <div className="mb-6">
                  <h3 className="text-xl font-bold text-slate-900 mb-3">Best Time to Visit</h3>
                  <div className="flex items-center gap-2 p-3 bg-blue-50 rounded-lg">
                    <Calendar className="w-5 h-5 text-blue-600" />
                    <span className="text-blue-800">{destination.bestTime}</span>
                  </div>
                </div>
              )}
            </div>

            {/* Side Info */}
            <div className="space-y-6">
              {/* Quick Facts */}
              <div className="bg-slate-50 rounded-xl p-4">
                <h3 className="font-bold text-slate-900 mb-3">Quick Facts</h3>
                <div className="space-y-2 text-sm">
                  {destination.currency && (
                    <div className="flex justify-between">
                      <span className="text-slate-600">Currency:</span>
                      <span className="font-medium">{destination.currency}</span>
                    </div>
                  )}
                  {destination.language && (
                    <div className="flex justify-between">
                      <span className="text-slate-600">Language:</span>
                      <span className="font-medium">{destination.language}</span>
                    </div>
                  )}
                  {destination.timezone && (
                    <div className="flex justify-between">
                      <span className="text-slate-600">Timezone:</span>
                      <span className="font-medium">{destination.timezone}</span>
                    </div>
                  )}
                  {destination.visa && (
                    <div className="flex justify-between">
                      <span className="text-slate-600">Visa:</span>
                      <span className="font-medium">{destination.visa}</span>
                    </div>
                  )}
                </div>
              </div>

              {/* Actions */}
              <div className="space-y-3">
                <button
                  onClick={() => onPlanTrip(destination)}
                  className="w-full bg-gradient-to-r from-orange-500 to-orange-600 text-white py-3 px-4 rounded-xl hover:from-orange-600 hover:to-orange-700 transition-all duration-200 font-semibold shadow-lg"
                >
                  Plan a Trip Here
                </button>

                {onViewAllImages && (
                  <button
                    onClick={() => onViewAllImages(destination)}
                    className="w-full flex items-center justify-center gap-2 border border-slate-300 text-slate-700 py-3 px-4 rounded-xl hover:bg-slate-50 transition-colors"
                  >
                    <Camera className="w-4 h-4" />
                    View Gallery
                  </button>
                )}
              </div>
            </div>
          </div>
        </div>
      </motion.div>
    </motion.div>
  );
};

export default DestinationModal;