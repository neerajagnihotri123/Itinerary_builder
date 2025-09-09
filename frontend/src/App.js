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
  Edit3
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
    <div className={`max-w-[80%] ${isUser ? 'order-2' : 'order-1'}`}>
      {!isUser && (
        <div className="flex items-center gap-3 mb-2">
          <Avatar />
          <span className="text-sm text-gray-600 font-medium">Travello.ai</span>
        </div>
      )}
      <div
        className={`p-4 rounded-2xl ${
          isUser
            ? 'bg-gradient-to-r from-blue-600 to-purple-600 text-white ml-4'
            : 'bg-white/80 backdrop-blur-sm text-gray-800 mr-4 border border-white/30'
        }`}
      >
        <p className="leading-relaxed">{message.content}</p>
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
  
  if (!destination) return null;
  
  const tabs = [
    { id: 'overview', label: 'Overview', icon: MapPin },
    { id: 'stays', label: 'Stays', icon: Hotel },
    { id: 'restaurants', label: 'Restaurants', icon: Heart },
    { id: 'activities', label: 'Things to Do', icon: Star },
    { id: 'reviews', label: 'Reviews', icon: MessageCircle }
  ];
  
  return (
    <AnimatePresence>
      {isOpen && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          className="fixed inset-0 bg-black/50 backdrop-blur-sm z-50 flex items-center justify-center p-4"
          onClick={onClose}
        >
          <motion.div
            variants={modalVariants}
            initial="hidden"
            animate="visible"
            exit="exit"
            className="bg-white rounded-3xl max-w-4xl w-full max-h-[90vh] overflow-hidden"
            onClick={e => e.stopPropagation()}
          >
            <div className="relative h-64 overflow-hidden rounded-t-3xl">
              <img
                src={destination.hero_image}
                alt={destination.name}
                className="w-full h-full object-cover"
              />
              <div className="absolute inset-0 bg-gradient-to-t from-black/50 to-transparent" />
              <button
                onClick={onClose}
                className="absolute top-4 right-4 w-10 h-10 bg-white/90 backdrop-blur-sm rounded-full flex items-center justify-center hover:bg-white transition-colors duration-200"
              >
                <X className="w-5 h-5 text-gray-700" />
              </button>
              <div className="absolute bottom-6 left-6 text-white">
                <h2 className="text-3xl font-bold mb-2">
                  {destination.name}, {destination.country}
                </h2>
                <div className="flex items-center gap-4 text-sm">
                  <span>{destination.weather.temp}</span>
                  <span>•</span>
                  <span>{destination.weather.condition}</span>
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
                      className={`flex items-center gap-2 px-6 py-4 text-sm font-medium whitespace-nowrap border-b-2 transition-colors duration-200 ${
                        activeTab === tab.id
                          ? 'border-blue-600 text-blue-600'
                          : 'border-transparent text-gray-600 hover:text-gray-800'
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
            <div className="p-8 max-h-96 overflow-y-auto">
              {activeTab === 'overview' && (
                <div>
                  <div className="flex flex-wrap gap-2 mb-6">
                    {destination.category.map((cat, index) => (
                      <span
                        key={index}
                        className="bg-blue-100 text-blue-800 px-3 py-1 rounded-full text-sm font-medium"
                      >
                        {cat}
                      </span>
                    ))}
                  </div>
                  
                  <p className="text-gray-700 text-lg leading-relaxed mb-8">
                    {destination.description}
                  </p>
                  
                  <div className="mb-8">
                    <h3 className="text-xl font-bold text-gray-800 mb-4">Top Attractions</h3>
                    <div className="grid grid-cols-2 gap-3">
                      {destination.highlights.map((highlight, index) => (
                        <div key={index} className="flex items-center gap-3 p-3 bg-gray-50 rounded-xl">
                          <MapPin className="w-5 h-5 text-blue-600" />
                          <span className="font-medium text-gray-800">{highlight}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                </div>
              )}

              {activeTab === 'stays' && (
                <div>
                  <h3 className="text-xl font-bold text-gray-800 mb-6">Accommodation Options</h3>
                  <div className="space-y-4">
                    {[
                      { name: 'Luxury Resort & Spa', price: '$200-300/night', rating: 4.8, type: 'Resort' },
                      { name: 'Boutique City Hotel', price: '$120-180/night', rating: 4.6, type: 'Hotel' },
                      { name: 'Cozy Guesthouse', price: '$60-90/night', rating: 4.4, type: 'Guesthouse' }
                    ].map((stay, index) => (
                      <div key={index} className="border rounded-xl p-4 hover:shadow-md transition-shadow duration-200">
                        <div className="flex justify-between items-start">
                          <div>
                            <h4 className="font-semibold text-gray-800">{stay.name}</h4>
                            <p className="text-gray-600 text-sm">{stay.type}</p>
                            <div className="flex items-center gap-2 mt-2">
                              <Star className="w-4 h-4 text-yellow-500 fill-current" />
                              <span className="text-sm font-medium">{stay.rating}</span>
                            </div>
                          </div>
                          <div className="text-right">
                            <p className="font-semibold text-green-600">{stay.price}</p>
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {activeTab === 'restaurants' && (
                <div>
                  <h3 className="text-xl font-bold text-gray-800 mb-6">Local Cuisine</h3>
                  <div className="space-y-4">
                    {[
                      { name: 'Traditional Local Cuisine', type: 'Fine Dining', rating: 4.7, price: '$$$$' },
                      { name: 'Street Food Markets', type: 'Local Street Food', rating: 4.5, price: '$' },
                      { name: 'Rooftop Restaurant', type: 'International', rating: 4.6, price: '$$$' }
                    ].map((restaurant, index) => (
                      <div key={index} className="border rounded-xl p-4 hover:shadow-md transition-shadow duration-200">
                        <div className="flex justify-between items-start">
                          <div>
                            <h4 className="font-semibold text-gray-800">{restaurant.name}</h4>
                            <p className="text-gray-600 text-sm">{restaurant.type}</p>
                            <div className="flex items-center gap-2 mt-2">
                              <Star className="w-4 h-4 text-yellow-500 fill-current" />
                              <span className="text-sm font-medium">{restaurant.rating}</span>
                            </div>
                          </div>
                          <div className="text-right">
                            <p className="font-semibold text-gray-600">{restaurant.price}</p>
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {activeTab === 'activities' && (
                <div>
                  <h3 className="text-xl font-bold text-gray-800 mb-6">Things to Do</h3>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    {[
                      { name: 'Historical Walking Tour', duration: '3 hours', price: '$25' },
                      { name: 'Local Market Experience', duration: '2 hours', price: '$20' },
                      { name: 'Scenic Viewpoint Visit', duration: '1 hour', price: 'Free' },
                      { name: 'Cultural Workshop', duration: '4 hours', price: '$40' }
                    ].map((activity, index) => (
                      <div key={index} className="border rounded-xl p-4 hover:shadow-md transition-shadow duration-200">
                        <h4 className="font-semibold text-gray-800 mb-2">{activity.name}</h4>
                        <div className="flex justify-between text-sm text-gray-600">
                          <span>{activity.duration}</span>
                          <span className="font-medium">{activity.price}</span>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {activeTab === 'reviews' && (
                <div>
                  <h3 className="text-xl font-bold text-gray-800 mb-6">Traveler Reviews</h3>
                  <div className="space-y-6">
                    {[
                      { name: 'Sarah M.', rating: 5, comment: 'Absolutely stunning destination! The culture and scenery exceeded all expectations.' },
                      { name: 'James L.', rating: 4, comment: 'Great place to visit. Food was amazing and locals were very friendly.' },
                      { name: 'Maria C.', rating: 5, comment: 'Perfect for a romantic getaway. Highly recommend the sunset tours!' }
                    ].map((review, index) => (
                      <div key={index} className="border rounded-xl p-4">
                        <div className="flex items-center gap-3 mb-3">
                          <div className="w-10 h-10 bg-gradient-to-br from-blue-500 to-purple-600 rounded-full flex items-center justify-center text-white font-semibold">
                            {review.name.charAt(0)}
                          </div>
                          <div>
                            <h5 className="font-semibold text-gray-800">{review.name}</h5>
                            <div className="flex items-center gap-1">
                              {[...Array(review.rating)].map((_, i) => (
                                <Star key={i} className="w-4 h-4 text-yellow-500 fill-current" />
                              ))}
                            </div>
                          </div>
                        </div>
                        <p className="text-gray-700">{review.comment}</p>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
            
            <div className="p-6 border-t border-gray-200 bg-gray-50">
              <div className="flex gap-4">
                <motion.button
                  className="flex-1 bg-gradient-to-r from-blue-600 to-purple-600 text-white font-semibold py-4 px-8 rounded-xl hover:from-blue-700 hover:to-purple-700 transition-all duration-200"
                  whileHover={{ scale: 1.02 }}
                  whileTap={{ scale: 0.98 }}
                >
                  Plan Trip Here
                </motion.button>
                <motion.button
                  className="px-8 py-4 border-2 border-gray-200 text-gray-700 font-semibold rounded-xl hover:border-gray-300 hover:bg-gray-50 transition-all duration-200"
                  whileHover={{ scale: 1.02 }}
                  whileTap={{ scale: 0.98 }}
                >
                  Save for Later
                </motion.button>
              </div>
            </div>
          </motion.div>
        </motion.div>
      )}
    </AnimatePresence>
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
        className="fixed inset-0 bg-black/20 backdrop-blur-sm z-40"
        onClick={onClose}
      >
        <motion.div
          initial={{ x: -300 }}
          animate={{ x: 0 }}
          exit={{ x: -300 }}
          className="w-80 h-full bg-white/95 backdrop-blur-xl border-r border-white/30 shadow-2xl"
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

// Trip Planning Bar Component
const TripPlanningBar = ({ tripDetails, onUpdateTrip, isVisible }) => {
  if (!isVisible) return null;

  return (
    <motion.div
      initial={{ opacity: 0, y: -20 }}
      animate={{ opacity: 1, y: 0 }}
      className="bg-white/90 backdrop-blur-sm border border-white/30 rounded-xl p-4 mb-4 shadow-lg"
    >
      <div className="flex items-center gap-4 flex-wrap">
        <div className="flex items-center gap-2">
          <MapPin className="w-5 h-5 text-blue-600" />
          <button className="text-sm font-medium text-gray-700 hover:text-blue-600 transition-colors duration-200">
            {tripDetails.destination || 'Choose destination'}
          </button>
        </div>
        
        <div className="flex items-center gap-2">
          <Calendar className="w-5 h-5 text-green-600" />
          <button className="text-sm font-medium text-gray-700 hover:text-green-600 transition-colors duration-200">
            {tripDetails.dates || 'Select dates'}
          </button>
        </div>
        
        <div className="flex items-center gap-2">
          <Users className="w-5 h-5 text-purple-600" />
          <button className="text-sm font-medium text-gray-700 hover:text-purple-600 transition-colors duration-200">
            {tripDetails.travelers || '1 traveler'}
          </button>
        </div>
        
        <div className="flex items-center gap-2">
          <DollarSign className="w-5 h-5 text-orange-600" />
          <button className="text-sm font-medium text-gray-700 hover:text-orange-600 transition-colors duration-200">
            {tripDetails.budget || 'Set budget'}
          </button>
        </div>
        
        <button className="ml-auto p-2 hover:bg-gray-100 rounded-lg transition-colors duration-200">
          <Edit3 className="w-4 h-4 text-gray-500" />
        </button>
      </div>
    </motion.div>
  );
};
function App() {
  const [messages, setMessages] = useState([
    {
      id: '1',
      role: 'assistant',
      content: 'Hi! I\'m Travello.ai, your personal travel planner. I can help you discover amazing destinations, find perfect accommodations, and create unforgettable itineraries. Where would you like to explore today?'
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
  const [destinations] = useState([]);
  
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

    const userMessage = {
      id: Date.now().toString(),
      role: 'user',
      content: inputMessage
    };

    setMessages(prev => [...prev, userMessage]);
    setInputMessage('');
    setIsLoading(true);

    try {
      const response = await axios.post(`${API}/chat`, {
        message: inputMessage,
        session_id: sessionId,
        user_profile: userProfile
      });

      const assistantMessage = {
        id: Date.now().toString() + '_assistant',
        role: 'assistant',
        content: response.data.chat_text
      };

      setMessages(prev => [...prev, assistantMessage]);

      // Process UI actions
      const newRecommendations = [];
      const newChips = [];

      response.data.ui_actions.forEach(action => {
        if (action.type === 'card_add') {
          newRecommendations.push(action.payload);
        } else if (action.type === 'prompt') {
          newChips.push(...action.payload.chips);
        }
      });

      setRecommendations(prev => [...prev, ...newRecommendations]);
      setCurrentChips(newChips);
      setUserProfile(response.data.updated_profile);

    } catch (error) {
      console.error('Chat API error:', error);
      const errorMessage = {
        id: Date.now().toString() + '_error',
        role: 'assistant',
        content: 'I apologize, but I\'m having trouble connecting right now. Please try again in a moment.'
      };
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
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

  const handleCardAction = (action, item) => {
    switch (action) {
      case 'explore':
      case 'details':
        setSelectedDestination(item);
        setIsDestinationModalOpen(true);
        break;
      case 'map':
        // Focus on map area or show item on map
        console.log('Show on map:', item);
        break;
      case 'book':
        // Open booking flow
        console.log('Book:', item);
        break;
      default:
        console.log('Action:', action, item);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-blue-50 to-indigo-100">
      <div className="flex h-screen">
        {/* Left Panel - Chat */}
        <div className="w-[48%] flex flex-col bg-white/80 backdrop-blur-xl border-r border-white/30">
          {/* Header */}
          <div className="p-6 border-b border-white/30 bg-white/50 backdrop-blur-sm">
            <div className="flex items-center gap-4">
              <Avatar />
              <div>
                <h1 className="text-2xl font-bold bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent">
                  Travello.ai
                </h1>
                <p className="text-sm text-gray-600">Your AI Travel Companion</p>
              </div>
            </div>
          </div>

          {/* Chat Messages */}
          <div className="flex-1 overflow-y-auto p-6 space-y-6">
            <AnimatePresence>
              {messages.map((message) => (
                <MessageBubble
                  key={message.id}
                  message={message}
                  isUser={message.role === 'user'}
                />
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
                <button className="absolute right-3 top-1/2 transform -translate-y-1/2 p-2 text-gray-400 hover:text-gray-600 transition-colors duration-200">
                  <Camera className="w-5 h-5" />
                </button>
              </div>
              <motion.button
                onClick={handleSendMessage}
                disabled={!inputMessage.trim() || isLoading}
                className="p-4 bg-gradient-to-r from-blue-600 to-purple-600 text-white rounded-2xl hover:from-blue-700 hover:to-purple-700 disabled:opacity-50 disabled:cursor-not-allowed transition-all duration-200 shadow-lg"
                whileHover={{ scale: 1.05 }}
                whileTap={{ scale: 0.95 }}
              >
                <Send className="w-5 h-5" />
              </motion.button>
            </div>

            {/* Footer Actions */}
            <div className="flex justify-between items-center mt-4 text-sm text-gray-600">
              <button className="hover:text-blue-600 transition-colors duration-200">
                Save & Exit
              </button>
              <button className="hover:text-blue-600 transition-colors duration-200">
                Invite Collaborator
              </button>
            </div>
          </div>
        </div>

        {/* Right Panel - Feature Canvas */}
        <div className="w-[52%] flex flex-col bg-gradient-to-br from-white/40 to-white/60 backdrop-blur-xl">
          {/* Map Section */}
          <div className="p-6">
            <div className="mb-4">
              <h2 className="text-2xl font-bold text-gray-800 mb-2">Know the Destinations</h2>
              <p className="text-gray-600">Discover amazing places around the world</p>
            </div>
            <WorldMap
              destinations={destinations}
              onDestinationClick={(dest) => {
                setSelectedDestination(dest);
                setIsDestinationModalOpen(true);
              }}
            />
          </div>

          {/* Itinerary & Hotels Section */}
          <div className="flex-1 p-6 overflow-y-auto">
            <div className="space-y-6">
              {/* Itinerary Placeholder */}
              <div className="bg-white/60 backdrop-blur-sm rounded-2xl p-6 border border-white/30">
                <h3 className="text-lg font-bold text-gray-800 mb-4 flex items-center gap-2">
                  <Calendar className="w-5 h-5 text-blue-600" />
                  Your Itinerary
                </h3>
                <div className="text-center py-8 text-gray-500">
                  <Clock className="w-12 h-12 mx-auto mb-3 text-gray-300" />
                  <p>Start planning to see your itinerary here</p>
                </div>
              </div>

              {/* Popular Destinations */}
              <div className="bg-white/60 backdrop-blur-sm rounded-2xl p-6 border border-white/30">
                <h3 className="text-lg font-bold text-gray-800 mb-4 flex items-center gap-2">
                  <Heart className="w-5 h-5 text-red-500" />
                  Popular for You
                </h3>
                <div className="grid grid-cols-2 gap-4">
                  {[
                    { name: 'Paris', image: 'https://images.unsplash.com/photo-1502602898536-47ad22581b52?w=300&h=200&fit=crop' },
                    { name: 'Tokyo', image: 'https://images.unsplash.com/photo-1540959733332-eab4deabeeaf?w=300&h=200&fit=crop' },
                    { name: 'Bali', image: 'https://images.unsplash.com/photo-1537953773345-d172ccf13cf1?w=300&h=200&fit=crop' },
                    { name: 'New York', image: 'https://images.unsplash.com/photo-1496442226666-8d4d0e62e6e9?w=300&h=200&fit=crop' }
                  ].map((dest, index) => (
                    <motion.div
                      key={dest.name}
                      initial={{ opacity: 0, scale: 0.9 }}
                      animate={{ opacity: 1, scale: 1 }}
                      transition={{ delay: index * 0.1 }}
                      className="relative rounded-xl overflow-hidden cursor-pointer group"
                      whileHover={{ scale: 1.05 }}
                    >
                      <img
                        src={dest.image}
                        alt={dest.name}
                        className="w-full h-24 object-cover group-hover:scale-110 transition-transform duration-300"
                      />
                      <div className="absolute inset-0 bg-gradient-to-t from-black/60 to-transparent" />
                      <div className="absolute bottom-2 left-2 text-white text-sm font-semibold">
                        {dest.name}
                      </div>
                    </motion.div>
                  ))}
                </div>
              </div>

              {/* Accommodation Placeholder */}
              <div className="bg-white/60 backdrop-blur-sm rounded-2xl p-6 border border-white/30">
                <h3 className="text-lg font-bold text-gray-800 mb-4 flex items-center gap-2">
                  <Hotel className="w-5 h-5 text-green-600" />
                  Accommodation
                </h3>
                <div className="text-center py-8 text-gray-500">
                  <Hotel className="w-12 h-12 mx-auto mb-3 text-gray-300" />
                  <p>Search for hotels to see options here</p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Destination Modal */}
      <DestinationModal
        destination={selectedDestination}
        isOpen={isDestinationModalOpen}
        onClose={() => setIsDestinationModalOpen(false)}
      />
    </div>
  );
}

export default App;