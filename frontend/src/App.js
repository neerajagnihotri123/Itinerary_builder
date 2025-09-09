import React, { useState, useEffect, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import './App.css';
import axios from 'axios';
import { 
  Send, 
  MapPin, 
  Star, 
  Calendar, 
  Users, 
  Mic, 
  Navigation, 
  Hotel,
  Plane,
  Heart,
  Clock,
  DollarSign,
  X,
  ChevronRight,
  Upload,
  Link,
  Menu,
  Plus,
  MessageCircle,
  FileText,
  Image,
  Edit3,
  Eye,
  Utensils,
  Cloud,
  Shield,
  ArrowLeft,
  Clock
} from 'lucide-react';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

// Animation variants
const cardVariants = {
  hidden: { opacity: 0, y: 12, scale: 0.995 },
  visible: { 
    opacity: 1, 
    y: 0, 
    scale: 1, 
    transition: { 
      duration: 0.26, 
      type: 'spring', 
      damping: 16 
    } 
  },
  exit: { 
    opacity: 0, 
    y: 8, 
    transition: { duration: 0.18 } 
  }
};

const chipVariants = {
  hidden: { scale: 0.96, opacity: 0 },
  visible: { 
    scale: 1, 
    opacity: 1, 
    transition: { 
      type: 'spring', 
      damping: 16, 
      duration: 0.26 
    } 
  }
};

const modalVariants = {
  hidden: { opacity: 0, scale: 0.95 },
  visible: { 
    opacity: 1, 
    scale: 1, 
    transition: { 
      duration: 0.36, 
      type: 'spring', 
      damping: 20 
    } 
  },
  exit: { 
    opacity: 0, 
    scale: 0.95, 
    transition: { duration: 0.24 } 
  }
};

// Components
const Avatar = () => (
  <motion.div 
    className="w-12 h-12 rounded-full bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center shadow-lg"
    animate={{ 
      boxShadow: ['0 4px 20px rgba(59, 130, 246, 0.3)', '0 4px 30px rgba(147, 51, 234, 0.4)', '0 4px 20px rgba(59, 130, 246, 0.3)']
    }}
    transition={{ 
      duration: 2, 
      repeat: Infinity, 
      repeatType: 'reverse' 
    }}
  >
    <Plane className="w-6 h-6 text-white" />
  </motion.div>
);

const RecommendationCard = ({ item, onAction }) => {
  const [isHovered, setIsHovered] = useState(false);
  
  return (
    <motion.div
      variants={cardVariants}
      initial="hidden"
      animate="visible"
      exit="exit"
      layout
      className="bg-white/90 backdrop-blur-md rounded-2xl shadow-xl border border-white/20 overflow-hidden mb-4 cursor-pointer"
      onMouseEnter={() => setIsHovered(true)}
      onMouseLeave={() => setIsHovered(false)}
      whileHover={{ 
        y: -6, 
        boxShadow: '0 20px 40px rgba(0,0,0,0.15)' 
      }}
      transition={{ duration: 0.2 }}
    >
      <div className="relative h-48 overflow-hidden">
        <motion.img
          src={item.hero_image}
          alt={item.title}
          className="w-full h-full object-cover"
          animate={{ scale: isHovered ? 1.05 : 1 }}
          transition={{ duration: 0.3 }}
        />
        <div className="absolute inset-0 bg-gradient-to-t from-black/50 to-transparent" />
        <div className="absolute bottom-4 left-4 text-white">
          <h3 className="text-xl font-bold mb-1">{item.title}</h3>
          {item.weather && (
            <div className="flex items-center gap-2 text-sm">
              <span>{item.weather.temp}</span>
              <span>•</span>
              <span>{item.weather.condition}</span>
            </div>
          )}
        </div>
        {item.rating && (
          <div className="absolute top-4 right-4 bg-white/90 backdrop-blur-sm rounded-full px-3 py-1 flex items-center gap-1">
            <Star className="w-4 h-4 text-yellow-500 fill-current" />
            <span className="text-sm font-semibold">{item.rating}</span>
          </div>
        )}
      </div>
      
      <div className="p-6">
        <p className="text-gray-600 mb-3 leading-relaxed">{item.pitch}</p>
        
        {item.why_match && (
          <div className="bg-blue-50 rounded-lg p-3 mb-4">
            <p className="text-blue-700 text-sm font-medium">
              <Heart className="w-4 h-4 inline mr-2" />
              {item.why_match}
            </p>
          </div>
        )}
        
        {item.highlights && (
          <div className="mb-4">
            <h4 className="font-semibold text-gray-800 mb-2">Highlights</h4>
            <div className="flex flex-wrap gap-2">
              {item.highlights.slice(0, 3).map((highlight, index) => (
                <span
                  key={index}
                  className="bg-gray-100 text-gray-700 px-3 py-1 rounded-full text-sm"
                >
                  {highlight}
                </span>
              ))}
            </div>
          </div>
        )}
        
        {item.price_estimate && (
          <div className="flex items-center gap-2 mb-4 text-green-600">
            <DollarSign className="w-4 h-4" />
            <span className="font-semibold">
              ${item.price_estimate.min} - ${item.price_estimate.max} / night
            </span>
          </div>
        )}
        
        <div className="flex gap-3">
          <motion.button
            onClick={() => onAction(item.cta_primary?.action, item)}
            className="flex-1 bg-gradient-to-r from-blue-600 to-purple-600 text-white font-semibold py-3 px-6 rounded-xl hover:from-blue-700 hover:to-purple-700 transition-all duration-200 flex items-center justify-center gap-2"
            whileHover={{ scale: 1.02 }}
            whileTap={{ scale: 0.98 }}
          >
            {item.cta_primary?.label || 'Explore'}
            <ChevronRight className="w-4 h-4" />
          </motion.button>
          
          <motion.button
            onClick={() => onAction(item.cta_secondary?.action, item)}
            className="px-6 py-3 border-2 border-gray-200 text-gray-700 font-semibold rounded-xl hover:border-gray-300 hover:bg-gray-50 transition-all duration-200 flex items-center justify-center"
            whileHover={{ scale: 1.02 }}
            whileTap={{ scale: 0.98 }}
          >
            <MapPin className="w-4 h-4" />
          </motion.button>
        </div>
      </div>
    </motion.div>
  );
};

const MessageBubble = ({ message, isUser }) => (
  <motion.div
    initial={{ opacity: 0, y: 20, scale: 0.95 }}
    animate={{ opacity: 1, y: 0, scale: 1 }}
    transition={{ duration: 0.3 }}
    className={`flex ${isUser ? 'justify-end' : 'justify-start'} mb-4`}
  >
    <div className={`max-w-[80%] ${isUser ? 'order-2' : 'order-1'} flex ${isUser ? 'flex-row-reverse' : 'flex-row'} items-end gap-3`}>
      {/* User Icon */}
      {isUser && (
        <div className="w-10 h-10 bg-gradient-to-br from-gray-400 to-gray-600 rounded-full flex items-center justify-center text-white font-semibold text-sm">
          U
        </div>
      )}
      
      {/* AI Avatar */}
      {!isUser && (
        <div className="flex-shrink-0">
          <Avatar />
        </div>
      )}
      
      <div className="flex flex-col">
        {/* Name label */}
        {!isUser && (
          <span className="text-sm text-gray-600 font-medium mb-1 ml-1">Travello.ai</span>
        )}
        
        {/* Message bubble */}
        <div
          className={`p-4 rounded-2xl ${
            isUser
              ? 'bg-gradient-to-r from-green-600 to-orange-600 text-white'
              : 'bg-white/80 backdrop-blur-sm text-gray-800 border border-white/30'
          }`}
        >
          <p className="leading-relaxed">{message.content}</p>
        </div>
      </div>
    </div>
  </motion.div>
);

const Chip = ({ chip, onClick }) => (
  <motion.button
    variants={chipVariants}
    initial="hidden"
    animate="visible"
    onClick={() => onClick(chip)}
    className="bg-white/90 backdrop-blur-sm border border-white/30 text-gray-700 px-4 py-2 rounded-full text-sm font-medium hover:bg-white hover:border-gray-200 transition-all duration-200 whitespace-nowrap shadow-sm"
    whileHover={{ scale: 1.05, y: -2 }}
    whileTap={{ scale: 0.95 }}
  >
    {chip.label}
  </motion.button>
);

const WorldMap = ({ destinations, onDestinationClick }) => (
  <div className="relative w-full h-80 bg-gradient-to-br from-blue-50 to-indigo-100 rounded-2xl overflow-hidden">
    <div className="absolute inset-0 bg-gradient-to-br from-blue-400/20 to-purple-400/20" />
    <div className="absolute inset-0 flex items-center justify-center">
      <div className="text-center">
        <motion.div
          initial={{ scale: 0.5, opacity: 0 }}
          animate={{ scale: 1, opacity: 1 }}
          transition={{ duration: 0.5 }}
          className="w-16 h-16 bg-gradient-to-br from-blue-500 to-purple-600 rounded-full flex items-center justify-center mx-auto mb-4 shadow-xl"
        >
          <MapPin className="w-8 h-8 text-white" />
        </motion.div>
        <h3 className="text-xl font-bold text-gray-800 mb-2">Discover Destinations</h3>
        <p className="text-gray-600">
          Start chatting to see personalized recommendations on the map
        </p>
      </div>
    </div>
    
    {destinations.map((dest, index) => (
      <motion.div
        key={dest.id}
        initial={{ scale: 0, opacity: 0 }}
        animate={{ scale: 1, opacity: 1 }}
        transition={{ delay: index * 0.1, duration: 0.3 }}
        className="absolute cursor-pointer"
        style={{
          left: `${20 + index * 15}%`,
          top: `${30 + (index % 2) * 20}%`
        }}
        onClick={() => onDestinationClick(dest)}
        whileHover={{ scale: 1.2 }}
      >
        <div className="w-8 h-8 bg-red-500 rounded-full border-2 border-white shadow-lg flex items-center justify-center">
          <div className="w-3 h-3 bg-white rounded-full animate-pulse" />
        </div>
      </motion.div>
    ))}
  </div>
);

const DestinationModal = ({ destination, isOpen, onClose }) => {
  const [activeTab, setActiveTab] = useState('overview');
  
  if (!isOpen || !destination) return null;
  
  const tabs = [
    { id: 'overview', label: 'Overview', icon: Eye },
    { id: 'stays', label: 'Stays', icon: Hotel },
    { id: 'restaurants', label: 'Restaurants', icon: Utensils },
    { id: 'activities', label: 'Things to Do', icon: MapPin },
    { id: 'reviews', label: 'Reviews', icon: MessageCircle }
  ];
  
  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      className="fixed inset-0 bg-black/50 backdrop-blur-sm z-[60] flex items-center justify-center p-4"
      onClick={onClose}
    >
      <motion.div
        initial={{ scale: 0.9, opacity: 0 }}
        animate={{ scale: 1, opacity: 1 }}
        exit={{ scale: 0.9, opacity: 0 }}
        className="bg-white rounded-3xl max-w-4xl w-full max-h-[90vh] overflow-hidden shadow-2xl"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header with Hero Image */}
        <div className="relative h-64">
          <img
            src={destination.hero_image}
            alt={destination.name}
            className="w-full h-full object-cover"
          />
          <div className="absolute inset-0 bg-gradient-to-t from-black/60 to-transparent" />
          
          {/* Close Button */}
          <button
            onClick={onClose}
            className="absolute top-4 right-4 w-10 h-10 bg-white/90 backdrop-blur-sm rounded-full flex items-center justify-center hover:bg-white transition-colors duration-200"
          >
            <X className="w-5 h-5 text-gray-700" />
          </button>
          
          {/* Destination Info Overlay */}
          <div className="absolute bottom-6 left-6 right-6 text-white">
            <div className="flex items-center gap-3 mb-3">
              <h1 className="text-3xl font-bold">{destination.name}</h1>
              <div className="bg-green-600 text-white px-3 py-1 rounded-full text-sm font-medium">
                {destination.weather.temp}
              </div>
            </div>
            
            <div className="flex items-center gap-4 mb-3">
              <div className="flex items-center gap-1">
                <MapPin className="w-4 h-4" />
                <span className="text-sm">{destination.country}</span>
                {destination.state && <span className="text-sm">, {destination.state}</span>}
              </div>
              <div className="flex items-center gap-1">
                <Cloud className="w-4 h-4" />
                <span className="text-sm">{destination.weather.condition}</span>
              </div>
            </div>
            
            {/* Category Tags */}
            <div className="flex flex-wrap gap-2">
              {destination.category.map((cat, index) => (
                <span
                  key={index}
                  className="bg-orange-600/80 backdrop-blur-sm text-white px-3 py-1 rounded-full text-xs font-medium"
                >
                  {cat}
                </span>
              ))}
            </div>
          </div>
        </div>
        
        {/* Tab Navigation */}
        <div className="border-b border-gray-200">
          <div className="flex overflow-x-auto">
            {tabs.map((tab) => {
              const Icon = tab.icon;
              return (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id)}
                  className={`flex items-center gap-2 px-6 py-4 text-sm font-medium border-b-2 transition-colors duration-200 whitespace-nowrap ${
                    activeTab === tab.id
                      ? 'border-green-600 text-green-600'
                      : 'border-transparent text-gray-500 hover:text-green-600'
                  }`}
                >
                  <Icon className="w-4 h-4" />
                  {tab.label}
                </button>
              );
            })}
          </div>
        </div>
        
        {/* Tab Content */}
        <div className="p-6 max-h-96 overflow-y-auto">
          {activeTab === 'overview' && (
            <div className="space-y-6">
              <div>
                <p className="text-gray-700 leading-relaxed mb-6">
                  {destination.description}
                </p>
                <div className="bg-green-50 border border-green-200 rounded-xl p-4">
                  <h3 className="font-semibold text-green-800 mb-2">Why Perfect For You</h3>
                  <p className="text-green-700">{destination.why_match}</p>
                </div>
              </div>
              
              <div>
                <h3 className="text-lg font-bold text-gray-800 mb-4 flex items-center gap-2">
                  <Star className="w-5 h-5 text-orange-600" />
                  Top Attractions
                </h3>
                <div className="grid grid-cols-2 gap-4">
                  {destination.highlights.map((highlight, index) => (
                    <div
                      key={index}
                      className="bg-white border border-gray-200 rounded-xl p-4 hover:shadow-md transition-shadow duration-200"
                    >
                      <div className="flex items-center gap-3">
                        <div className="w-10 h-10 bg-gradient-to-br from-green-500 to-orange-600 rounded-lg flex items-center justify-center">
                          <MapPin className="w-5 h-5 text-white" />
                        </div>
                        <div>
                          <h4 className="font-semibold text-gray-800">{highlight}</h4>
                          <p className="text-sm text-gray-600">Must-visit attraction</p>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          )}
          
          {activeTab === 'stays' && (
            <div className="space-y-4">
              <div className="text-center py-12">
                <Hotel className="w-16 h-16 text-green-500 mx-auto mb-4" />
                <h3 className="text-lg font-semibold text-gray-800 mb-2">Accommodation Options</h3>
                <p className="text-gray-600">Discover the best places to stay in {destination.name}</p>
                <button className="mt-4 bg-gradient-to-r from-green-600 to-orange-600 text-white px-6 py-2 rounded-xl hover:from-green-700 hover:to-orange-700 transition-colors duration-200">
                  View Hotels
                </button>
              </div>
            </div>
          )}
          
          {activeTab === 'restaurants' && (
            <div className="space-y-4">
              <div className="text-center py-12">
                <Utensils className="w-16 h-16 text-orange-500 mx-auto mb-4" />
                <h3 className="text-lg font-semibold text-gray-800 mb-2">Local Cuisine</h3>
                <p className="text-gray-600">Experience authentic flavors and local delicacies</p>
                <button className="mt-4 bg-gradient-to-r from-green-600 to-orange-600 text-white px-6 py-2 rounded-xl hover:from-green-700 hover:to-orange-700 transition-colors duration-200">
                  Find Restaurants
                </button>
              </div>
            </div>
          )}
          
          {activeTab === 'activities' && (
            <div className="space-y-4">
              <div className="text-center py-12">
                <MapPin className="w-16 h-16 text-green-500 mx-auto mb-4" />
                <h3 className="text-lg font-semibold text-gray-800 mb-2">Things to Do</h3>
                <p className="text-gray-600">Explore exciting activities and experiences</p>
                <button className="mt-4 bg-gradient-to-r from-green-600 to-orange-600 text-white px-6 py-2 rounded-xl hover:from-green-700 hover:to-orange-700 transition-colors duration-200">
                  Book Activities
                </button>
              </div>
            </div>
          )}
          
          {activeTab === 'reviews' && (
            <div className="space-y-4">
              <div className="text-center py-12">
                <MessageCircle className="w-16 h-16 text-orange-500 mx-auto mb-4" />
                <h3 className="text-lg font-semibold text-gray-800 mb-2">Traveler Reviews</h3>
                <p className="text-gray-600">Read what other travelers say about {destination.name}</p>
                <button className="mt-4 bg-gradient-to-r from-green-600 to-orange-600 text-white px-6 py-2 rounded-xl hover:from-green-700 hover:to-orange-700 transition-colors duration-200">
                  Read Reviews
                </button>
              </div>
            </div>
          )}
        </div>
      </motion.div>
    </motion.div>
  );
};

// Sidebar Component
const Sidebar = ({ isOpen, onClose, chatHistory, onNewChat, onSelectChat }) => (
  <AnimatePresence>
    {isOpen && (
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        exit={{ opacity: 0 }}
        className="fixed inset-0 bg-black/20 backdrop-blur-sm z-[50]"
        onClick={onClose}
      >
        <motion.div
          initial={{ x: -300 }}
          animate={{ x: 0 }}
          exit={{ x: -300 }}
          className="w-80 h-full bg-white/95 backdrop-blur-xl border-r border-white/30 shadow-2xl z-[55]"
          onClick={e => e.stopPropagation()}
        >
          <div className="p-6 border-b border-white/30">
            <div className="flex items-center justify-between">
              <h2 className="text-xl font-bold text-gray-800">Chat History</h2>
              <button
                onClick={onClose}
                className="p-2 hover:bg-gray-100 rounded-lg transition-colors duration-200"
              >
                <X className="w-5 h-5 text-gray-600" />
              </button>
            </div>
          </div>

          <div className="p-4">
            <motion.button
              onClick={onNewChat}
              className="w-full flex items-center gap-3 p-4 bg-gradient-to-r from-blue-600 to-purple-600 text-white rounded-xl hover:from-blue-700 hover:to-purple-700 transition-all duration-200 mb-4"
              whileHover={{ scale: 1.02 }}
              whileTap={{ scale: 0.98 }}
            >
              <Plus className="w-5 h-5" />
              New Travel Chat
            </motion.button>

            <div className="space-y-2">
              {chatHistory.length === 0 ? (
                <div className="text-center py-8 text-gray-500">
                  <MessageCircle className="w-12 h-12 mx-auto mb-3 text-gray-300" />
                  <p>No previous chats</p>
                </div>
              ) : (
                chatHistory.map((chat, index) => (
                  <motion.button
                    key={chat.id}
                    onClick={() => onSelectChat(chat)}
                    className="w-full text-left p-3 hover:bg-gray-50 rounded-lg transition-colors duration-200 border border-gray-100"
                    whileHover={{ scale: 1.01 }}
                  >
                    <div className="font-medium text-gray-800 truncate">
                      {chat.title || 'Travel Planning Chat'}
                    </div>
                    <div className="text-sm text-gray-500 mt-1">
                      {new Date(chat.timestamp).toLocaleDateString()}
                    </div>
                  </motion.button>
                ))
              )}
            </div>
          </div>
        </motion.div>
      </motion.div>
    )}
  </AnimatePresence>
);

// Personalization Questionnaire Modal - FIXED POSITIONING
const PersonalizationModal = ({ isOpen, onClose, onComplete }) => {
  const [currentPage, setCurrentPage] = useState(0);
  const [responses, setResponses] = useState({});

  const questionnaire = [
    {
      id: 'vacation_style',
      title: 'How do you like to vacation?',
      subtitle: 'Is your ideal vacation day an exhilarating adventure or a relaxing break?',
      type: 'single',
      options: [
        { id: 'adventurous', label: 'Adventurous', icon: '🏃' },
        { id: 'relaxing', label: 'Relaxing', icon: '🏖️' },
        { id: 'balanced', label: 'Strike a balance', icon: '⚖️' }
      ]
    },
    {
      id: 'experience_type',
      title: 'Would you rather explore the great outdoors or pursue a cultural experience?',
      type: 'single',
      options: [
        { id: 'nature', label: 'Nature', icon: '⛰️' },
        { id: 'culture', label: 'Culture', icon: '🛖' },
        { id: 'no_preference', label: 'No preference', icon: '🤷' }
      ]
    },
    {
      id: 'attraction_preference',
      title: 'In a new place, do you prefer to visit popular attractions or engage in authentic local experiences?',
      subtitle: 'e.g. Eiffel Tower vs neighborhood tour or market',
      type: 'single',
      options: [
        { id: 'popular', label: 'Popular', icon: '🗽' },
        { id: 'local', label: 'Local', icon: '🏠' },
        { id: 'both', label: 'Like both equally', icon: '🤝' }
      ]
    },
    {
      id: 'accommodation',
      title: 'What\'s your usual accommodation style?',
      subtitle: 'Select any of the following or add your own.',
      type: 'multiple',
      options: [
        { id: 'luxury_hotels', label: 'Luxury Hotels', icon: '🏨' },
        { id: 'boutique_hotels', label: 'Boutique Hotels', icon: '🌟' },
        { id: 'bnb', label: 'Bed & Breakfast', icon: '🏡' },
        { id: 'budget_hotels', label: 'Budget-friendly Hotels', icon: '💰' },
        { id: 'hostels', label: 'Hostels', icon: '🛌' }
      ],
      allowCustom: true
    },
    {
      id: 'interests',
      title: 'What are your interests or favorite things to do while traveling?',
      subtitle: 'Select any of the following or add your own.',
      type: 'multiple',
      options: [
        { id: 'beach', label: 'Beach', icon: '🏖' },
        { id: 'hiking', label: 'Hiking', icon: '🥾' },
        { id: 'museums', label: 'Museums', icon: '🖼' },
        { id: 'nightlife', label: 'Nightlife', icon: '🌃' },
        { id: 'shopping', label: 'Shopping', icon: '🛍️' },
        { id: 'food', label: 'Local Food', icon: '🍽️' }
      ],
      allowCustom: true
    }
  ];

  const currentQuestion = questionnaire[currentPage];
  const [customInput, setCustomInput] = useState('');

  const handleOptionSelect = (optionId) => {
    const questionId = currentQuestion.id;
    
    if (currentQuestion.type === 'single') {
      setResponses(prev => ({ ...prev, [questionId]: [optionId] }));
    } else {
      const currentSelections = responses[questionId] || [];
      
      if (currentSelections.includes(optionId)) {
        setResponses(prev => ({
          ...prev,
          [questionId]: currentSelections.filter(id => id !== optionId)
        }));
      } else {
        setResponses(prev => ({
          ...prev,
          [questionId]: [...currentSelections, optionId]
        }));
      }
    }
  };

  const handleNext = () => {
    if (currentPage < questionnaire.length - 1) {
      setCurrentPage(prev => prev + 1);
    } else {
      onComplete(responses);
    }
  };

  const handlePrevious = () => {
    if (currentPage > 0) {
      setCurrentPage(prev => prev - 1);
    }
  };

  const isCurrentAnswered = () => {
    const questionId = currentQuestion.id;
    const selections = responses[questionId];
    return selections && selections.length > 0;
  };

  return (
    <AnimatePresence>
      {isOpen && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          className="fixed inset-0 bg-black/60 backdrop-blur-md z-[100] flex items-center justify-center p-4"
          onClick={onClose}
        >
          <motion.div
            variants={modalVariants}
            initial="hidden"
            animate="visible"
            exit="exit"
            className="bg-white rounded-3xl max-w-2xl w-full max-h-[85vh] overflow-y-auto shadow-2xl z-[110]"
            onClick={e => e.stopPropagation()}
          >
            {/* Header */}
            <div className="p-6 border-b border-gray-200 bg-gradient-to-r from-blue-50 to-purple-50">
              <div className="flex items-center justify-between">
                <div>
                  <h2 className="text-2xl font-bold text-gray-800">Tell me more about you</h2>
                  <p className="text-gray-600 mt-1">Page {currentPage + 1} of {questionnaire.length}</p>
                </div>
                <button onClick={onClose} className="p-2 hover:bg-white/50 rounded-lg transition-colors duration-200">
                  <X className="w-5 h-5 text-gray-600" />
                </button>
              </div>
              
              {/* Progress Bar */}
              <div className="mt-4 bg-gray-200 rounded-full h-2">
                <div 
                  className="bg-gradient-to-r from-blue-600 to-purple-600 h-2 rounded-full transition-all duration-300"
                  style={{ width: `${((currentPage + 1) / questionnaire.length) * 100}%` }}
                />
              </div>
            </div>

            {/* Question Content */}
            <div className="p-6">
              <div className="mb-6">
                <h3 className="text-xl font-bold text-gray-800 mb-2">{currentQuestion.title}</h3>
                {currentQuestion.subtitle && (
                  <p className="text-gray-600">{currentQuestion.subtitle}</p>
                )}
              </div>

              {/* Options Grid */}
              <div className="grid grid-cols-2 md:grid-cols-3 gap-3 mb-6">
                {currentQuestion.options.map((option) => {
                  const isSelected = (responses[currentQuestion.id] || []).includes(option.id);
                  return (
                    <motion.button
                      key={option.id}
                      onClick={() => handleOptionSelect(option.id)}
                      className={`p-4 rounded-xl border-2 transition-all duration-200 text-left ${
                        isSelected 
                          ? 'border-blue-500 bg-blue-50 text-blue-700' 
                          : 'border-gray-200 hover:border-gray-300 hover:bg-gray-50'
                      }`}
                      whileHover={{ scale: 1.02 }}
                      whileTap={{ scale: 0.98 }}
                    >
                      <div className="text-2xl mb-2">{option.icon}</div>
                      <div className="font-medium text-sm">{option.label}</div>
                    </motion.button>
                  );
                })}
              </div>

              {/* Custom Input */}
              {currentQuestion.allowCustom && (
                <div className="border-t border-gray-200 pt-6">
                  <div className="flex gap-3">
                    <input
                      type="text"
                      value={customInput}
                      onChange={(e) => setCustomInput(e.target.value)}
                      placeholder="Add your own..."
                      className="flex-1 p-3 border border-gray-200 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    />
                    <button
                      onClick={() => {
                        if (customInput.trim()) {
                          handleOptionSelect(`custom_${customInput}`);
                          setCustomInput('');
                        }
                      }}
                      disabled={!customInput.trim()}
                      className="px-6 py-3 bg-blue-600 text-white rounded-xl hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors duration-200"
                    >
                      Add
                    </button>
                  </div>
                </div>
              )}
            </div>

            {/* Footer */}
            <div className="p-6 border-t border-gray-200 bg-gray-50 rounded-b-3xl">
              <div className="flex justify-between items-center">
                <button
                  onClick={handlePrevious}
                  disabled={currentPage === 0}
                  className="px-6 py-3 border border-gray-300 text-gray-700 rounded-xl hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed transition-colors duration-200"
                >
                  Previous
                </button>
                
                <span className="text-sm text-gray-600">
                  {currentPage + 1} of {questionnaire.length}
                </span>
                
                <button
                  onClick={handleNext}
                  disabled={!isCurrentAnswered()}
                  className="px-6 py-3 bg-gradient-to-r from-blue-600 to-purple-600 text-white rounded-xl hover:from-blue-700 hover:to-purple-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors duration-200"
                >
                  {currentPage === questionnaire.length - 1 ? 'Complete' : 'Next'}
                </button>
              </div>
            </div>
          </motion.div>
        </motion.div>
      )}
    </AnimatePresence>
  );
};
const WhereModal = ({ isOpen, onClose, onSelect, currentDestination }) => (
  <AnimatePresence>
    {isOpen && (
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        exit={{ opacity: 0 }}
        className="fixed inset-0 bg-black/50 backdrop-blur-sm z-[80] flex items-center justify-center p-4"
        onClick={onClose}
      >
        <motion.div
          variants={modalVariants}
          initial="hidden"
          animate="visible"
          exit="exit"
          className="bg-white rounded-3xl max-w-md w-full p-6"
          onClick={e => e.stopPropagation()}
        >
          <div className="flex items-center justify-between mb-6">
            <h3 className="text-xl font-bold text-gray-800">Choose Destination</h3>
            <button onClick={onClose} className="p-2 hover:bg-gray-100 rounded-lg">
              <X className="w-5 h-5 text-gray-600" />
            </button>
          </div>
          
          <div className="space-y-3">
            {[
              { name: 'Manali, Himachal Pradesh', value: 'Manali, Himachal Pradesh' },
              { name: 'Rishikesh, Uttarakhand', value: 'Rishikesh, Uttarakhand' },
              { name: 'Andaman Islands', value: 'Andaman Islands' },
              { name: 'Pondicherry, Tamil Nadu', value: 'Pondicherry, Tamil Nadu' },
              { name: 'Kerala Backwaters', value: 'Kerala Backwaters' },
              { name: 'Rajasthan Desert', value: 'Rajasthan Desert' },
              { name: 'Custom Destination', value: 'Custom Destination' }
            ].map((destination) => (
              <button
                key={destination.value}
                onClick={() => {
                  onSelect(destination.value);
                  onClose();
                }}
                className={`w-full text-left p-4 rounded-xl border-2 transition-all duration-200 hover:shadow-md ${
                  currentDestination === destination.value
                    ? 'border-green-600 bg-green-50 text-green-700'
                    : 'border-gray-200 hover:border-green-300 bg-white hover:bg-green-50'
                }`}
              >
                <div className="flex items-center gap-3">
                  <MapPin className={`w-5 h-5 ${
                    currentDestination === destination.value ? 'text-green-600' : 'text-gray-400'
                  }`} />
                  <span className="font-medium">{destination.name}</span>
                </div>
              </button>
            ))}
          </div>
        </motion.div>
      </motion.div>
    )}
  </AnimatePresence>
);

