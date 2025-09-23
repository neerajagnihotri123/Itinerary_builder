import React, { useState } from 'react';
import { motion } from 'framer-motion';
import { X, Search, MapPin, TrendingUp } from 'lucide-react';

const WhereModal = ({ isOpen, onClose, onSelect, currentDestination }) => {
  const [searchTerm, setSearchTerm] = useState('');

  const popularDestinations = [
    { id: 1, name: 'Goa', country: 'India', type: 'Beach Paradise', image: 'goa.jpg' },
    { id: 2, name: 'Kerala', country: 'India', type: 'Backwaters & Spices', image: 'kerala.jpg' },
    { id: 3, name: 'Rajasthan', country: 'India', type: 'Royal Heritage', image: 'rajasthan.jpg' },
    { id: 4, name: 'Himachal Pradesh', country: 'India', type: 'Mountain Adventure', image: 'himachal.jpg' },
    { id: 5, name: 'Mumbai', country: 'India', type: 'City of Dreams', image: 'mumbai.jpg' },
    { id: 6, name: 'Delhi', country: 'India', type: 'Cultural Capital', image: 'delhi.jpg' }
  ];

  const filteredDestinations = popularDestinations.filter(dest =>
    dest.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
    dest.type.toLowerCase().includes(searchTerm.toLowerCase())
  );

  if (!isOpen) return null;

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      className="fixed inset-0 bg-black/60 backdrop-blur-sm z-[60] flex items-center justify-center p-4"
      onClick={onClose}
    >
      <motion.div
        initial={{ scale: 0.9, y: 20 }}
        animate={{ scale: 1, y: 0 }}
        exit={{ scale: 0.9, y: 20 }}
        className="bg-white rounded-2xl max-w-2xl w-full max-h-[80vh] overflow-hidden shadow-2xl"
        onClick={e => e.stopPropagation()}
      >
        {/* Header */}
        <div className="bg-gradient-to-r from-blue-500 to-blue-600 p-6 text-white">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-2xl font-bold">Where do you want to go?</h2>
            <button
              onClick={onClose}
              className="p-2 bg-white/20 rounded-full hover:bg-white/30 transition-colors"
            >
              <X className="w-5 h-5" />
            </button>
          </div>

          {/* Search */}
          <div className="relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-slate-400" />
            <input
              type="text"
              placeholder="Search destinations..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full pl-10 pr-4 py-3 rounded-xl bg-white text-slate-900 placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-blue-300"
            />
          </div>
        </div>

        {/* Content */}
        <div className="p-6 max-h-96 overflow-y-auto">
          <div className="flex items-center gap-2 mb-4">
            <TrendingUp className="w-5 h-5 text-orange-500" />
            <h3 className="font-semibold text-slate-900">Popular Destinations</h3>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            {filteredDestinations.map((destination) => (
              <motion.button
                key={destination.id}
                onClick={() => {
                  onSelect(destination.name);
                  onClose();
                }}
                className="text-left p-4 rounded-xl border border-slate-200 hover:border-blue-300 hover:bg-blue-50 transition-all duration-200"
                whileHover={{ scale: 1.02 }}
                whileTap={{ scale: 0.98 }}
              >
                <div className="flex items-start gap-3">
                  <MapPin className="w-5 h-5 text-blue-500 mt-0.5" />
                  <div className="flex-1">
                    <div className="font-semibold text-slate-900">{destination.name}</div>
                    <div className="text-sm text-slate-600">{destination.type}</div>
                    <div className="text-xs text-slate-500 mt-1">{destination.country}</div>
                  </div>
                </div>
              </motion.button>
            ))}
          </div>

          {filteredDestinations.length === 0 && (
            <div className="text-center py-8 text-slate-500">
              <MapPin className="w-12 h-12 mx-auto mb-3 text-slate-300" />
              <p>No destinations found for "{searchTerm}"</p>
            </div>
          )}
        </div>
      </motion.div>
    </motion.div>
  );
};

export default WhereModal;