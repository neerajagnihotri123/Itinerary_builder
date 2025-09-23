import React, { useState } from 'react';
import { motion } from 'framer-motion';
import { X, Users, Plus, Minus } from 'lucide-react';

const TravelersModal = ({ isOpen, onClose, onSelect, currentTravelers }) => {
  const [travelers, setTravelers] = useState({
    adults: 2,
    children: 0,
    infants: 0
  });

  const updateCount = (type, change) => {
    setTravelers(prev => ({
      ...prev,
      [type]: Math.max(0, prev[type] + change)
    }));
  };

  const getTotalTravelers = () => {
    return travelers.adults + travelers.children + travelers.infants;
  };

  const getDisplayText = () => {
    const parts = [];
    if (travelers.adults > 0) parts.push(`${travelers.adults} Adult${travelers.adults > 1 ? 's' : ''}`);
    if (travelers.children > 0) parts.push(`${travelers.children} Child${travelers.children > 1 ? 'ren' : ''}`);
    if (travelers.infants > 0) parts.push(`${travelers.infants} Infant${travelers.infants > 1 ? 's' : ''}`);
    return parts.join(', ');
  };

  const handleConfirm = () => {
    onSelect({
      ...travelers,
      total: getTotalTravelers(),
      displayText: getDisplayText()
    });
    onClose();
  };

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
        className="bg-white rounded-2xl max-w-md w-full shadow-2xl"
        onClick={e => e.stopPropagation()}
      >
        {/* Header */}
        <div className="bg-gradient-to-r from-purple-500 to-purple-600 p-6 text-white">
          <div className="flex items-center justify-between">
            <h2 className="text-2xl font-bold">How many travelers?</h2>
            <button
              onClick={onClose}
              className="p-2 bg-white/20 rounded-full hover:bg-white/30 transition-colors"
            >
              <X className="w-5 h-5" />
            </button>
          </div>
        </div>

        {/* Content */}
        <div className="p-6 space-y-6">
          {/* Adults */}
          <div className="flex items-center justify-between">
            <div>
              <div className="font-semibold text-slate-900">Adults</div>
              <div className="text-sm text-slate-600">Ages 13 or above</div>
            </div>
            <div className="flex items-center gap-3">
              <button
                onClick={() => updateCount('adults', -1)}
                disabled={travelers.adults <= 1}
                className="p-2 border border-slate-300 rounded-lg hover:bg-slate-50 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                <Minus className="w-4 h-4" />
              </button>
              <span className="w-8 text-center font-semibold">{travelers.adults}</span>
              <button
                onClick={() => updateCount('adults', 1)}
                className="p-2 border border-slate-300 rounded-lg hover:bg-slate-50"
              >
                <Plus className="w-4 h-4" />
              </button>
            </div>
          </div>

          {/* Children */}
          <div className="flex items-center justify-between">
            <div>
              <div className="font-semibold text-slate-900">Children</div>
              <div className="text-sm text-slate-600">Ages 2-12</div>
            </div>
            <div className="flex items-center gap-3">
              <button
                onClick={() => updateCount('children', -1)}
                disabled={travelers.children <= 0}
                className="p-2 border border-slate-300 rounded-lg hover:bg-slate-50 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                <Minus className="w-4 h-4" />
              </button>
              <span className="w-8 text-center font-semibold">{travelers.children}</span>
              <button
                onClick={() => updateCount('children', 1)}
                className="p-2 border border-slate-300 rounded-lg hover:bg-slate-50"
              >
                <Plus className="w-4 h-4" />
              </button>
            </div>
          </div>

          {/* Infants */}
          <div className="flex items-center justify-between">
            <div>
              <div className="font-semibold text-slate-900">Infants</div>
              <div className="text-sm text-slate-600">Under 2</div>
            </div>
            <div className="flex items-center gap-3">
              <button
                onClick={() => updateCount('infants', -1)}
                disabled={travelers.infants <= 0}
                className="p-2 border border-slate-300 rounded-lg hover:bg-slate-50 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                <Minus className="w-4 h-4" />
              </button>
              <span className="w-8 text-center font-semibold">{travelers.infants}</span>
              <button
                onClick={() => updateCount('infants', 1)}
                className="p-2 border border-slate-300 rounded-lg hover:bg-slate-50"
              >
                <Plus className="w-4 h-4" />
              </button>
            </div>
          </div>

          {/* Summary */}
          <div className="p-4 bg-purple-50 rounded-xl">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Users className="w-5 h-5 text-purple-600" />
                <span className="font-medium text-purple-900">Total Travelers</span>
              </div>
              <span className="text-2xl font-bold text-purple-600">{getTotalTravelers()}</span>
            </div>
            {getDisplayText() && (
              <div className="mt-2 text-sm text-purple-700">{getDisplayText()}</div>
            )}
          </div>

          {/* Action Button */}
          <button
            onClick={handleConfirm}
            className="w-full bg-gradient-to-r from-purple-500 to-purple-600 text-white py-3 px-4 rounded-xl hover:from-purple-600 hover:to-purple-700 transition-all duration-200 font-semibold shadow-lg"
          >
            Confirm Travelers
          </button>
        </div>
      </motion.div>
    </motion.div>
  );
};

export default TravelersModal;