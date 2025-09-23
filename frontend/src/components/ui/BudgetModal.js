import React, { useState } from 'react';
import { motion } from 'framer-motion';
import { X, DollarSign, TrendingUp } from 'lucide-react';

const BudgetModal = ({ isOpen, onClose, onSelect, currentDestination }) => {
  const [selectedBudget, setSelectedBudget] = useState('');
  const [customBudget, setCustomBudget] = useState('');

  const budgetRanges = [
    {
      id: 'budget',
      label: 'Budget Travel',
      range: '₹10,000 - ₹25,000',
      description: 'Hostels, local transport, street food',
      color: 'green',
      icon: '🎒'
    },
    {
      id: 'mid-range',
      label: 'Mid-Range',
      range: '₹25,000 - ₹50,000',
      description: '3-star hotels, mix of activities',
      color: 'blue',
      icon: '🏨'
    },
    {
      id: 'luxury',
      label: 'Luxury',
      range: '₹50,000 - ₹1,00,000',
      description: '4-5 star hotels, premium experiences',
      color: 'purple',
      icon: '✨'
    },
    {
      id: 'ultra-luxury',
      label: 'Ultra Luxury',
      range: '₹1,00,000+',
      description: 'Exclusive resorts, private experiences',
      color: 'gold',
      icon: '👑'
    }
  ];

  const handleBudgetSelect = (budget) => {
    setSelectedBudget(budget.id);
    setCustomBudget('');
  };

  const handleConfirm = () => {
    if (selectedBudget) {
      const budget = budgetRanges.find(b => b.id === selectedBudget);
      onSelect({
        type: budget.id,
        label: budget.label,
        range: budget.range,
        displayText: `${budget.label} (${budget.range})`
      });
    } else if (customBudget) {
      onSelect({
        type: 'custom',
        label: 'Custom Budget',
        range: `₹${parseInt(customBudget).toLocaleString()}`,
        displayText: `₹${parseInt(customBudget).toLocaleString()}`
      });
    }
    onClose();
  };

  const getColorClasses = (color, isSelected) => {
    const colors = {
      green: isSelected 
        ? 'border-green-500 bg-green-50 text-green-700'
        : 'border-slate-200 hover:border-green-300 hover:bg-green-25',
      blue: isSelected
        ? 'border-blue-500 bg-blue-50 text-blue-700'
        : 'border-slate-200 hover:border-blue-300 hover:bg-blue-25',
      purple: isSelected
        ? 'border-purple-500 bg-purple-50 text-purple-700'
        : 'border-slate-200 hover:border-purple-300 hover:bg-purple-25',
      gold: isSelected
        ? 'border-yellow-500 bg-yellow-50 text-yellow-700'
        : 'border-slate-200 hover:border-yellow-300 hover:bg-yellow-25'
    };
    return colors[color];
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
        <div className="bg-gradient-to-r from-orange-500 to-orange-600 p-6 text-white">
          <div className="flex items-center justify-between">
            <h2 className="text-2xl font-bold">What's your budget?</h2>
            <button
              onClick={onClose}
              className="p-2 bg-white/20 rounded-full hover:bg-white/30 transition-colors"
            >
              <X className="w-5 h-5" />
            </button>
          </div>
          {currentDestination && (
            <p className="text-orange-100 mt-2">For your trip to {currentDestination}</p>
          )}
        </div>

        {/* Content */}
        <div className="p-6 space-y-6">
          {/* Budget Ranges */}
          <div>
            <h3 className="font-semibold text-slate-900 mb-4 flex items-center gap-2">
              <TrendingUp className="w-5 h-5 text-orange-500" />
              Popular Budget Ranges
            </h3>
            <div className="space-y-3">
              {budgetRanges.map((budget) => {
                const isSelected = selectedBudget === budget.id;
                return (
                  <motion.button
                    key={budget.id}
                    onClick={() => handleBudgetSelect(budget)}
                    className={`w-full p-4 rounded-xl border-2 text-left transition-all duration-200 ${getColorClasses(budget.color, isSelected)}`}
                    whileHover={{ scale: 1.02 }}
                    whileTap={{ scale: 0.98 }}
                  >
                    <div className="flex items-start gap-3">
                      <span className="text-2xl">{budget.icon}</span>
                      <div className="flex-1">
                        <div className="flex items-center justify-between">
                          <div className="font-semibold">{budget.label}</div>
                          <div className="font-bold">{budget.range}</div>
                        </div>
                        <div className="text-sm mt-1 opacity-75">{budget.description}</div>
                      </div>
                    </div>
                  </motion.button>
                );
              })}
            </div>
          </div>

          {/* Custom Budget */}
          <div>
            <h3 className="font-semibold text-slate-900 mb-3 flex items-center gap-2">
              <DollarSign className="w-5 h-5 text-orange-500" />
              Custom Budget
            </h3>
            <div className="relative">
              <span className="absolute left-3 top-1/2 transform -translate-y-1/2 text-slate-500">₹</span>
              <input
                type="number"
                placeholder="Enter your budget"
                value={customBudget}
                onChange={(e) => {
                  setCustomBudget(e.target.value);
                  setSelectedBudget('');
                }}
                className="w-full pl-8 pr-4 py-3 border border-slate-300 rounded-lg focus:ring-2 focus:ring-orange-500 focus:border-orange-500"
              />
            </div>
          </div>

          {/* Action Button */}
          <button
            onClick={handleConfirm}
            disabled={!selectedBudget && !customBudget}
            className="w-full bg-gradient-to-r from-orange-500 to-orange-600 text-white py-3 px-4 rounded-xl hover:from-orange-600 hover:to-orange-700 disabled:opacity-50 disabled:cursor-not-allowed transition-all duration-200 font-semibold shadow-lg"
          >
            Confirm Budget
          </button>
        </div>
      </motion.div>
    </motion.div>
  );
};

export default BudgetModal;