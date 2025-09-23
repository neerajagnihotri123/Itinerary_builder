import React, { useState } from 'react';
import { motion } from 'framer-motion';
import { X, Calendar, Clock } from 'lucide-react';

const WhenModal = ({ isOpen, onClose, onSelect, currentDates }) => {
  const [startDate, setStartDate] = useState('');
  const [endDate, setEndDate] = useState('');
  const [duration, setDuration] = useState('');

  const quickOptions = [
    { label: 'This Weekend', value: 'this-weekend', days: 2 },
    { label: 'Next Week', value: 'next-week', days: 7 },
    { label: '3 Days', value: '3-days', days: 3 },
    { label: '1 Week', value: '1-week', days: 7 },
    { label: '2 Weeks', value: '2-weeks', days: 14 },
    { label: '1 Month', value: '1-month', days: 30 }
  ];

  const handleQuickSelect = (option) => {
    const today = new Date();
    let start, end;

    switch (option.value) {
      case 'this-weekend':
        start = new Date(today);
        start.setDate(today.getDate() + (6 - today.getDay())); // Next Saturday
        end = new Date(start);
        end.setDate(start.getDate() + 1); // Sunday
        break;
      case 'next-week':
        start = new Date(today);
        start.setDate(today.getDate() + 7);
        end = new Date(start);
        end.setDate(start.getDate() + 7);
        break;
      default:
        start = new Date(today);
        start.setDate(today.getDate() + 1);
        end = new Date(start);
        end.setDate(start.getDate() + option.days - 1);
    }

    const formatDate = (date) => date.toISOString().split('T')[0];
    
    setStartDate(formatDate(start));
    setEndDate(formatDate(end));
    setDuration(`${option.days} days`);
  };

  const handleConfirm = () => {
    if (startDate && endDate) {
      const start = new Date(startDate);
      const end = new Date(endDate);
      const days = Math.ceil((end - start) / (1000 * 60 * 60 * 24)) + 1;
      
      onSelect({
        startDate,
        endDate,
        duration: `${days} days`,
        displayText: `${start.toLocaleDateString()} - ${end.toLocaleDateString()}`
      });
      onClose();
    }
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
        className="bg-white rounded-2xl max-w-lg w-full max-h-[80vh] overflow-hidden shadow-2xl"
        onClick={e => e.stopPropagation()}
      >
        {/* Header */}
        <div className="bg-gradient-to-r from-green-500 to-green-600 p-6 text-white">
          <div className="flex items-center justify-between">
            <h2 className="text-2xl font-bold">When are you traveling?</h2>
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
          {/* Quick Options */}
          <div>
            <h3 className="font-semibold text-slate-900 mb-3 flex items-center gap-2">
              <Clock className="w-5 h-5 text-green-500" />
              Quick Options
            </h3>
            <div className="grid grid-cols-2 gap-3">
              {quickOptions.map((option) => (
                <motion.button
                  key={option.value}
                  onClick={() => handleQuickSelect(option)}
                  className="p-3 text-left border border-slate-200 rounded-lg hover:border-green-300 hover:bg-green-50 transition-colors"
                  whileHover={{ scale: 1.02 }}
                  whileTap={{ scale: 0.98 }}
                >
                  <div className="font-medium text-slate-900">{option.label}</div>
                  <div className="text-sm text-slate-600">{option.days} days</div>
                </motion.button>
              ))}
            </div>
          </div>

          {/* Custom Dates */}
          <div>
            <h3 className="font-semibold text-slate-900 mb-3 flex items-center gap-2">
              <Calendar className="w-5 h-5 text-green-500" />
              Custom Dates
            </h3>
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-2">
                  Start Date
                </label>
                <input
                  type="date"
                  value={startDate}
                  onChange={(e) => setStartDate(e.target.value)}
                  min={new Date().toISOString().split('T')[0]}
                  className="w-full px-4 py-3 border border-slate-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-green-500"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-slate-700 mb-2">
                  End Date
                </label>
                <input
                  type="date"
                  value={endDate}
                  onChange={(e) => setEndDate(e.target.value)}
                  min={startDate || new Date().toISOString().split('T')[0]}
                  className="w-full px-4 py-3 border border-slate-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-green-500"
                />
              </div>
            </div>
          </div>

          {/* Action Button */}
          <button
            onClick={handleConfirm}
            disabled={!startDate || !endDate}
            className="w-full bg-gradient-to-r from-green-500 to-green-600 text-white py-3 px-4 rounded-xl hover:from-green-600 hover:to-green-700 disabled:opacity-50 disabled:cursor-not-allowed transition-all duration-200 font-semibold shadow-lg"
          >
            Confirm Dates
          </button>
        </div>
      </motion.div>
    </motion.div>
  );
};

export default WhenModal;