const WhenModal = ({ isOpen, onClose, onSelect, currentDates }) => (
  <AnimatePresence>
    {isOpen && (
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        exit={{ opacity: 0 }}
        className="fixed inset-0 bg-black/50 backdrop-blur-sm z-[80] flex items-center justify-center p-4"
        onClick={onClose}
      >
        <motion.div
          variants={modalVariants}
          initial="hidden"
          animate="visible"
          exit="exit"
          className="bg-white rounded-3xl max-w-md w-full p-6"
          onClick={e => e.stopPropagation()}
        >
          <div className="flex items-center justify-between mb-6">
            <h3 className="text-xl font-bold text-gray-800">Select Dates</h3>
            <button onClick={onClose} className="p-2 hover:bg-gray-100 rounded-lg">
              <X className="w-5 h-5 text-gray-600" />
            </button>
          </div>
          
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Check-in</label>
              <input 
                type="date" 
                className="w-full p-3 border border-gray-200 rounded-xl focus:ring-2 focus:ring-green-500 focus:border-transparent"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Check-out</label>
              <input 
                type="date" 
                className="w-full p-3 border border-gray-200 rounded-xl focus:ring-2 focus:ring-green-500 focus:border-transparent"
              />
            </div>
            
            <div className="flex gap-2 mt-4">
              {['This Weekend', 'Next Week', 'Flexible'].map((option) => (
                <button
                  key={option}
                  onClick={() => onSelect(option)}
                  className="px-4 py-2 bg-green-100 text-green-700 rounded-lg text-sm hover:bg-green-200 transition-colors duration-200"
                >
                  {option}
                </button>
              ))}
            </div>
          </div>
          
          <button 
            onClick={() => onSelect('Selected dates')}
            className="w-full mt-6 bg-gradient-to-r from-green-600 to-orange-600 text-white font-semibold py-3 rounded-xl hover:from-green-700 hover:to-orange-700"
          >
            Confirm Dates
          </button>
        </motion.div>
      </motion.div>
    )}
  </AnimatePresence>
);

