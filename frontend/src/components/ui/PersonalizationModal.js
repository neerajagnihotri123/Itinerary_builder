import React, { useState } from 'react';
import { motion } from 'framer-motion';
import { X, MapPin, Calendar, Users, DollarSign, Heart, Star } from 'lucide-react';

const PersonalizationModal = ({ isOpen, onClose, onComplete }) => {
  const [currentStep, setCurrentStep] = useState(0);
  const [formData, setFormData] = useState({
    travelStyle: '',
    budget: '',
    interests: [],
    activityLevel: '',
    accommodation: '',
    groupSize: '',
    specialRequirements: ''
  });

  const steps = [
    {
      title: "What's your travel style?",
      key: 'travelStyle',
      type: 'single',
      options: [
        { id: 'luxury', label: 'Luxury & Comfort', icon: '✨', desc: 'Premium experiences and accommodations' },
        { id: 'adventure', label: 'Adventure & Thrills', icon: '🏔️', desc: 'Exciting activities and challenges' },
        { id: 'cultural', label: 'Cultural Immersion', icon: '🏛️', desc: 'Local experiences and traditions' },
        { id: 'budget', label: 'Budget-Friendly', icon: '💰', desc: 'Cost-effective travel options' },
        { id: 'family', label: 'Family-Oriented', icon: '👨‍👩‍👧‍👦', desc: 'Kid-friendly activities and amenities' },
        { id: 'romantic', label: 'Romantic Getaway', icon: '💕', desc: 'Intimate and romantic experiences' }
      ]
    },
    {
      title: "What are your interests?",
      key: 'interests',
      type: 'multiple',
      options: [
        { id: 'food', label: 'Food & Cuisine', icon: '🍜' },
        { id: 'nature', label: 'Nature & Wildlife', icon: '🌲' },
        { id: 'history', label: 'History & Museums', icon: '🏛️' },
        { id: 'adventure', label: 'Adventure Sports', icon: '🏄‍♂️' },
        { id: 'shopping', label: 'Shopping', icon: '🛍️' },
        { id: 'nightlife', label: 'Nightlife & Entertainment', icon: '🎭' },
        { id: 'wellness', label: 'Wellness & Spa', icon: '🧘‍♀️' },
        { id: 'photography', label: 'Photography', icon: '📸' }
      ]
    },
    {
      title: "How active do you want to be?",
      key: 'activityLevel',
      type: 'single',
      options: [
        { id: 'low', label: 'Relaxed Pace', icon: '🛋️', desc: 'Leisurely activities and lots of rest' },
        { id: 'moderate', label: 'Moderate Activity', icon: '🚶‍♂️', desc: 'Mix of activities and relaxation' },
        { id: 'high', label: 'Very Active', icon: '🏃‍♂️', desc: 'Packed schedule with lots of activities' }
      ]
    }
  ];

  const handleOptionSelect = (key, value, isMultiple = false) => {
    if (isMultiple) {
      setFormData(prev => ({
        ...prev,
        [key]: prev[key].includes(value)
          ? prev[key].filter(item => item !== value)
          : [...prev[key], value]
      }));
    } else {
      setFormData(prev => ({ ...prev, [key]: value }));
    }
  };

  const handleNext = () => {
    if (currentStep < steps.length - 1) {
      setCurrentStep(currentStep + 1);
    } else {
      onComplete(formData);
    }
  };

  const handleBack = () => {
    if (currentStep > 0) {
      setCurrentStep(currentStep - 1);
    }
  };

  const isStepValid = () => {
    const step = steps[currentStep];
    const value = formData[step.key];
    
    if (step.type === 'multiple') {
      return value && value.length > 0;
    }
    return value && value.trim() !== '';
  };

  if (!isOpen) return null;

  const currentStepData = steps[currentStep];

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      className="fixed inset-0 bg-black/60 backdrop-blur-sm z-[60] flex items-center justify-center p-4"
    >
      <motion.div
        initial={{ scale: 0.9, opacity: 0 }}
        animate={{ scale: 1, opacity: 1 }}
        exit={{ scale: 0.9, opacity: 0 }}
        className="bg-white rounded-3xl max-w-2xl w-full max-h-[90vh] overflow-hidden shadow-2xl"
      >
        {/* Header */}
        <div className="bg-gradient-to-r from-orange-500 to-orange-600 p-6 text-white relative">
          <button
            onClick={onClose}
            className="absolute top-4 right-4 p-2 bg-white/20 rounded-full hover:bg-white/30 transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
          <div className="pr-12">
            <h2 className="text-2xl font-bold mb-2">Personalize Your Experience</h2>
            <div className="flex items-center gap-2">
              <div className="text-sm opacity-90">
                Step {currentStep + 1} of {steps.length}
              </div>
              <div className="flex-1 h-2 bg-white/20 rounded-full ml-3">
                <div
                  className="h-full bg-white rounded-full transition-all duration-500"
                  style={{ width: `${((currentStep + 1) / steps.length) * 100}%` }}
                />
              </div>
            </div>
          </div>
        </div>

        {/* Content */}
        <div className="p-8">
          <h3 className="text-2xl font-bold text-slate-900 mb-6 text-center">
            {currentStepData.title}
          </h3>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-8">
            {currentStepData.options.map((option) => {
              const isSelected = currentStepData.type === 'multiple' 
                ? formData[currentStepData.key].includes(option.id)
                : formData[currentStepData.key] === option.id;

              return (
                <motion.button
                  key={option.id}
                  onClick={() => handleOptionSelect(currentStepData.key, option.id, currentStepData.type === 'multiple')}
                  className={`p-4 rounded-xl border-2 text-left transition-all duration-200 ${
                    isSelected
                      ? 'border-orange-500 bg-orange-50 shadow-md'
                      : 'border-slate-200 hover:border-orange-300 hover:bg-orange-25'
                  }`}
                  whileHover={{ scale: 1.02 }}
                  whileTap={{ scale: 0.98 }}
                >
                  <div className="flex items-start gap-3">
                    <span className="text-2xl">{option.icon}</span>
                    <div className="flex-1">
                      <div className={`font-semibold ${isSelected ? 'text-orange-700' : 'text-slate-800'}`}>
                        {option.label}
                      </div>
                      {option.desc && (
                        <div className={`text-sm mt-1 ${isSelected ? 'text-orange-600' : 'text-slate-600'}`}>
                          {option.desc}
                        </div>
                      )}
                    </div>
                    {isSelected && (
                      <div className="text-orange-500">
                        <Star className="w-5 h-5 fill-current" />
                      </div>
                    )}
                  </div>
                </motion.button>
              );
            })}
          </div>

          {/* Navigation */}
          <div className="flex justify-between">
            <button
              onClick={handleBack}
              disabled={currentStep === 0}
              className="px-6 py-3 border border-slate-300 text-slate-700 rounded-xl hover:bg-slate-50 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              Back
            </button>

            <button
              onClick={handleNext}
              disabled={!isStepValid()}
              className="px-8 py-3 bg-gradient-to-r from-orange-500 to-orange-600 text-white rounded-xl hover:from-orange-600 hover:to-orange-700 disabled:opacity-50 disabled:cursor-not-allowed transition-all duration-200 shadow-lg"
            >
              {currentStep === steps.length - 1 ? 'Complete Setup' : 'Next'}
            </button>
          </div>
        </div>
      </motion.div>
    </motion.div>
  );
};

export default PersonalizationModal;