const TravelersModal = ({ isOpen, onClose, onSelect, currentTravelers }) => {
  const [adults, setAdults] = useState(1);
  const [children, setChildren] = useState(0);
  const [infants, setInfants] = useState(0);
  const [pets, setPets] = useState(0);

  return (
    <AnimatePresence>
      {isOpen && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          className="fixed inset-0 bg-black/50 backdrop-blur-sm z-[80] flex items-center justify-center p-4"
          onClick={onClose}
        >
          <motion.div
            variants={modalVariants}
            initial="hidden"
            animate="visible"
            exit="exit"
            className="bg-white rounded-3xl max-w-md w-full p-6"
            onClick={e => e.stopPropagation()}
          >
            <div className="flex items-center justify-between mb-6">
              <h3 className="text-xl font-bold text-gray-800">Travelers</h3>
              <button onClick={onClose} className="p-2 hover:bg-gray-100 rounded-lg">
                <X className="w-5 h-5 text-gray-600" />
              </button>
            </div>
            
            <div className="space-y-4">
              {[
                { label: 'Adults', value: adults, setter: setAdults, desc: 'Ages 13+' },
                { label: 'Children', value: children, setter: setChildren, desc: 'Ages 2-12' },
                { label: 'Infants', value: infants, setter: setInfants, desc: 'Under 2' },
                { label: 'Pets', value: pets, setter: setPets, desc: 'Bringing a pet?' }
              ].map((item) => (
                <div key={item.label} className="flex items-center justify-between p-3 border border-gray-200 rounded-xl">
                  <div>
                    <div className="font-medium text-gray-800">{item.label}</div>
                    <div className="text-sm text-gray-600">{item.desc}</div>
                  </div>
                  <div className="flex items-center gap-3">
                    <button
                      onClick={() => item.setter(Math.max(0, item.value - 1))}
                      className="w-8 h-8 rounded-full border border-gray-300 flex items-center justify-center hover:bg-gray-50"
                    >
                      -
                    </button>
                    <span className="w-8 text-center font-medium">{item.value}</span>
                    <button
                      onClick={() => item.setter(item.value + 1)}
                      className="w-8 h-8 rounded-full border border-gray-300 flex items-center justify-center hover:bg-gray-50"
                    >
                      +
                    </button>
                  </div>
                </div>
              ))}
            </div>
            
            <button 
              onClick={() => onSelect(`${adults + children + infants} travelers`)}
              className="w-full mt-6 bg-gradient-to-r from-green-600 to-orange-600 text-white font-semibold py-3 rounded-xl hover:from-green-700 hover:to-orange-700"
            >
              Confirm Travelers
            </button>
          </motion.div>
        </motion.div>
      )}
    </AnimatePresence>
  );
};

const BudgetModal = ({ isOpen, onClose, onSelect, currentBudget }) => (
  <AnimatePresence>
    {isOpen && (
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        exit={{ opacity: 0 }}
        className="fixed inset-0 bg-black/50 backdrop-blur-sm z-[80] flex items-center justify-center p-4"
        onClick={onClose}
      >
        <motion.div
          variants={modalVariants}
          initial="hidden"
          animate="visible"
          exit="exit"
          className="bg-white rounded-3xl max-w-md w-full p-6"
          onClick={e => e.stopPropagation()}
        >
          <div className="flex items-center justify-between mb-6">
            <h3 className="text-xl font-bold text-gray-800">Set Budget</h3>
            <button onClick={onClose} className="p-2 hover:bg-gray-100 rounded-lg">
              <X className="w-5 h-5 text-gray-600" />
            </button>
          </div>
          
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Total Budget (USD)</label>
              <div className="relative">
                <DollarSign className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-gray-400" />
                <input 
                  type="number" 
                  placeholder="5000"
                  className="w-full pl-10 pr-4 py-3 border border-gray-200 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                />
              </div>
            </div>
            
            <div className="grid grid-cols-2 gap-3">
              {['$1,000', '$2,500', '$5,000', '$10,000'].map((amount) => (
                <button
                  key={amount}
                  onClick={() => onSelect(amount)}
                  className="p-3 border border-gray-200 rounded-xl hover:border-blue-300 hover:bg-blue-50 transition-colors duration-200 text-center font-medium"
                >
                  {amount}
                </button>
              ))}
            </div>
          </div>
          
          <button 
            onClick={() => onSelect('Budget set')}
            className="w-full mt-6 bg-gradient-to-r from-green-600 to-orange-600 text-white font-semibold py-3 rounded-xl hover:from-green-700 hover:to-orange-700"
          >
            Set Budget
          </button>
        </motion.div>
      </motion.div>
    )}
  </AnimatePresence>
);

// Upload Options Popup
const UploadPopup = ({ isOpen, onClose, onFileUpload, onLinkSubmit }) => (
  <AnimatePresence>
    {isOpen && (
      <motion.div
        initial={{ opacity: 0, scale: 0.9, y: 20 }}
        animate={{ opacity: 1, scale: 1, y: 0 }}
        exit={{ opacity: 0, scale: 0.9, y: 20 }}
        className="absolute bottom-16 left-0 bg-white/95 backdrop-blur-xl border border-white/30 rounded-2xl shadow-2xl p-4 min-w-80 z-50"
      >
        <div className="space-y-3">
          <div className="flex items-center gap-3 p-3 hover:bg-gray-50 rounded-xl cursor-pointer transition-colors duration-200">
            <Upload className="w-5 h-5 text-blue-600" />
            <div className="flex-1">
              <h4 className="font-medium text-gray-800 text-sm">Upload a file</h4>
              <p className="text-xs text-gray-600">Start your journey with a travel-related photo, screenshot or PDF.</p>
            </div>
            <input
              type="file"
              accept=".pdf,.jpg,.jpeg,.png,.gif"
              onChange={onFileUpload}
              className="hidden"
              id="file-upload-popup"
            />
            <label
              htmlFor="file-upload-popup"
              className="px-3 py-1 bg-blue-100 text-blue-700 rounded-lg text-xs font-medium cursor-pointer hover:bg-blue-200 transition-colors duration-200"
            >
              Browse
            </label>
          </div>
          
          <div className="flex items-center gap-3 p-3 hover:bg-gray-50 rounded-xl cursor-pointer transition-colors duration-200">
            <Link className="w-5 h-5 text-green-600" />
            <div className="flex-1">
              <h4 className="font-medium text-gray-800 text-sm">Add a link</h4>
              <p className="text-xs text-gray-600">Convert videos, social posts and articles into trip plans.</p>
            </div>
            <button
              onClick={() => {
                const link = prompt('Enter a link to process:');
                if (link) onLinkSubmit(link);
                onClose();
              }}
              className="px-3 py-1 bg-green-100 text-green-700 rounded-lg text-xs font-medium hover:bg-green-200 transition-colors duration-200"
            >
              Add Link
            </button>
          </div>
        </div>
      </motion.div>
    )}
  </AnimatePresence>
);

// Interactive Map Component with scrollable real map
const InteractiveMap = ({ destinations, onMarkerClick, highlightedDestinations = [] }) => {
  const [zoom, setZoom] = useState(1);
  const [panPosition, setPanPosition] = useState({ x: 0, y: 0 });
  const [isDragging, setIsDragging] = useState(false);
  const [dragStart, setDragStart] = useState({ x: 0, y: 0 });

  const handleMouseDown = (e) => {
    setIsDragging(true);
    setDragStart({ x: e.clientX - panPosition.x, y: e.clientY - panPosition.y });
  };

  const handleMouseMove = (e) => {
    if (!isDragging) return;
    setPanPosition({
      x: e.clientX - dragStart.x,
      y: e.clientY - dragStart.y
    });
  };

  const handleMouseUp = () => {
    setIsDragging(false);
  };

  const handleZoomIn = () => {
    setZoom(prev => Math.min(prev + 0.2, 2));
  };

  const handleZoomOut = () => {
    setZoom(prev => Math.max(prev - 0.2, 0.5));
  };

  return (
    <div className="relative w-full h-full bg-gradient-to-br from-blue-50 to-indigo-100 rounded-2xl overflow-hidden cursor-grab"
         onMouseDown={handleMouseDown}
         onMouseMove={handleMouseMove}
         onMouseUp={handleMouseUp}
         onMouseLeave={handleMouseUp}
    >
      <div 
        className="absolute inset-0 transition-transform duration-200"
        style={{
          transform: `translate(${panPosition.x}px, ${panPosition.y}px) scale(${zoom})`,
          transformOrigin: 'center'
        }}
      >
        {/* More realistic world map */}
        <div className="absolute inset-0 bg-gradient-to-br from-blue-400/20 to-purple-400/20" />
        
        {/* World Map Background - More detailed */}
        <svg className="w-full h-full" viewBox="0 0 1000 500">
          {/* North America */}
          <path d="M50 100 Q80 80 120 100 L180 120 Q200 140 180 160 L160 180 Q140 200 100 180 L80 160 Q60 140 50 120 Z" fill="#34d399" opacity="0.7" />
          {/* South America */}
          <path d="M120 220 Q140 200 160 220 L180 260 Q170 300 150 320 L130 340 Q110 320 120 280 Z" fill="#34d399" opacity="0.7" />
          {/* Europe */}
          <path d="M380 80 Q420 70 460 80 L480 100 Q470 120 450 130 L430 140 Q410 130 390 120 L380 100 Z" fill="#34d399" opacity="0.7" />
          {/* Africa */}
          <path d="M380 160 Q420 150 460 160 L480 200 Q470 260 450 300 L430 320 Q410 300 390 260 L380 200 Z" fill="#34d399" opacity="0.7" />
          {/* Asia */}
          <path d="M520 60 Q600 50 680 60 L720 80 Q700 120 680 140 L660 160 Q640 140 620 120 L600 100 Q580 80 560 80 L540 80 Q520 80 520 80 Z" fill="#34d399" opacity="0.7" />
          {/* Australia */}
          <path d="M680 320 Q720 310 760 320 L780 340 Q770 360 750 370 L730 380 Q710 370 690 360 L680 340 Z" fill="#34d399" opacity="0.7" />
          
          {/* Ocean details */}
          <circle cx="200" cy="200" r="5" fill="#3b82f6" opacity="0.3" />
          <circle cx="600" cy="250" r="8" fill="#3b82f6" opacity="0.3" />
          <circle cx="800" cy="180" r="6" fill="#3b82f6" opacity="0.3" />
        </svg>
        
        {/* Destination Markers with accurate positions */}
        {destinations && destinations.length > 0 && destinations.map((dest, index) => {
          // More accurate geographic positions for Indian destinations
          const positions = {
            'manali_himachal': { left: '70%', top: '28%' },       // Manali in Himachal Pradesh  
            'rishikesh_uttarakhand': { left: '72%', top: '30%' }, // Rishikesh in Uttarakhand
            'andaman_islands': { left: '82%', top: '58%' },       // Andaman Islands in Bay of Bengal
            'pondicherry_tamil_nadu': { left: '74%', top: '52%' }, // Pondicherry in Tamil Nadu
            'kerala_backwaters': { left: '68%', top: '55%' },     // Kerala backwaters
            'rajasthan_desert': { left: '69%', top: '35%' }       // Rajasthan in northwest India
          };
          
          const position = positions[dest.id] || { left: `${20 + index * 15}%`, top: `${30 + (index % 2) * 20}%` };
          const isHighlighted = highlightedDestinations.includes(dest.id);
          
          return (
            <motion.div
              key={dest.id}
              initial={{ scale: 0, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              transition={{ delay: index * 0.1, duration: 0.3 }}
              className={`absolute cursor-pointer ${isHighlighted ? 'z-30' : 'z-20'}`}
              style={position}
              onClick={(e) => {
                e.stopPropagation();
                onMarkerClick(dest);
              }}
              whileHover={{ scale: 1.3 }}
            >
              {/* Marker Pin */}
              <div className={`w-10 h-10 rounded-full border-3 border-white shadow-lg flex items-center justify-center ${
                isHighlighted 
                  ? 'bg-blue-600 animate-pulse shadow-blue-400/50' 
                  : 'bg-red-500 hover:bg-red-600'
              }`}>
                <div className="w-4 h-4 bg-white rounded-full" />
              </div>
              
              {/* Location Name Label */}
              <motion.div 
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                className={`absolute -bottom-8 left-1/2 transform -translate-x-1/2 px-2 py-1 rounded-md text-xs whitespace-nowrap font-medium shadow-sm ${
                  isHighlighted
                    ? 'bg-blue-600 text-white'
                    : 'bg-white text-gray-700 border border-gray-200'
                }`}
              >
                {dest.name}
              </motion.div>
              
              {/* Pulse animation for highlighted destinations */}
              {isHighlighted && (
                <div className="absolute inset-0 w-10 h-10 rounded-full bg-blue-400 animate-ping opacity-20" />
              )}
            </motion.div>
          );
        })}
      </div>
      
      {/* Default message when no destinations */}
      {(!destinations || destinations.length === 0) && (
        <div className="absolute inset-0 flex items-center justify-center pointer-events-none">
          <div className="text-center">
            <motion.div
              initial={{ scale: 0.5, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              transition={{ duration: 0.5 }}
              className="w-16 h-16 bg-gradient-to-br from-green-500 to-orange-600 rounded-full flex items-center justify-center mx-auto mb-4 shadow-xl"
            >
              <MapPin className="w-8 h-8 text-white" />
            </motion.div>
            <h3 className="text-xl font-bold text-gray-800 mb-2">Discover Destinations</h3>
            <p className="text-gray-600">
              Start chatting to see personalized recommendations on the map
            </p>
          </div>
        </div>
      )}
      
      {/* Map Controls */}
      <div className="absolute top-4 right-4 flex flex-col gap-2 z-40">
        <button 
          onClick={handleZoomIn}
          className="w-10 h-10 bg-white/90 backdrop-blur-sm rounded-lg shadow-md flex items-center justify-center hover:bg-white transition-colors duration-200 text-gray-700 font-semibold"
        >
          +
        </button>
        <button 
          onClick={handleZoomOut}
          className="w-10 h-10 bg-white/90 backdrop-blur-sm rounded-lg shadow-md flex items-center justify-center hover:bg-white transition-colors duration-200 text-gray-700 font-semibold"
        >
          -
        </button>
      </div>
      
      {/* Pan instructions */}
      <div className="absolute bottom-4 left-4 bg-white/80 backdrop-blur-sm rounded-lg px-3 py-2 text-xs text-gray-600">
        Drag to pan • Use +/- to zoom
      </div>
    </div>
  );
};

// Destination Exploration View
const DestinationExplorationView = ({ destination, onClose, onMapMarkerClick }) => (
  <motion.div
    initial={{ opacity: 0 }}
    animate={{ opacity: 1 }}
    exit={{ opacity: 0 }}
    className="fixed inset-0 bg-gray-50 z-50"
  >
    <div className="h-full flex">
      {/* Left Panel - Destination Summary */}
      <div className="w-1/2 bg-white border-r border-gray-200 overflow-y-auto">
        <div className="p-6">
          <div className="flex items-center justify-between mb-6">
            <button
              onClick={onClose}
              className="flex items-center gap-2 text-gray-600 hover:text-gray-800 transition-colors duration-200"
            >
              <X className="w-5 h-5" />
              Back to Chat
            </button>
          </div>
          
          {/* Destination Hero */}
          <div className="relative h-64 rounded-2xl overflow-hidden mb-6">
            <img
              src={destination.hero_image}
              alt={destination.name}
              className="w-full h-full object-cover"
            />
            <div className="absolute inset-0 bg-gradient-to-t from-black/50 to-transparent" />
            <div className="absolute bottom-4 left-4 text-white">
              <h1 className="text-3xl font-bold mb-2">{destination.name}, {destination.country}</h1>
              <div className="flex items-center gap-4 text-sm">
                <span>{destination.weather.temp}</span>
                <span>•</span>
                <span>{destination.weather.condition}</span>
              </div>
            </div>
          </div>
          
          {/* Quick Facts */}
          <div className="mb-6">
            <h3 className="text-xl font-bold text-gray-800 mb-4">Quick Facts</h3>
            <div className="grid grid-cols-2 gap-4">
              <div className="bg-blue-50 p-4 rounded-xl">
                <div className="text-blue-600 font-semibold text-sm">Best Time</div>
                <div className="text-gray-700 font-medium">Mar - May</div>
              </div>
              <div className="bg-green-50 p-4 rounded-xl">
                <div className="text-green-600 font-semibold text-sm">Currency</div>
                <div className="text-gray-700 font-medium">USD</div>
              </div>
              <div className="bg-purple-50 p-4 rounded-xl">
                <div className="text-purple-600 font-semibold text-sm">Language</div>
                <div className="text-gray-700 font-medium">English</div>
              </div>
              <div className="bg-orange-50 p-4 rounded-xl">
                <div className="text-orange-600 font-semibold text-sm">Time Zone</div>
                <div className="text-gray-700 font-medium">GMT-5</div>
              </div>
            </div>
          </div>
          
          {/* Let's Plan Your Trip */}
          <div className="mb-6">
            <h3 className="text-xl font-bold text-gray-800 mb-4">Let's Plan Your Trip</h3>
            <div className="space-y-3">
              {[
                "What's your travel style?",
                "How many days are you planning?",
                "What's your budget range?",
                "Any specific interests?"
              ].map((question, index) => (
                <button
                  key={index}
                  className="w-full text-left p-4 bg-gray-50 hover:bg-gray-100 rounded-xl transition-colors duration-200 border border-gray-200 text-gray-700 font-medium"
                >
                  {question}
                </button>
              ))}
            </div>
          </div>
        </div>
        
        {/* Quick Ask Bar - Sticky at bottom */}
        <div className="sticky bottom-0 bg-white border-t border-gray-200 p-4">
          <div className="flex gap-3">
            <input
              type="text"
              placeholder={`Ask about this destination...`}
              className="flex-1 p-3 border border-gray-200 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            />
            <button className="p-3 bg-blue-600 text-white rounded-xl hover:bg-blue-700 transition-colors duration-200">
              <Send className="w-5 h-5" />
            </button>
          </div>
        </div>
      </div>
      
      {/* Right Panel - Interactive Map */}
      <div className="w-1/2 bg-gray-100 p-6">
        <div className="h-full">
          <h3 className="text-xl font-bold text-gray-800 mb-4">Explore {destination.name}</h3>
          <InteractiveMap
            destinations={[destination]}
            onMarkerClick={onMapMarkerClick}
            highlightedDestinations={[destination.id]}
          />
        </div>
      </div>
    </div>
  </motion.div>
);
// Trip Planning Bar Component - FIXED POSITIONING
const TripPlanningBar = ({ tripDetails, onUpdateTrip, isVisible, onApplyFilters }) => {
  const [showWhereModal, setShowWhereModal] = useState(false);
  const [showWhenModal, setShowWhenModal] = useState(false);
  const [showTravelersModal, setShowTravelersModal] = useState(false);
  const [showBudgetModal, setShowBudgetModal] = useState(false);

  if (!isVisible) return null;

  const hasAllDetails = tripDetails.destination && tripDetails.dates && tripDetails.travelers && tripDetails.budget;

  return (
    <>
      {/* Trip Planning Bar - Fixed positioning */}
      <motion.div
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        className="bg-white/95 backdrop-blur-sm border border-white/30 rounded-xl p-4 mb-4 shadow-lg mx-6 relative z-20"
      >
        <div className="flex items-center gap-4 flex-wrap">
          <div className="flex items-center gap-2">
            <MapPin className="w-5 h-5 text-green-600" />
            <button 
              onClick={() => setShowWhereModal(true)}
              className="text-sm font-medium text-gray-700 hover:text-green-600 transition-colors duration-200"
            >
              {tripDetails.destination || 'Choose destination'}
            </button>
          </div>
          
          <div className="flex items-center gap-2">
            <Calendar className="w-5 h-5 text-orange-600" />
            <button 
              onClick={() => setShowWhenModal(true)}
              className="text-sm font-medium text-gray-700 hover:text-green-600 transition-colors duration-200"
            >
              {tripDetails.dates || 'Select dates'}
            </button>
          </div>
          
          <div className="flex items-center gap-2">
            <Users className="w-5 h-5 text-green-600" />
            <button 
              onClick={() => setShowTravelersModal(true)}
              className="text-sm font-medium text-gray-700 hover:text-green-600 transition-colors duration-200"
            >
              {tripDetails.travelers || '1 traveler'}
            </button>
          </div>
          
          <div className="flex items-center gap-2">
            <DollarSign className="w-5 h-5 text-orange-600" />
            <button 
              onClick={() => setShowBudgetModal(true)}
              className="text-sm font-medium text-gray-700 hover:text-orange-600 transition-colors duration-200"
            >
              {tripDetails.budget || 'Set budget'}
            </button>
          </div>
          
          <div className="ml-auto flex items-center gap-2">
            <button className="p-2 hover:bg-gray-100 rounded-lg transition-colors duration-200">
              <Edit3 className="w-4 h-4 text-gray-500" />
            </button>
            
            {hasAllDetails && (
              <motion.button
                onClick={onApplyFilters}
                className="px-4 py-2 bg-gradient-to-r from-green-600 to-orange-600 text-white rounded-lg hover:from-green-700 hover:to-orange-700 transition-colors duration-200 text-sm font-medium"
                whileHover={{ scale: 1.05 }}
                whileTap={{ scale: 0.95 }}
              >
                Apply
              </motion.button>
            )}
          </div>
        </div>
      </motion.div>

      {/* Modals - Proper z-index to avoid overlap */}
      <AnimatePresence>
        <WhereModal
          isOpen={showWhereModal}
          onClose={() => setShowWhereModal(false)}
          currentDestination={tripDetails.destination}
          onSelect={(dest) => {
            onUpdateTrip({ ...tripDetails, destination: dest });
            setShowWhereModal(false);
          }}
        />
        
        <WhenModal
          isOpen={showWhenModal}
          onClose={() => setShowWhenModal(false)}
          currentDates={tripDetails.dates}
          onSelect={(dates) => {
            onUpdateTrip({ ...tripDetails, dates });
            setShowWhenModal(false);
          }}
        />
        
        <TravelersModal
          isOpen={showTravelersModal}
          onClose={() => setShowTravelersModal(false)}
          currentTravelers={tripDetails.travelers}
          onSelect={(travelers) => {
            onUpdateTrip({ ...tripDetails, travelers });
            setShowTravelersModal(false);
          }}
        />
        
        <BudgetModal
          isOpen={showBudgetModal}
          onClose={() => setShowBudgetModal(false)}
          currentBudget={tripDetails.budget}
          onSelect={(budget) => {
            onUpdateTrip({ ...tripDetails, budget });
            setShowBudgetModal(false);
          }}
        />
      </AnimatePresence>
    </>
  );
};
function App() {
  const [messages, setMessages] = useState([
    {
      id: '1',
      role: 'assistant',
      content: 'Where to today?'
    }
  ]);
  const [inputMessage, setInputMessage] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [recommendations, setRecommendations] = useState([]);
  const [currentChips, setCurrentChips] = useState([]);
  const [userProfile, setUserProfile] = useState({});
  const [sessionId] = useState(() => `session_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`);
  const [selectedDestination, setSelectedDestination] = useState(null);
  const [isDestinationModalOpen, setIsDestinationModalOpen] = useState(false);
  const [destinations] = useState([
    {
      id: "manali_himachal",
      name: "Manali",
      country: "India", 
      state: "Himachal Pradesh",
      coordinates: {"lat": 32.2396, "lng": 77.1887},
      hero_image: "https://images.unsplash.com/photo-1464822759844-d150baec0494?w=800&h=400&fit=crop",
      category: ["Adventure", "Mountains", "Paragliding", "River Rafting"],
      weather: {"temp": "18°C", "condition": "Pleasant"},  
      description: "Adventure hub of Himachal Pradesh offering paragliding, river rafting, trekking, and stunning Himalayan views.",
      highlights: ["Solang Valley Paragliding", "Beas River Rafting", "Rohtang Pass", "Snow Activities"],
      why_match: "Perfect for adventure sports enthusiasts"
    },
    {
      id: "rishikesh_uttarakhand",
      name: "Rishikesh",
      country: "India",
      state: "Uttarakhand", 
      coordinates: {"lat": 30.0869, "lng": 78.2676},
      hero_image: "https://images.unsplash.com/photo-1544551763-46a013bb70d5?w=800&h=400&fit=crop",
      category: ["Adventure", "Spiritual", "River Rafting", "Bungee Jumping"],
      weather: {"temp": "25°C", "condition": "Sunny"},
      description: "Yoga capital and adventure hub offering world-class river rafting, bungee jumping, and spiritual experiences.",
      highlights: ["White Water Rafting", "Bungee Jumping", "Lakshman Jhula", "Yoga Ashrams"],
      why_match: "Ultimate destination for adventure and spirituality"
    },
    {
      id: "andaman_islands",
      name: "Andaman Islands", 
      country: "India",
      state: "Andaman & Nicobar",
      coordinates: {"lat": 11.7401, "lng": 92.6586},
      hero_image: "https://images.unsplash.com/photo-1544551763-77ef2d0cfc6c?w=800&h=400&fit=crop",
      category: ["Beach", "Scuba Diving", "Marine Life", "Water Sports"],
      weather: {"temp": "30°C", "condition": "Tropical"},
      description: "Pristine tropical islands with crystal clear waters, coral reefs, and world-class scuba diving.",
      highlights: ["Scuba Diving", "Snorkeling", "Radhanagar Beach", "Neil Island"],
      why_match: "Paradise for marine life and beach lovers"
    },
    {
      id: "pondicherry_tamil_nadu",
      name: "Pondicherry",
      country: "India",
      state: "Tamil Nadu",
      coordinates: {"lat": 11.9416, "lng": 79.8083},
      hero_image: "https://images.unsplash.com/photo-1582510003544-4d00b7f74220?w=800&h=400&fit=crop",
      category: ["Beach", "Scuba Diving", "French Culture", "Water Sports"],
      weather: {"temp": "29°C", "condition": "Sunny"},
      description: "French colonial charm meets adventure with scuba diving, surfing, and cultural experiences.",
      highlights: ["Scuba Diving", "French Quarter", "Auroville", "Paradise Beach"],
      why_match: "Unique blend of culture and water sports"
    },
    {
      id: "kerala_backwaters",
      name: "Kerala",
      country: "India",
      state: "Kerala",
      coordinates: {"lat": 10.8505, "lng": 76.2711},
      hero_image: "https://images.unsplash.com/photo-1602216056096-3b40cc0c9944?w=800&h=400&fit=crop",
      category: ["Backwaters", "Houseboat", "Nature", "Cultural"],
      weather: {"temp": "28°C", "condition": "Humid"},
      description: "God's own country with serene backwaters, houseboat cruises, spice plantations, and Ayurvedic treatments.",
      highlights: ["Alleppey Houseboat", "Munnar Tea Gardens", "Thekkady Wildlife", "Kochi Heritage"],
      why_match: "Perfect for nature lovers and cultural enthusiasts"
    },
    {
      id: "rajasthan_desert",
      name: "Rajasthan",
      country: "India",
      state: "Rajasthan", 
      coordinates: {"lat": 27.0238, "lng": 74.2179},
      hero_image: "https://images.unsplash.com/photo-1477587458883-47145ed94245?w=800&h=400&fit=crop",
      category: ["Desert Safari", "Heritage", "Culture", "Palaces"],
      weather: {"temp": "32°C", "condition": "Sunny"},
      description: "Land of maharajas with majestic palaces, desert safaris, camel rides, and royal heritage.",
      highlights: ["Jaisalmer Desert Safari", "Udaipur Palaces", "Jaipur Pink City", "Camel Safari"],
      why_match: "Ultimate destination for heritage and desert adventure"
    }
  ]);
  const [isSidebarOpen, setIsSidebarOpen] = useState(false);
  const [chatHistory, setChatHistory] = useState([]);
  const [tripDetails, setTripDetails] = useState({});
  const [showTripBar, setShowTripBar] = useState(false);
  const [isRecording, setIsRecording] = useState(false);
  const [showUploadPopup, setShowUploadPopup] = useState(false);
  const [showDestinationExploration, setShowDestinationExploration] = useState(false);
  const [exploringDestination, setExploringDestination] = useState(null);
  const [showPersonalizationModal, setShowPersonalizationModal] = useState(false);
  const [highlightedDestinations, setHighlightedDestinations] = useState([]);
  const [showGeneratedContent, setShowGeneratedContent] = useState(false);
  const [generatedItinerary, setGeneratedItinerary] = useState([]);
  const [generatedAccommodations, setGeneratedAccommodations] = useState([]);
  const [rightPanelContent, setRightPanelContent] = useState('default'); // 'default', 'destination', 'itinerary', 'tour', 'activity'
  const [selectedMapDestination, setSelectedMapDestination] = useState(null);
  const [selectedTour, setSelectedTour] = useState(null);
  const [selectedActivity, setSelectedActivity] = useState(null);
  
  const messagesEndRef = useRef(null);
  const inputRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, recommendations]);

  const handleSendMessage = async () => {
    if (!inputMessage.trim() || isLoading) return;

    console.log('🚀 Sending message:', inputMessage);

    const messageId = `user_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
    const userMessage = {
      id: messageId,
      role: 'user',
      content: inputMessage
    };

    setMessages(prev => {
      // Check if message already exists to prevent duplicates
      if (prev.some(msg => msg.id === messageId)) {
        console.log('Message already exists, skipping duplicate');
        return prev;
      }
      console.log('Adding user message to state');
      return [...prev, userMessage];
    });
    
    const currentInput = inputMessage;
    setInputMessage('');
    setIsLoading(true);

    // Check if user is asking about a specific destination
    const destinationKeywords = ['explore', 'visit', 'go to', 'about', 'tell me about'];
    const mentionedDestination = destinations.find(dest => 
      currentInput.toLowerCase().includes(dest.name.toLowerCase()) ||
      currentInput.toLowerCase().includes(dest.country.toLowerCase())
    );
    
    if (mentionedDestination && destinationKeywords.some(keyword => currentInput.toLowerCase().includes(keyword))) {
      setHighlightedDestinations([mentionedDestination.id]);
      console.log('🎯 Highlighted destination:', mentionedDestination.name);
    }

    // Check if user is expressing interest in planning a trip
    const tripKeywords = ['plan', 'trip', 'travel', 'visit', 'go to', 'vacation', 'holiday'];
    const containsTripKeyword = tripKeywords.some(keyword => currentInput.toLowerCase().includes(keyword));
    
    if (containsTripKeyword) {
      setShowTripBar(true);
      console.log('📋 Trip planning detected, showing trip bar');
    }

    try {
      console.log('📡 Making API call to:', `${API}/chat`);
      
      const response = await axios.post(`${API}/chat`, {
        message: currentInput,
        session_id: sessionId,
        user_profile: userProfile
      });

      console.log('✅ API Response received:', response.data);

      const assistantMessageId = `assistant_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
      const assistantMessage = {
        id: assistantMessageId,
        role: 'assistant',
        content: response.data.chat_text
      };

      setMessages(prev => {
        // Check if message already exists to prevent duplicates
        if (prev.some(msg => msg.id === assistantMessageId)) {
          console.log('Assistant message already exists, skipping duplicate');
          return prev;
        }
        console.log('Adding assistant message to state');
        return [...prev, assistantMessage];
      });

      // Process UI actions
      const newRecommendations = [];
      const newChips = [];

      if (response.data.ui_actions && response.data.ui_actions.length > 0) {
        console.log('🎨 Processing UI actions:', response.data.ui_actions.length);
        
        response.data.ui_actions.forEach(action => {
          if (action.type === 'card_add') {
            // Find the full destination data
            const fullDestination = destinations.find(d => 
              d.name.toLowerCase() === action.payload.title.split(',')[0].toLowerCase()
            );
            
            if (fullDestination) {
              // Use full destination data instead of payload
              const enhancedCard = {
                ...action.payload,
                ...fullDestination,
                title: `${fullDestination.name}, ${fullDestination.country}`
              };
              newRecommendations.push(enhancedCard);
              console.log('📋 Enhanced card added:', enhancedCard.title);
            } else {
              newRecommendations.push(action.payload);
              console.log('📋 Basic card added:', action.payload.title);
            }
          } else if (action.type === 'prompt') {
            newChips.push(...action.payload.chips);
            console.log('🔸 Added chips:', action.payload.chips);
          }
        });
      } else {
        // Fallback: if no UI actions from backend, create recommendations from local data
        if (mentionedDestination) {
          const fallbackCard = {
            id: mentionedDestination.id,
            category: "destination",
            title: `${mentionedDestination.name}, ${mentionedDestination.country}`,
            hero_image: mentionedDestination.hero_image,
            pitch: mentionedDestination.description,
            why_match: mentionedDestination.why_match,
            weather: mentionedDestination.weather,
            highlights: mentionedDestination.highlights,
            coordinates: mentionedDestination.coordinates,
            cta_primary: {"label": "Explore", "action": "explore"},
            cta_secondary: {"label": "View on map", "action": "map"},
            motion: {"enter_ms": 260, "stagger_ms": 80},
            ...mentionedDestination
          };
          
          newRecommendations.push(fallbackCard);
          console.log('🔄 Fallback card created for:', mentionedDestination.name);
          
          newChips.push(
            { label: "🏃 Adventurous", value: "adventure" },
            { label: "🏖 Relaxing", value: "relax" },
            { label: "🏛 Cultural", value: "culture" }
          );
        }
        console.log('⚠️ No UI actions from backend, using fallback');
      }

      if (newRecommendations.length > 0) {
        setRecommendations(prev => {
          console.log('🎴 Adding new recommendations:', newRecommendations.length);
          // Prevent duplicates by checking IDs
          const newRecs = newRecommendations.filter(newRec => 
            !prev.some(existingRec => existingRec.id === newRec.id)
          );
          if (newRecs.length === 0) {
            console.log('All recommendations already exist, skipping duplicates');
            return prev;
          }
          return [...prev, ...newRecs];
        });
      }
      
      if (newChips.length > 0) {
        setCurrentChips(newChips);
        console.log('🔸 Setting chips:', newChips.length);
      }

      setUserProfile(response.data.updated_profile);

    } catch (error) {
      console.error('❌ Chat API error:', error);
      const errorMessage = {
        id: Date.now().toString() + '_error',
        role: 'assistant',
        content: 'I apologize, but I\'m having trouble connecting right now. Please try again in a moment.'
      };
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
      console.log('✅ Message sending complete');
    }
  };

  const handleChipClick = (chip) => {
    const updatedProfile = { ...userProfile, [chip.value]: true };
    setUserProfile(updatedProfile);
    setCurrentChips(prev => prev.filter(c => c.value !== chip.value));
    
    // Send chip selection as a message
    const chipMessage = `I prefer ${chip.label.replace(/[🏃🏖🏛]/g, '').trim()}`;
    setInputMessage(chipMessage);
    setTimeout(() => handleSendMessage(), 100);
  };

  const handleApplyFilters = () => {
    console.log('🎯 Applying filters with trip details:', tripDetails);
    
    // Add helpful message before showing personalization
    const applyMessage = {
      id: Date.now().toString(),
      role: 'assistant',
      content: `Perfect! I have all your trip details for ${tripDetails.destination}. Now let me learn more about your travel preferences to create the perfect personalized itinerary for you.`
    };
    
    setMessages(prev => [...prev, applyMessage]);
    
    // Small delay to show message before opening modal
    setTimeout(() => {
      setShowPersonalizationModal(true);
    }, 1000);
  };

  const handlePersonalizationComplete = (responses) => {
    console.log('Personalization completed:', responses);
    setShowPersonalizationModal(false);
    
    // Generate personalized itinerary and recommendations based on actual destination
    const targetDestination = tripDetails.destination || 'your destination';
    const personalizedItinerary = generateItinerary(tripDetails, responses, targetDestination);
    const personalizedAccommodations = generateAccommodations(tripDetails, responses, targetDestination);
    
    // Add itinerary message to chat
    const itineraryMessage = {
      id: Date.now().toString(),
      role: 'assistant',
      content: `Perfect! Based on your preferences, I've created a personalized ${tripDetails.dates || '5-day'} itinerary for ${targetDestination}. Check the right panel for your customized recommendations and detailed day-by-day plan!`
    };
    
    setMessages(prev => [...prev, itineraryMessage]);
    
    // Set the generated content to state and switch right panel
    setGeneratedItinerary(personalizedItinerary);
    setGeneratedAccommodations(personalizedAccommodations);
    setRightPanelContent('itinerary');
    setShowGeneratedContent(true);
    
    console.log('Generated itinerary:', personalizedItinerary);
    console.log('Generated accommodations:', personalizedAccommodations);
  };

  const generateItinerary = (tripDetails, preferences, destination) => {
    // Get destination-specific data
    const destData = destinations.find(d => 
      d.name.toLowerCase() === destination.toLowerCase() || 
      destination.toLowerCase().includes(d.name.toLowerCase())
    );
    
    const isAdventurous = preferences.vacation_style?.includes('adventurous');
    const lovesNature = preferences.experience_type?.includes('nature');
    const prefersLocal = preferences.attraction_preference?.includes('local');
    const beachLover = preferences.interests?.includes('beach');
    
    const days = [
      {
        day: 1,
        title: "Arrival & First Impressions",
        activities: [
          { time: "9:00 AM", activity: "Airport Transfer & Hotel Check-in", location: "Hotel" },
          { time: "11:00 AM", activity: prefersLocal ? "Local Neighborhood Walk" : (destData?.highlights[0] || "Main Landmark Visit"), location: "City Center" },
          { time: "1:00 PM", activity: preferences.dining?.includes('street_food') ? "Street Food Tour" : "Welcome Lunch", location: "Local Area" },
          { time: "3:00 PM", activity: beachLover && destData?.category.includes('Beach') ? "Beach Exploration" : (destData?.highlights[1] || "Cultural Site Visit"), location: "Main Attraction" },
          { time: "6:00 PM", activity: "Sunset Experience", location: "Scenic Viewpoint" },
          { time: "8:00 PM", activity: "Welcome Dinner", location: "Recommended Restaurant" }
        ]
      },
      {
        day: 2,
        title: isAdventurous ? "Adventure & Exploration" : "Cultural Discovery",
        activities: [
          { time: "8:00 AM", activity: "Breakfast at Hotel", location: "Hotel" },
          { time: "9:30 AM", activity: isAdventurous ? (destData?.highlights[2] || "Adventure Activity") : (destData?.highlights[1] || "Museum Visit"), location: "Activity Site" },
          { time: "12:30 PM", activity: "Local Cuisine Lunch", location: "Authentic Restaurant" },
          { time: "2:00 PM", activity: lovesNature ? "Nature Park/Garden" : "Historical District Tour", location: "Nature/Heritage Area" },
          { time: "4:30 PM", activity: preferences.interests?.includes('shopping') ? "Local Markets" : "Art Gallery/Craft Workshop", location: "Cultural Quarter" },
          { time: "7:00 PM", activity: preferences.interests?.includes('nightlife') ? "Evening Entertainment" : "Traditional Performance", location: "Entertainment District" }
        ]
      },
      {
        day: 3,
        title: "Deeper Exploration",
        activities: [
          { time: "9:00 AM", activity: destData?.highlights[3] || "Hidden Gems Tour", location: "Off the beaten path" },
          { time: "11:30 AM", activity: preferences.interests?.includes('cooking_classes') ? "Cooking Class Experience" : "Local Craft Workshop", location: "Cultural Center" },
          { time: "1:30 PM", activity: "Farm-to-table Lunch", location: "Local Farm/Restaurant" },
          { time: "3:30 PM", activity: beachLover ? "Water Sports/Beach Activities" : "Scenic Drive/Nature Walk", location: "Outdoor Location" },
          { time: "6:00 PM", activity: "Photography Golden Hour", location: "Instagram-worthy Spots" },
          { time: "8:00 PM", activity: "Farewell Dinner", location: "Special Restaurant" }
        ]
      }
    ];
    
    return days;
  };

  const generateAccommodations = (tripDetails, preferences, destination) => {
    // Generate accommodations based on destination and preferences
    const accommodationTypes = preferences.accommodation || ['luxury_hotels'];
    const isLuxury = accommodationTypes.includes('luxury_hotels');
    const isBoutique = accommodationTypes.includes('boutique_hotels');
    const isBudget = accommodationTypes.includes('budget_hotels');
    
    // Get destination-specific imagery
    const destData = destinations.find(d => 
      d.name.toLowerCase() === destination.toLowerCase() || 
      destination.toLowerCase().includes(d.name.toLowerCase())
    );
    
    const accommodations = [
      {
        id: 'hotel_recommended',
        name: isLuxury ? `Grand ${destination} Resort & Spa` : isBoutique ? `Heritage ${destination} Hotel` : `${destination} Comfort Inn`,
        type: isLuxury ? 'Luxury Resort' : isBoutique ? 'Boutique Hotel' : 'Budget Hotel',
        rating: isLuxury ? 4.8 : isBoutique ? 4.5 : 4.2,
        price: isLuxury ? '$300-450' : isBudget ? '$80-120' : '$150-220',
        image: destData?.hero_image || 'https://images.unsplash.com/photo-1564501049412-61c2a3083791?w=400&h=300&fit=crop',
        amenities: isLuxury ? ['Spa', 'Pool', 'Fine Dining', 'Concierge', 'Beach Access'] : 
                   isBoutique ? ['WiFi', 'Restaurant', 'Rooftop Bar', 'Local Experience'] :
                   ['WiFi', 'Breakfast', 'Airport Shuttle'],
        match: '✨ Perfect match for your preferences and budget',
        highlighted: true,
        description: `Located in the heart of ${destination}, this ${isLuxury ? 'luxury' : isBoutique ? 'boutique' : 'comfortable'} accommodation offers the perfect base for your trip.`
      },
      {
        id: 'hotel_alternative',
        name: `${destination} City Hotel`,
        type: 'City Hotel',
        rating: 4.3,
        price: '$180-250',
        image: 'https://images.unsplash.com/photo-1551882547-ff40c63fe5fa?w=400&h=300&fit=crop',
        amenities: ['WiFi', 'Restaurant', 'Gym', 'Business Center'],
        match: 'Great central location alternative',
        highlighted: false,
        description: `Modern hotel in ${destination}'s business district with easy access to major attractions.`
      },
      {
        id: 'hotel_unique',
        name: preferences.accommodation?.includes('bnb') ? `Cozy ${destination} B&B` : `${destination} Eco Lodge`,
        type: preferences.accommodation?.includes('bnb') ? 'Bed & Breakfast' : 'Eco Lodge',
        rating: 4.4,
        price: preferences.accommodation?.includes('bnb') ? '$120-180' : '$160-220',
        image: 'https://images.unsplash.com/photo-1506905925346-21bda4d32df4?w=400&h=300&fit=crop',
        amenities: preferences.accommodation?.includes('bnb') ? ['Homemade Breakfast', 'Local Tips', 'Garden'] : ['Eco-friendly', 'Nature Views', 'Wellness Center'],
        match: 'Unique local experience',
        highlighted: false,
        description: `Experience authentic ${destination} hospitality in this charming local accommodation.`
      }
    ];
    
    return accommodations;
  };

  const handleMapMarkerClick = (destination) => {
    console.log('🗺️ Map marker clicked:', destination.name);
    setSelectedMapDestination(destination);
    setRightPanelContent('destination');
    setHighlightedDestinations([destination.id]);
    
    // Also open detailed modal
    setSelectedDestination(destination);
    setIsDestinationModalOpen(true);
  };

  const handleCardAction = (action, item) => {
    console.log('🎯 Card action:', action, item.title);
    
    switch (action) {
      case 'explore':
        // Don't open modal, just show message and guide user to trip planning
        const exploreMessage = {
          id: Date.now().toString(),
          role: 'assistant',
          content: `Great choice! ${item.title} is perfect for your trip. I can see you're interested in exploring this destination. Let me help you plan your perfect trip!`
        };
        setMessages(prev => [...prev, exploreMessage]);
        
        // Show trip planning bar and pre-fill destination
        setShowTripBar(true);
        setTripDetails(prev => ({ ...prev, destination: item.title }));
        break;
        
      case 'map':
        // Show destination in right panel instead of modal
        setSelectedMapDestination(item);
        setRightPanelContent('destination');
        setHighlightedDestinations([item.id]);
        break;
        
      case 'book':
        const bookingMessage = {
          id: Date.now().toString(),
          role: 'assistant',
          content: `I'd love to help you book ${item.title}! First, let's complete your trip planning details so I can find the perfect accommodations for you.`
        };
        setMessages(prev => [...prev, bookingMessage]);
        setShowTripBar(true);
        break;
        
      default:
        console.log('Unknown action:', action, item);
    }
  };

  const handleVoiceInput = () => {
    if (!('webkitSpeechRecognition' in window) && !('SpeechRecognition' in window)) {
      alert('Speech recognition is not supported in this browser');
      return;
    }

    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    const recognition = new SpeechRecognition();

    recognition.continuous = false;
    recognition.interimResults = false;
    recognition.lang = 'en-US';

    recognition.onstart = () => {
      setIsRecording(true);
    };

    recognition.onend = () => {
      setIsRecording(false);
    };

    recognition.onresult = (event) => {
      const transcript = event.results[0][0].transcript;
      setInputMessage(transcript);
    };

    recognition.onerror = (event) => {
      console.error('Speech recognition error:', event.error);
      setIsRecording(false);
    };

    recognition.start();
  };

  const handleNewChat = () => {
    setMessages([
      {
        id: Date.now().toString(),
        role: 'assistant',
        content: 'Dreaming of a getaway? Tell me your travel wishlist and I\'ll guide you.\nAsk anything about your upcoming travels!'
      }
    ]);
    setRecommendations([]);
    setCurrentChips([]);
    setTripDetails({});
    setShowTripBar(false);
    setIsSidebarOpen(false);
  };

  const handleFileUpload = (event) => {
    const file = event.target.files[0];
    if (file) {
      // Handle file upload logic here
      console.log('File uploaded:', file);
      // You could process the file and add it to the conversation
    }
  };

  const handleLinkSubmit = (link) => {
    if (link.trim()) {
      setInputMessage(`Process this link for travel planning: ${link}`);
      setTimeout(() => handleSendMessage(), 100);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-blue-50 to-indigo-100">
      <div className="flex h-screen">
        {/* Left Panel - Chat */}
        <div className="w-[48%] flex flex-col bg-white/80 backdrop-blur-xl border-r border-white/30 relative z-10">
          {/* Header */}
          <div className="p-6 border-b border-white/30 bg-white/50 backdrop-blur-sm">
            <div className="flex items-center gap-4">
              <button
                onClick={() => setIsSidebarOpen(true)}
                className="p-2 hover:bg-white/50 rounded-lg transition-colors duration-200"
              >
                <Menu className="w-5 h-5 text-gray-600" />
              </button>
              <Avatar />
              <div className="flex-1">
                <h1 className="text-2xl font-bold bg-gradient-to-r from-green-600 to-orange-600 bg-clip-text text-transparent">
                  Travello.ai
                </h1>
                <p className="text-sm text-gray-600">Your AI Travel Companion</p>
              </div>
            </div>
          </div>

          {/* Trip Planning Bar */}
          <TripPlanningBar 
            tripDetails={tripDetails}
            onUpdateTrip={setTripDetails}
            isVisible={showTripBar}
            onApplyFilters={handleApplyFilters}
          />

          {/* Chat Messages */}
          <div className="flex-1 overflow-y-auto p-6 space-y-6">
            <AnimatePresence>
              {messages.map((message) => (
                <div key={message.id}>
                  {message.role === 'assistant' && message.id === '1' ? (
                    // Centered welcome message
                    <motion.div
                      initial={{ opacity: 0, y: 20 }}
                      animate={{ opacity: 1, y: 0 }}
                      transition={{ duration: 0.5 }}
                      className="text-center py-12"
                    >
                      <div className="max-w-md mx-auto">
                        {/* Hero Image */}
                        <div className="relative w-32 h-32 mx-auto mb-6">
                          <div className="w-full h-full rounded-full bg-gradient-to-br from-green-400 via-orange-400 to-red-400 p-1">
                            <div className="w-full h-full rounded-full bg-white flex items-center justify-center overflow-hidden">
                              <img
                                src="https://images.unsplash.com/photo-1469474968028-56623f02e42e?w=200&h=200&fit=crop"
                                alt="Travel destinations"
                                className="w-full h-full object-cover"
                              />
                            </div>
                          </div>
                          {/* Location pin */}
                          <div className="absolute top-0 right-2 w-6 h-6 bg-red-500 rounded-full flex items-center justify-center text-white text-xs transform rotate-12">
                            📍
                          </div>
                        </div>
                        
                        <div className="space-y-4">
                          <h2 className="text-3xl font-bold text-gray-800">
                            Dreaming of a getaway?
                          </h2>
                          <p className="text-lg text-gray-600 leading-relaxed mt-4">
                            Tell me your travel wishlist and I'll guide you.
                            <br />
                            Ask anything about your upcoming travels!
                          </p>
                        </div>
                      </div>
                    </motion.div>
                  ) : (
                    <MessageBubble
                      message={message}
                      isUser={message.role === 'user'}
                    />
                  )}
                </div>
              ))}
            </AnimatePresence>

            {/* Recommendations */}
            <AnimatePresence>
              {recommendations.map((item, index) => (
                <RecommendationCard
                  key={`${item.id}_${index}`}
                  item={item}
                  onAction={handleCardAction}
                />
              ))}
            </AnimatePresence>

            {/* Debug: Show if we have recommendations */}
            {recommendations.length === 0 && messages.length > 1 && (
              <div className="text-center text-gray-500 p-4 bg-gray-50 rounded-xl">
                <p>No recommendation cards available yet. Try asking about destinations!</p>
              </div>
            )}

            {isLoading && (
              <motion.div
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                className="flex justify-start"
              >
                <div className="flex items-center gap-3 mb-2">
                  <Avatar />
                  <span className="text-sm text-gray-600 font-medium">Travello.ai</span>
                </div>
                <div className="bg-white/80 backdrop-blur-sm p-4 rounded-2xl border border-white/30 mr-4">
                  <div className="flex gap-2">
                    <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" />
                    <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0.1s' }} />
                    <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0.2s' }} />
                  </div>
                </div>
              </motion.div>
            )}
            
            <div ref={messagesEndRef} />
          </div>

          {/* Input Area */}
          <div className="p-6 border-t border-white/30 bg-white/50 backdrop-blur-sm">
            {/* Chips */}
            {currentChips.length > 0 && (
              <div className="mb-4">
                <motion.div
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  className="flex gap-2 overflow-x-auto pb-2"
                >
                  <AnimatePresence>
                    {currentChips.map((chip, index) => (
                      <Chip
                        key={`${chip.value}_${index}`}
                        chip={chip}
                        onClick={handleChipClick}
                      />
                    ))}
                  </AnimatePresence>
                </motion.div>
              </div>
            )}

            {/* Input */}
            <div className="flex gap-3">
              {/* Upload Plus Button - Moved to left */}
              <div className="relative">
                <motion.button
                  onClick={() => setShowUploadPopup(!showUploadPopup)}
                  className="p-4 bg-gray-100 hover:bg-gray-200 text-gray-600 rounded-2xl transition-all duration-200 shadow-md"
                  whileHover={{ scale: 1.05 }}
                  whileTap={{ scale: 0.95 }}
                >
                  <Plus className="w-5 h-5" />
                </motion.button>
                
                <UploadPopup
                  isOpen={showUploadPopup}
                  onClose={() => setShowUploadPopup(false)}
                  onFileUpload={handleFileUpload}
                  onLinkSubmit={handleLinkSubmit}
                />
              </div>
              
              <div className="flex-1 relative">
                <input
                  ref={inputRef}
                  type="text"
                  value={inputMessage}
                  onChange={(e) => setInputMessage(e.target.value)}
                  onKeyPress={(e) => e.key === 'Enter' && handleSendMessage()}
                  placeholder="Ask about destinations, hotels, activities..."
                  className="w-full p-4 pr-12 bg-white/90 backdrop-blur-sm border border-white/30 rounded-2xl focus:outline-none focus:ring-2 focus:ring-blue-500/50 focus:border-transparent placeholder-gray-500 text-gray-800"
                />
                <button 
                  onClick={handleVoiceInput}
                  className={`absolute right-3 top-1/2 transform -translate-y-1/2 p-2 rounded-full transition-all duration-200 ${
                    isRecording 
                      ? 'text-red-500 bg-red-50 animate-pulse' 
                      : 'text-gray-400 hover:text-gray-600 hover:bg-gray-50'
                  }`}
                >
                  <Mic className="w-5 h-5" />
                </button>
              </div>
              
              <motion.button
                onClick={handleSendMessage}
                disabled={!inputMessage.trim() || isLoading}
                className="p-4 bg-gradient-to-r from-green-600 to-orange-600 text-white rounded-2xl hover:from-green-700 hover:to-orange-700 disabled:opacity-50 disabled:cursor-not-allowed transition-all duration-200 shadow-lg"
                whileHover={{ scale: 1.05 }}
                whileTap={{ scale: 0.95 }}
              >
                <Send className="w-5 h-5" />
              </motion.button>
            </div>
          </div>
        </div>

        {/* Right Panel - Feature Canvas */}
        <div className="w-[52%] flex flex-col bg-gradient-to-br from-white/40 to-white/60 backdrop-blur-xl relative z-10">
          {rightPanelContent === 'itinerary' ? (
            /* Generated Itinerary Content View */
            <div className="flex-1 overflow-y-auto">
              {/* Back Button */}
              <div className="p-4 border-b border-white/20">
                <button
                  onClick={() => setRightPanelContent('default')}
                  className="flex items-center gap-2 text-gray-600 hover:text-gray-800 transition-colors duration-200"
                >
                  <X className="w-4 h-4" />
                  Back to Overview
                </button>
              </div>
              
              {/* Itinerary Section */}
              <div className="p-6">
                <h2 className="text-2xl font-bold text-gray-800 mb-4">Your Personalized Itinerary</h2>
                <div className="space-y-4">
                  {generatedItinerary.map((day, index) => (
                    <motion.div
                      key={day.day}
                      initial={{ opacity: 0, y: 20 }}
                      animate={{ opacity: 1, y: 0 }}
                      transition={{ delay: index * 0.1 }}
                      className="bg-white/80 backdrop-blur-sm rounded-2xl p-4 border border-white/30"
                    >
                      <h3 className="text-lg font-bold text-gray-800 mb-3">
                        Day {day.day}: {day.title}
                      </h3>
                      <div className="space-y-2">
                        {day.activities.map((activity, actIndex) => (
                          <div key={actIndex} className="flex items-start gap-3 p-2 hover:bg-gray-50 rounded-lg">
                            <div className="w-16 text-sm font-medium text-blue-600 shrink-0">
                              {activity.time}
                            </div>
                            <div className="flex-1">
                              <div className="font-medium text-gray-800">{activity.activity}</div>
                              <div className="text-sm text-gray-600">{activity.location}</div>
                            </div>
                          </div>
                        ))}
                      </div>
                    </motion.div>
                  ))}
                </div>
              </div>
              
              {/* Accommodations Section */}
              <div className="p-6 border-t border-white/30">
                <h2 className="text-2xl font-bold text-gray-800 mb-4">Recommended Accommodations</h2>
                <div className="space-y-4">
                  {generatedAccommodations.map((hotel, index) => (
                    <motion.div
                      key={hotel.id}
                      initial={{ opacity: 0, x: 20 }}
                      animate={{ opacity: 1, x: 0 }}
                      transition={{ delay: index * 0.1 }}
                      className={`bg-white/80 backdrop-blur-sm rounded-2xl p-4 border transition-all duration-200 ${
                        hotel.highlighted 
                          ? 'border-blue-300 shadow-lg shadow-blue-100' 
                          : 'border-white/30 hover:border-gray-200'
                      }`}
                    >
                      <div className="flex gap-4">
                        <img
                          src={hotel.image}
                          alt={hotel.name}
                          className="w-24 h-24 rounded-xl object-cover"
                        />
                        <div className="flex-1">
                          <div className="flex items-start justify-between">
                            <div>
                              <h3 className="font-bold text-gray-800">{hotel.name}</h3>
                              <p className="text-sm text-gray-600">{hotel.type}</p>
                              <div className="flex items-center gap-2 mt-1">
                                <Star className="w-4 h-4 text-yellow-500 fill-current" />
                                <span className="text-sm font-medium">{hotel.rating}</span>
                              </div>
                            </div>
                            <div className="text-right">
                              <div className="font-bold text-green-600">{hotel.price}</div>
                              <div className="text-xs text-gray-500">per night</div>
                            </div>
                          </div>
                          
                          <div className="mt-2">
                            <div className="flex flex-wrap gap-1 mb-2">
                              {hotel.amenities.slice(0, 3).map((amenity, i) => (
                                <span key={i} className="text-xs bg-gray-100 text-gray-600 px-2 py-1 rounded">
                                  {amenity}
                                </span>
                              ))}
                            </div>
                            <p className="text-sm text-blue-600 font-medium">{hotel.match}</p>
                          </div>
                          
                          {hotel.highlighted && (
                            <button className="mt-3 w-full bg-blue-600 text-white py-2 px-4 rounded-lg hover:bg-blue-700 transition-colors duration-200 text-sm font-medium">
                              Book Now
                            </button>
                          )}
                        </div>
                      </div>
                    </motion.div>
                  ))}
                </div>
              </div>
            </div>
          ) : rightPanelContent === 'destination' && selectedMapDestination ? (
            /* Destination Detail View */
            <div className="flex-1 overflow-y-auto">
              {/* Back Button */}
              <div className="p-4 border-b border-white/20">
                <button
                  onClick={() => setRightPanelContent('default')}
                  className="flex items-center gap-2 text-gray-600 hover:text-gray-800 transition-colors duration-200"
                >
                  <X className="w-4 h-4" />
                  Back to Map
                </button>
              </div>
              
              {/* Destination Details */}
              <div className="p-6">
                <div className="relative h-48 rounded-2xl overflow-hidden mb-6">
                  <img
                    src={selectedMapDestination.hero_image}
                    alt={selectedMapDestination.name}
                    className="w-full h-full object-cover"
                  />
                  <div className="absolute inset-0 bg-gradient-to-t from-black/50 to-transparent" />
                  <div className="absolute bottom-4 left-4 text-white">
                    <h2 className="text-2xl font-bold mb-2">
                      {selectedMapDestination.name}, {selectedMapDestination.country}
                    </h2>
                    <div className="flex items-center gap-4 text-sm">
                      <span>{selectedMapDestination.weather.temp}</span>
                      <span>•</span>
                      <span>{selectedMapDestination.weather.condition}</span>
                    </div>
                  </div>
                </div>
                
                <div className="mb-6">
                  <p className="text-gray-700 leading-relaxed mb-4">{selectedMapDestination.description}</p>
                  <div className="bg-green-50 p-4 rounded-xl">
                    <p className="text-green-700 font-medium">
                      <Heart className="w-4 h-4 inline mr-2" />
                      {selectedMapDestination.why_match}
                    </p>
                  </div>
                </div>
                
                <div className="mb-6">
                  <h3 className="text-xl font-bold text-gray-800 mb-4">Top Highlights</h3>
                  <div className="space-y-3">
                    {selectedMapDestination.highlights.map((highlight, index) => (
                      <div key={index} className="flex items-center gap-3 p-3 bg-white/60 rounded-xl border border-white/30">
                        <MapPin className="w-5 h-5 text-green-600" />
                        <span className="font-medium text-gray-800">{highlight}</span>
                      </div>
                    ))}
                  </div>
                </div>
                
                <div className="flex gap-3">
                  <button 
                    onClick={() => {
                      setExploringDestination(selectedMapDestination);
                      setShowDestinationExploration(true);
                    }}
                    className="flex-1 bg-gradient-to-r from-green-600 to-orange-600 text-white font-semibold py-3 px-6 rounded-xl hover:from-green-700 hover:to-orange-700 transition-all duration-200"
                  >
                    Explore Details
                  </button>
                  <button className="px-6 py-3 border-2 border-gray-200 text-gray-700 font-semibold rounded-xl hover:border-gray-300 hover:bg-gray-50 transition-all duration-200">
                    Save
                  </button>
                </div>
              </div>
            </div>
          ) : rightPanelContent === 'tour' && selectedTour ? (
            /* Tour Detail View */
            <div className="flex-1 overflow-y-auto">
              {/* Back Button */}
              <div className="p-4 border-b border-white/20">
                <button
                  onClick={() => setRightPanelContent('default')}
                  className="flex items-center gap-2 text-gray-600 hover:text-gray-800 transition-colors duration-200"
                >
                  <X className="w-4 h-4" />
                  Back to Tours
                </button>
              </div>
              
              {/* Tour Details */}
              <div className="p-6">
                <div className="relative h-48 rounded-2xl overflow-hidden mb-6">
                  <img
                    src={selectedTour.image}
                    alt={selectedTour.name}
                    className="w-full h-full object-cover"
                  />
                  <div className="absolute inset-0 bg-gradient-to-t from-black/60 to-transparent" />
                  
                  {/* Price Badge */}
                  <div className="absolute top-4 right-4 flex flex-col items-end gap-1">
                    <div className="bg-green-600 text-white px-3 py-2 rounded-lg font-bold text-lg">
                      {selectedTour.price}
                    </div>
                    {selectedTour.originalPrice && (
                      <div className="bg-red-500 text-white px-2 py-1 rounded text-sm line-through">
                        {selectedTour.originalPrice}
                      </div>
                    )}
                  </div>
                  
                  {/* Rating Badge */}
                  <div className="absolute top-4 left-4 bg-orange-500 text-white px-3 py-2 rounded-lg font-semibold flex items-center gap-2">
                    <Star className="w-4 h-4 fill-current" />
                    {selectedTour.rating}
                  </div>
                  
                  <div className="absolute bottom-4 left-4 text-white">
                    <h2 className="text-2xl font-bold mb-2">{selectedTour.name}</h2>
                    <div className="flex items-center gap-4 text-sm">
                      <span className="flex items-center gap-1">
                        <MapPin className="w-4 h-4" />
                        {selectedTour.location}
                      </span>
                      <span>•</span>
                      <span className="bg-white/20 px-2 py-1 rounded">{selectedTour.duration}</span>
                    </div>
                  </div>
                </div>
                
                <div className="mb-6">
                  <div className="flex items-center justify-between mb-4">
                    <h3 className="text-xl font-bold text-gray-800">Tour Overview</h3>
                    <div className="text-sm text-gray-600">
                      ⭐ {selectedTour.rating} ({selectedTour.reviews} reviews)
                    </div>
                  </div>
                  
                  <div className="bg-green-50 p-4 rounded-xl mb-4">
                    <p className="text-green-800 font-medium mb-2">🎯 {selectedTour.type}</p>
                    <p className="text-green-700">Experience the best of {selectedTour.location} with this amazing {selectedTour.duration} tour package.</p>
                  </div>
                  
                  <div className="grid grid-cols-2 gap-4 mb-6">
                    <div className="bg-white/60 p-4 rounded-xl border border-white/30">
                      <div className="flex items-center gap-2 mb-2">
                        <Calendar className="w-5 h-5 text-orange-600" />
                        <span className="font-semibold">Duration</span>
                      </div>
                      <p className="text-gray-700">{selectedTour.duration}</p>
                    </div>
                    <div className="bg-white/60 p-4 rounded-xl border border-white/30">
                      <div className="flex items-center gap-2 mb-2">
                        <Users className="w-5 h-5 text-green-600" />
                        <span className="font-semibold">Group Size</span>
                      </div>
                      <p className="text-gray-700">Up to 15 people</p>
                    </div>
                  </div>
                </div>
                
                <div className="flex gap-3">
                  <button className="flex-1 bg-gradient-to-r from-green-600 to-orange-600 text-white font-semibold py-3 px-6 rounded-xl hover:from-green-700 hover:to-orange-700 transition-all duration-200">
                    Book Now - {selectedTour.price}
                  </button>
                  <button className="px-6 py-3 border-2 border-green-200 text-green-700 font-semibold rounded-xl hover:border-green-300 hover:bg-green-50 transition-all duration-200">
                    Save Tour
                  </button>
                </div>
              </div>
            </div>
          ) : rightPanelContent === 'activity' && selectedActivity ? (
            /* Activity Detail View */
            <div className="flex-1 overflow-y-auto">
              {/* Back Button */}
              <div className="p-4 border-b border-white/20">
                <button
                  onClick={() => setRightPanelContent('default')}
                  className="flex items-center gap-2 text-gray-600 hover:text-gray-800 transition-colors duration-200"
                >
                  <X className="w-4 h-4" />
                  Back to Activities
                </button>
              </div>
              
              {/* Activity Details */}
              <div className="p-6">
                <div className="relative h-48 rounded-2xl overflow-hidden mb-6">
                  <img
                    src={selectedActivity.image}
                    alt={selectedActivity.name}
                    className="w-full h-full object-cover"
                  />
                  <div className="absolute inset-0 bg-gradient-to-t from-black/60 to-transparent" />
                  
                  {/* Price Badge */}
                  <div className="absolute top-4 right-4 flex flex-col items-end gap-1">
                    <div className="bg-orange-600 text-white px-3 py-2 rounded-lg font-bold text-lg">
                      {selectedActivity.price}
                    </div>
                    {selectedActivity.originalPrice && (
                      <div className="bg-red-500 text-white px-2 py-1 rounded text-sm line-through">
                        {selectedActivity.originalPrice}
                      </div>
                    )}
                  </div>
                  
                  {/* Rating Badge */}
                  <div className="absolute top-4 left-4 bg-green-500 text-white px-3 py-2 rounded-lg font-semibold flex items-center gap-2">
                    <Star className="w-4 h-4 fill-current" />
                    {selectedActivity.rating}
                  </div>
                  
                  <div className="absolute bottom-4 left-4 text-white">
                    <h2 className="text-2xl font-bold mb-2">{selectedActivity.name}</h2>
                    <div className="flex items-center gap-4 text-sm">
                      <span className="flex items-center gap-1">
                        <MapPin className="w-4 h-4" />
                        {selectedActivity.location}
                      </span>
                      <span>•</span>
                      <span className="bg-white/20 px-2 py-1 rounded">{selectedActivity.duration}</span>
                    </div>
                  </div>
                </div>
                
                <div className="mb-6">
                  <div className="flex items-center justify-between mb-4">
                    <h3 className="text-xl font-bold text-gray-800">Activity Details</h3>
                    <div className="text-sm text-gray-600">
                      ⭐ {selectedActivity.rating} ({selectedActivity.reviews} reviews)
                    </div>
                  </div>
                  
                  <div className="bg-orange-50 p-4 rounded-xl mb-4">
                    <p className="text-orange-800 font-medium mb-2">🎯 {selectedActivity.type}</p>
                    <p className="text-orange-700">Thrilling {selectedActivity.name.toLowerCase()} experience in {selectedActivity.location} for {selectedActivity.duration}.</p>
                  </div>
                  
                  <div className="grid grid-cols-2 gap-4 mb-6">
                    <div className="bg-white/60 p-4 rounded-xl border border-white/30">
                      <div className="flex items-center gap-2 mb-2">
                        <Clock className="w-5 h-5 text-orange-600" />
                        <span className="font-semibold">Duration</span>
                      </div>
                      <p className="text-gray-700">{selectedActivity.duration}</p>
                    </div>
                    <div className="bg-white/60 p-4 rounded-xl border border-white/30">
                      <div className="flex items-center gap-2 mb-2">
                        <Shield className="w-5 h-5 text-green-600" />
                        <span className="font-semibold">Safety</span>
                      </div>
                      <p className="text-gray-700">Professional guides</p>
                    </div>
                  </div>
                </div>
                
                <div className="flex gap-3">
                  <button className="flex-1 bg-gradient-to-r from-orange-600 to-green-600 text-white font-semibold py-3 px-6 rounded-xl hover:from-orange-700 hover:to-green-700 transition-all duration-200">
                    Book Now - {selectedActivity.price}
                  </button>
                  <button className="px-6 py-3 border-2 border-orange-200 text-orange-700 font-semibold rounded-xl hover:border-orange-300 hover:bg-orange-50 transition-all duration-200">
                    Save Activity
                  </button>
                </div>
              </div>
            </div>
          ) : (
            /* Default Canvas View */
            <>
              {/* Map Section */}
              <div className="p-6">
                <div className="mb-4">
                  <h2 className="text-2xl font-bold text-gray-800 mb-2">Know the Destinations</h2>
                  <p className="text-gray-600">Click on any location to explore</p>
                </div>
                <div className="h-80">
                  <InteractiveMap
                    destinations={destinations}
                    onMarkerClick={handleMapMarkerClick}
                    highlightedDestinations={highlightedDestinations}
                  />
                </div>
              </div>

              {/* Popular Destinations */}
              <div className="flex-1 p-6 overflow-y-auto">
                <div className="space-y-6">
                  {/* Popular Tours for You */}
                  <div className="bg-white/60 backdrop-blur-sm rounded-2xl p-6 border border-white/30">
                    <h3 className="text-lg font-bold text-gray-800 mb-4 flex items-center gap-2">
                      <MapPin className="w-5 h-5 text-green-600" />
                      Popular Tours for You
                    </h3>
                    <div className="grid grid-cols-2 gap-4">
                      {[
                        { 
                          name: 'River Rafting + Paragliding Combo', 
                          location: 'Manali, Himachal Pradesh',
                          image: 'https://images.unsplash.com/photo-1464822759844-d150baec0494?w=400&h=300&fit=crop',
                          price: '₹2,199',
                          originalPrice: '₹3,500',
                          duration: 'Full Day',
                          rating: 4.8,
                          reviews: 1250,
                          type: 'Adventure Combo'
                        },
                        { 
                          name: '8-Day Enchanting Kerala Expedition', 
                          location: 'Kerala (Kochi to Trivandrum)',
                          image: 'https://images.unsplash.com/photo-1602216056096-3b40cc0c9944?w=400&h=300&fit=crop',
                          price: '₹25,999',
                          originalPrice: '₹32,000',
                          duration: '8 Days',
                          rating: 4.7,
                          reviews: 890,
                          type: 'Cultural Tour'
                        },
                        { 
                          name: '16km White Water Rafting + Camp', 
                          location: 'Rishikesh, Uttarakhand',
                          image: 'https://images.unsplash.com/photo-1544551763-46a013bb70d5?w=400&h=300&fit=crop',
                          price: '₹3,000',
                          originalPrice: '₹4,000',
                          duration: '2 Days',
                          rating: 4.9,
                          reviews: 2100,
                          type: 'Adventure Package'
                        },
                        { 
                          name: 'Rajasthan Heritage & Desert Safari', 
                          location: 'Rajasthan (Jaipur to Jaisalmer)',
                          image: 'https://images.unsplash.com/photo-1477587458883-47145ed94245?w=400&h=300&fit=crop',
                          price: '₹15,999',
                          originalPrice: '₹20,000',
                          duration: '7 Days',
                          rating: 4.6,
                          reviews: 750,
                          type: 'Heritage Tour'
                        }
                      ].map((tour, index) => (
                        <motion.div
                          key={tour.name}
                          initial={{ opacity: 0, scale: 0.9 }}
                          animate={{ opacity: 1, scale: 1 }}
                          transition={{ delay: index * 0.1 }}
                          className="relative rounded-xl overflow-hidden cursor-pointer group bg-white shadow-lg border border-green-100"
                          whileHover={{ scale: 1.05 }}
                          onClick={() => {
                            // Open tour details in right panel
                            setRightPanelContent('tour');
                            setSelectedTour(tour);
                          }}
                        >
                          <img
                            src={tour.image}
                            alt={tour.name}
                            className="w-full h-32 object-cover group-hover:scale-110 transition-transform duration-300"
                          />
                          <div className="absolute inset-0 bg-gradient-to-t from-black/70 to-transparent" />
                          
                          {/* Price Badge with Discount */}
                          <div className="absolute top-2 right-2 flex flex-col items-end gap-1">
                            <div className="bg-green-600 text-white px-2 py-1 rounded-lg text-xs font-semibold">
                              {tour.price}
                            </div>
                            {tour.originalPrice && (
                              <div className="bg-red-500 text-white px-1 py-0.5 rounded text-xs line-through">
                                {tour.originalPrice}
                              </div>
                            )}
                          </div>
                          
                          {/* Rating Badge */}
                          <div className="absolute top-2 left-2 bg-orange-500 text-white px-2 py-1 rounded-lg text-xs font-semibold flex items-center gap-1">
                            <Star className="w-3 h-3 fill-current" />
                            {tour.rating}
                          </div>
                          
                          {/* Tour Info */}
                          <div className="absolute bottom-0 left-0 right-0 p-3 text-white">
                            <h4 className="font-semibold text-sm mb-1 line-clamp-2">{tour.name}</h4>
                            <div className="flex items-center justify-between text-xs mb-1">
                              <span className="flex items-center gap-1">
                                <MapPin className="w-3 h-3" />
                                {tour.location}
                              </span>
                            </div>
                            <div className="flex items-center justify-between text-xs">
                              <span className="bg-white/20 px-2 py-1 rounded">
                                {tour.duration}
                              </span>
                              <span className="text-yellow-300">
                                ({tour.reviews} reviews)
                              </span>
                            </div>
                          </div>
                        </motion.div>
                      ))}
                    </div>
                  </div>

                  {/* Activities for You */}
                  <div className="bg-white/60 backdrop-blur-sm rounded-2xl p-6 border border-white/30">
                    <h3 className="text-lg font-bold text-gray-800 mb-4 flex items-center gap-2">
                      <Star className="w-5 h-5 text-orange-600" />
                      Activities for You
                    </h3>
                    <div className="grid grid-cols-2 gap-4">
                      {[
                        { 
                          name: 'Paragliding in Manali', 
                          location: 'Solang Valley, Manali',
                          image: 'https://images.unsplash.com/photo-1540979388789-6cee28a1cdc9?w=400&h=300&fit=crop',
                          price: '₹3,000',
                          originalPrice: '₹3,500',
                          duration: '15 minutes',
                          rating: 4.8,
                          reviews: 1845,
                          type: 'Adventure'
                        },
                        { 
                          name: 'Scuba Diving with Free Videography', 
                          location: 'Pondicherry',
                          image: 'https://images.unsplash.com/photo-1544551763-77ef2d0cfc6c?w=400&h=300&fit=crop',
                          price: '₹6,499',
                          originalPrice: '₹7,500',
                          duration: '2 Hours',
                          rating: 4.9,
                          reviews: 920,
                          type: 'Water Sports'
                        },
                        { 
                          name: 'Scuba Diving in Andaman', 
                          location: 'Havelock Island',
                          image: 'https://images.unsplash.com/photo-1559827260-dc66d52bef19?w=400&h=300&fit=crop',
                          price: '₹3,500',
                          originalPrice: '₹4,200',
                          duration: '30 minutes',
                          rating: 4.9,
                          reviews: 1150,
                          type: 'Marine Adventure'
                        },
                        { 
                          name: 'Bungee Jumping in Rishikesh', 
                          location: 'Jumpin Heights, Rishikesh',
                          image: 'https://images.unsplash.com/photo-1551698618-1dfe5d97d256?w=400&h=300&fit=crop',
                          price: '₹3,500',
                          originalPrice: '₹4,000',
                          duration: '1 Hour',
                          rating: 4.7,
                          reviews: 2200,
                          type: 'Extreme Adventure'
                        }
                      ].map((activity, index) => (
                        <motion.div
                          key={activity.name}
                          initial={{ opacity: 0, scale: 0.9 }}
                          animate={{ opacity: 1, scale: 1 }}
                          transition={{ delay: index * 0.1 }}
                          className="relative rounded-xl overflow-hidden cursor-pointer group bg-white shadow-lg border border-orange-100"
                          whileHover={{ scale: 1.05 }}
                          onClick={() => {
                            // Open activity details in right panel
                            setRightPanelContent('activity');
                            setSelectedActivity(activity);
                          }}
                        >
                          <img
                            src={activity.image}
                            alt={activity.name}
                            className="w-full h-32 object-cover group-hover:scale-110 transition-transform duration-300"
                          />
                          <div className="absolute inset-0 bg-gradient-to-t from-black/70 to-transparent" />
                          
                          {/* Price Badge with Discount */}
                          <div className="absolute top-2 right-2 flex flex-col items-end gap-1">
                            <div className="bg-orange-600 text-white px-2 py-1 rounded-lg text-xs font-semibold">
                              {activity.price}
                            </div>
                            {activity.originalPrice && (
                              <div className="bg-red-500 text-white px-1 py-0.5 rounded text-xs line-through">
                                {activity.originalPrice}
                              </div>
                            )}
                          </div>
                          
                          {/* Rating Badge */}
                          <div className="absolute top-2 left-2 bg-green-500 text-white px-2 py-1 rounded-lg text-xs font-semibold flex items-center gap-1">
                            <Star className="w-3 h-3 fill-current" />
                            {activity.rating}
                          </div>
                          
                          {/* Activity Info */}
                          <div className="absolute bottom-0 left-0 right-0 p-3 text-white">
                            <h4 className="font-semibold text-sm mb-1 line-clamp-2">{activity.name}</h4>
                            <div className="flex items-center justify-between text-xs mb-1">
                              <span className="flex items-center gap-1">
                                <MapPin className="w-3 h-3" />
                                {activity.location}
                              </span>
                            </div>
                            <div className="flex items-center justify-between text-xs">
                              <span className="bg-white/20 px-2 py-1 rounded">
                                {activity.duration}
                              </span>
                              <span className="text-yellow-300">
                                ({activity.reviews} reviews)
                              </span>
                            </div>
                          </div>
                        </motion.div>
                      ))}
                    </div>
                  </div>
                </div>
              </div>
            </>
          )}
        </div>
      </div>

      {/* Personalization Modal - Only show when explicitly triggered */}
      <PersonalizationModal
        isOpen={showPersonalizationModal}
        onClose={() => setShowPersonalizationModal(false)}
        onComplete={handlePersonalizationComplete}
      />

      {/* Destination Modal for detailed view */}
      <DestinationModal
        destination={selectedDestination}
        isOpen={isDestinationModalOpen}
        onClose={() => setIsDestinationModalOpen(false)}
      />

      {/* Sidebar */}
      <Sidebar
        isOpen={isSidebarOpen}
        onClose={() => setIsSidebarOpen(false)}
        chatHistory={chatHistory}
        onNewChat={handleNewChat}
        onSelectChat={(chat) => {
          console.log('Selected chat:', chat);
          setIsSidebarOpen(false);
        }}
      />
    </div>
  );
}

export default App;