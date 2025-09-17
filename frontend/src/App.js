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
  ChevronLeft,
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
  ArrowLeft
} from 'lucide-react';

// Use local backend for development, production URL for deployed version
const BACKEND_URL = window.location.hostname === 'localhost' 
  ? 'http://localhost:8001' 
  : (process.env.REACT_APP_BACKEND_URL || '');
const API = `${BACKEND_URL}/api`;

console.log('🔍 BACKEND_URL configured as:', BACKEND_URL || 'RELATIVE URL');
console.log('🔍 API URL will be:', API);

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

// Components with updated color palette
const Avatar = () => (
  <motion.div 
    className="w-12 h-12 rounded-full flex items-center justify-center shadow-lg"
    style={{
      background: 'linear-gradient(135deg, var(--primary-500) 0%, var(--primary-600) 100%)'
    }}
    animate={{ 
      boxShadow: [
        '0 4px 20px rgba(230, 149, 67, 0.3)', 
        '0 4px 30px rgba(230, 149, 67, 0.5)', 
        '0 4px 20px rgba(230, 149, 67, 0.3)'
      ]
    }}
    transition={{ 
      duration: 2, 
      repeat: Infinity, 
      repeatType: 'reverse' 
    }}
  >
    <Plane className="w-6 h-6" style={{ color: 'var(--light-50)' }} />
  </motion.div>
);

// Enhanced Professional Horizontal Carousel Component
const ProfessionalCarousel = ({ items, onAction, title = "Recommendations", itemsPerView = 2 }) => {
  const [currentIndex, setCurrentIndex] = useState(0);
  const [isDragging, setIsDragging] = useState(false);
  const [startX, setStartX] = useState(0);
  const [translateX, setTranslateX] = useState(0);
  const [dragVelocity, setDragVelocity] = useState(0);
  const carouselRef = useRef(null);

  const maxIndex = Math.max(0, items.length - itemsPerView);
  const cardWidth = itemsPerView === 2 ? 450 : 340; // Wider cards for 2-item view

  const handleMouseDown = (e) => {
    setIsDragging(true);
    setStartX(e.clientX - translateX);
    setDragVelocity(0);
  };

  const handleMouseMove = (e) => {
    if (!isDragging) return;
    e.preventDefault();
    const currentX = e.clientX - startX;
    const velocity = currentX - translateX;
    setTranslateX(currentX);
    setDragVelocity(velocity);
  };

  const handleMouseUp = () => {
    if (!isDragging) return;
    setIsDragging(false);
    
    const threshold = cardWidth / 3;
    const velocityThreshold = 5;
    
    // Use velocity for smoother interaction
    if ((translateX > threshold || dragVelocity > velocityThreshold) && currentIndex > 0) {
      setCurrentIndex(prev => prev - 1);
    } else if ((translateX < -threshold || dragVelocity < -velocityThreshold) && currentIndex < maxIndex) {
      setCurrentIndex(prev => prev + 1);
    }
    
    setTranslateX(0);
    setDragVelocity(0);
  };

  useEffect(() => {
    if (isDragging) {
      document.addEventListener('mousemove', handleMouseMove);
      document.addEventListener('mouseup', handleMouseUp);
    }
    
    return () => {
      document.removeEventListener('mousemove', handleMouseMove);
      document.removeEventListener('mouseup', handleMouseUp);
    };
  }, [isDragging]); // Only depend on isDragging to prevent infinite loops

  const goToPrevious = () => {
    setCurrentIndex(prev => Math.max(0, prev - 1));
  };

  const goToNext = () => {
    setCurrentIndex(prev => Math.min(maxIndex, prev + 1));
  };

  if (!items || items.length === 0) return null;

  return (
    <div className="mb-8">
      {/* Header with new color palette */}
      <div className="flex items-center justify-between mb-6 px-6">
        <h3 className="text-xl font-bold" style={{ color: 'var(--charcoal-900)' }}>
          {title}
        </h3>
        <div className="flex items-center gap-3">
          <span className="text-sm" style={{ color: 'var(--accent-500)' }}>
            {currentIndex + 1} - {Math.min(currentIndex + itemsPerView, items.length)} of {items.length}
          </span>
          <div className="flex gap-2">
            <button
              className="w-8 h-8 rounded-full flex items-center justify-center transition-all duration-300 hover:scale-110"
              style={{
                backgroundColor: currentIndex === 0 ? 'var(--light-400)' : 'var(--primary-500)',
                color: currentIndex === 0 ? 'var(--accent-500)' : 'var(--light-50)',
                boxShadow: currentIndex === 0 ? 'none' : '0 4px 12px rgba(230, 149, 67, 0.3)'
              }}
              onClick={goToPrevious}
              disabled={currentIndex === 0}
            >
              <ChevronLeft className="w-4 h-4" />
            </button>
            <button
              className="w-8 h-8 rounded-full flex items-center justify-center transition-all duration-300 hover:scale-110"
              style={{
                backgroundColor: currentIndex >= maxIndex ? 'var(--light-400)' : 'var(--primary-500)',
                color: currentIndex >= maxIndex ? 'var(--accent-500)' : 'var(--light-50)',
                boxShadow: currentIndex >= maxIndex ? 'none' : '0 4px 12px rgba(230, 149, 67, 0.3)'
              }}
              onClick={goToNext}
              disabled={currentIndex >= maxIndex}
            >
              <ChevronRight className="w-4 h-4" />
            </button>
          </div>
        </div>
      </div>

      {/* Carousel Container */}
      <div className="relative overflow-hidden px-6">
        <motion.div
          ref={carouselRef}
          className="flex gap-6 cursor-grab active:cursor-grabbing"
          style={{
            transform: `translateX(${-currentIndex * cardWidth + translateX}px)`,
          }}
          animate={{
            transform: `translateX(${-currentIndex * cardWidth}px)`,
          }}
          transition={{
            type: "spring",
            stiffness: 400,
            damping: 40,
            mass: 0.8
          }}
          onMouseDown={handleMouseDown}
          drag="x"
          dragConstraints={{ left: -maxIndex * cardWidth, right: 0 }}
          dragElastic={0.1}
        >
          {items.map((item, index) => (
            <motion.div
              key={item.id || index}
              className="flex-shrink-0 bg-white rounded-2xl overflow-hidden shadow-lg hover:shadow-xl transition-all duration-300 cursor-pointer group"
              style={{
                width: `${cardWidth - 24}px`,
                border: '1px solid var(--light-300)',
                backgroundColor: 'var(--light-50)'
              }}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: index * 0.1 }}
              whileHover={{ 
                y: -8, 
                boxShadow: '0 20px 40px rgba(35,35,35,0.15)',
                borderColor: 'var(--primary-300)'
              }}
              onClick={() => onAction && onAction('explore', item)}
            >
              {/* Enhanced Card Content */}
              <div className="relative h-48 overflow-hidden">
                <img
                  src={item.hero_image || item.image}
                  alt={item.title || item.name}
                  className="w-full h-full object-cover group-hover:scale-110 transition-transform duration-500"
                />
                <div className="absolute inset-0 bg-gradient-to-t from-black/60 via-transparent to-transparent" />
                
                {/* Rating Badge */}
                {item.rating && (
                  <div className="absolute top-4 right-4 px-2 py-1 rounded-full flex items-center gap-1"
                       style={{ backgroundColor: 'rgba(255,255,255,0.95)', backdropFilter: 'blur(10px)' }}>
                    <Star className="w-3 h-3" style={{ color: 'var(--primary-500)' }} fill="currentColor" />
                    <span className="text-xs font-bold" style={{ color: 'var(--charcoal-900)' }}>{item.rating}</span>
                  </div>
                )}
                
                {/* Title Overlay */}
                <div className="absolute bottom-4 left-4 right-4">
                  <h4 className="font-bold text-white text-lg mb-1">{item.title || item.name}</h4>
                  {item.location && (
                    <p className="text-white/80 text-sm flex items-center gap-1">
                      <MapPin className="w-3 h-3" />
                      {item.location}
                    </p>
                  )}
                </div>
              </div>
              
              {/* Card Details */}
              <div className="p-4">
                <div className="flex items-center justify-between mb-3">
                  <span className="text-xs font-medium px-2 py-1 rounded-full"
                        style={{ 
                          backgroundColor: 'var(--primary-100)', 
                          color: 'var(--primary-700)' 
                        }}>
                    {item.duration || item.category || 'Experience'}
                  </span>
                  {item.price && (
                    <span className="font-bold" style={{ color: 'var(--primary-600)' }}>
                      {item.price}
                    </span>
                  )}
                </div>
                
                <p className="text-sm leading-relaxed mb-3" style={{ color: 'var(--accent-600)' }}>
                  {(item.description || item.pitch || '').substring(0, 100)}...
                </p>
                
                <button 
                  className="w-full py-2 px-4 rounded-lg font-medium text-sm transition-all duration-200 hover:scale-105"
                  style={{
                    background: 'linear-gradient(135deg, var(--primary-500) 0%, var(--primary-600) 100%)',
                    color: 'var(--light-50)',
                    boxShadow: '0 4px 12px rgba(230, 149, 67, 0.3)'
                  }}
                  onClick={(e) => {
                    e.stopPropagation();
                    onAction && onAction('explore', item);
                  }}
                >
                  Explore
                </button>
              </div>
            </motion.div>
          ))}
        </motion.div>
      </div>

      {/* Progress Dots */}
      <div className="flex justify-center mt-6 gap-2">
        {Array.from({ length: Math.ceil(items.length / itemsPerView) }, (_, index) => (
          <button
            key={index}
            className="w-2 h-2 rounded-full transition-all duration-300"
            style={{
              backgroundColor: Math.floor(currentIndex / itemsPerView) === index 
                ? 'var(--primary-500)' 
                : 'var(--light-400)',
              transform: Math.floor(currentIndex / itemsPerView) === index ? 'scale(1.5)' : 'scale(1)'
            }}
            onClick={() => setCurrentIndex(index * itemsPerView)}
          />
        ))}
      </div>
    </div>
  );
};

const RecommendationCard = ({ item, onAction }) => {
  const [isHovered, setIsHovered] = useState(false);
  const [currentImageIndex, setCurrentImageIndex] = useState(0);
  
  // Mock multiple images for demonstration
  const images = item.images || [item.hero_image, item.hero_image, item.hero_image];
  
  return (
    <motion.div
      variants={cardVariants}
      initial="hidden"
      animate="visible"
      exit="exit"
      layout
      className="card-premium overflow-hidden mb-6 cursor-pointer group"
      onMouseEnter={() => setIsHovered(true)}
      onMouseLeave={() => setIsHovered(false)}
      whileHover={{ 
        y: -8, 
        boxShadow: '0 25px 50px rgba(0,0,0,0.15)' 
      }}
      transition={{ duration: 0.3 }}
    >
      <div className="relative h-56 overflow-hidden">
        {/* Image Gallery */}
        <motion.img
          src={images[currentImageIndex]}
          alt={item.title}
          className="w-full h-full object-cover"
          animate={{ scale: isHovered ? 1.08 : 1 }}
          transition={{ duration: 0.4 }}
        />
        
        {/* Image Navigation Dots */}
        {images.length > 1 && (
          <div className="absolute bottom-4 left-1/2 transform -translate-x-1/2 flex gap-2">
            {images.map((_, index) => (
              <button
                key={index}
                onClick={(e) => {
                  e.stopPropagation();
                  setCurrentImageIndex(index);
                }}
                className={`w-2 h-2 rounded-full transition-all duration-200 ${
                  index === currentImageIndex ? 'bg-white scale-125' : 'bg-white/60 hover:bg-white/80'
                }`}
              />
            ))}
          </div>
        )}
        
        {/* View All Photos Button */}
        {images.length > 1 && (
          <button
            onClick={(e) => {
              e.stopPropagation();
              onAction('view_photos', item);
            }}
            className="absolute top-4 left-4 bg-black/60 backdrop-blur-sm text-white px-3 py-1 rounded-full text-xs font-medium opacity-0 group-hover:opacity-100 transition-opacity duration-200 flex items-center gap-2"
          >
            <Image className="w-3 h-3" />
            View All ({images.length})
          </button>
        )}
        
        <div className="absolute inset-0 bg-gradient-to-t from-black/60 via-transparent to-transparent" />
        
        {/* Content Overlay */}
        <div className="absolute bottom-4 left-4 right-4 text-white">
          <h3 className="text-xl font-bold mb-2 text-shadow">{item.title}</h3>
          {item.weather && (
            <div className="flex items-center gap-3 text-sm">
              <div className="flex items-center gap-1 bg-black/30 backdrop-blur-sm rounded-full px-2 py-1">
                <Cloud className="w-3 h-3" />
                <span>{item.weather.temp}</span>
              </div>
              <div className="flex items-center gap-1 bg-black/30 backdrop-blur-sm rounded-full px-2 py-1">
                <span>{item.weather.condition}</span>
              </div>
            </div>
          )}
        </div>
        
        {/* Rating Badge */}
        {item.rating && (
          <div className="absolute top-4 right-4 glass-morphism rounded-full px-3 py-2 flex items-center gap-1">
            <Star className="w-4 h-4 text-yellow-500 fill-current" />
            <span className="text-sm font-bold text-slate-800">{item.rating}</span>
          </div>
        )}
        
        {/* Category Badge */}
        {item.category && (
          <div className="absolute top-16 right-4">
            <span className="chip-primary text-xs">
              {item.category === 'destination' ? '🗺️ Destination' : '🏨 Hotel'}
            </span>
          </div>
        )}
      </div>
      
      <div className="p-6 space-y-4">
        {/* Description */}
        <p className="text-slate-600 leading-relaxed text-sm">{item.pitch}</p>
        
        {/* Why Match Section */}
        {item.why_match && (
          <div className="bg-gradient-to-r from-blue-50 to-purple-50 border border-blue-200 rounded-xl p-4">
            <p className="text-blue-800 text-sm font-medium flex items-start gap-3">
              <Heart className="w-4 h-4 text-blue-600 mt-0.5 flex-shrink-0" />
              <span>{item.why_match}</span>
            </p>
          </div>
        )}
        
        {/* Highlights */}
        {item.highlights && (
          <div>
            <h4 className="font-semibold text-slate-800 mb-3 flex items-center gap-2">
              <Star className="w-4 h-4 text-orange-500" />
              Top Highlights
            </h4>
            <div className="grid grid-cols-2 gap-2">
              {item.highlights.slice(0, 4).map((highlight, index) => (
                <div
                  key={index}
                  className="chip-secondary flex items-center gap-2 text-xs p-2"
                >
                  <div className="w-2 h-2 bg-orange-400 rounded-full"></div>
                  <span className="truncate">{highlight}</span>
                </div>
              ))}
            </div>
          </div>
        )}
        
        {/* Pricing */}
        {item.price_estimate && (
          <div className="bg-green-50 border border-green-200 rounded-xl p-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2 text-green-700">
                <DollarSign className="w-5 h-5" />
                <span className="font-bold text-lg">
                  ${item.price_estimate.min} - ${item.price_estimate.max}
                </span>
              </div>
              <span className="text-green-600 text-sm font-medium">per night</span>
            </div>
          </div>
        )}
        
        {/* Amenities for Hotels */}
        {item.amenities && (
          <div>
            <h4 className="font-semibold text-slate-800 mb-2 flex items-center gap-2">
              <Shield className="w-4 h-4 text-blue-500" />
              Amenities
            </h4>
            <div className="flex flex-wrap gap-1">
              {item.amenities.slice(0, 3).map((amenity, index) => (
                <span
                  key={index}
                  className="chip-primary text-xs"
                >
                  {amenity}
                </span>
              ))}
              {item.amenities.length > 3 && (
                <span className="chip-primary text-xs">
                  +{item.amenities.length - 3} more
                </span>
              )}
            </div>
          </div>
        )}
        
        {/* Action Buttons - Updated with Explore and Plan buttons */}
        <div className="flex gap-3 pt-2 border-t border-slate-100">
          {/* Explore Button - Always present */}
          <motion.button
            onClick={() => onAction('explore', item)}
            className="btn-primary flex-1 flex items-center justify-center gap-2 py-3"
            whileHover={{ scale: 1.02 }}
            whileTap={{ scale: 0.98 }}
          >
            Explore
            <ChevronRight className="w-4 h-4" />
          </motion.button>
          
          {/* Plan Trip button for destination cards */}
          {item.category === 'destination' && (
            <motion.button
              onClick={() => onAction('plan_trip', item)}
              className="btn-secondary flex-1 flex items-center justify-center gap-2 py-3"
              whileHover={{ scale: 1.02 }}
              whileTap={{ scale: 0.98 }}
            >
              <Calendar className="w-4 h-4" />
              Plan Trip
            </motion.button>
          )}
          
          {/* Plan Tour button for tour and activity cards */}
          {(item.category === 'tour' || item.category === 'activity' || item.category === 'hotel') && (
            <motion.button
              onClick={() => onAction('plan_tour', item)}
              className="btn-secondary flex-1 flex items-center justify-center gap-2 py-3"
              whileHover={{ scale: 1.02 }}
              whileTap={{ scale: 0.98 }}
            >
              <Calendar className="w-4 h-4" />
              Plan Tour
            </motion.button>
          )}
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
        <div 
          className="w-10 h-10 rounded-full flex items-center justify-center font-semibold text-sm"
          style={{ 
            background: 'linear-gradient(135deg, var(--accent-500) 0%, var(--accent-600) 100%)',
            color: 'var(--light-50)'
          }}
        >
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
          <span className="text-sm font-medium mb-1 ml-1" style={{ color: 'var(--accent-500)' }}>
            Travello.ai
          </span>
        )}
        
        {/* Message bubble */}
        <div
          className={`p-4 rounded-2xl shadow-lg ${
            isUser
              ? 'text-white'
              : 'glass-morphism'
          }`}
          style={{
            background: isUser 
              ? 'linear-gradient(135deg, var(--primary-500) 0%, var(--primary-600) 100%)'
              : undefined,
            color: isUser ? 'var(--light-50)' : 'var(--charcoal-900)'
          }}
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

// Professional Interactive Map Component using Leaflet
const InteractiveWorldMap = ({ destinations, onDestinationClick, highlightedDestinations = [] }) => {
  const [map, setMap] = useState(null);
  const [isLoaded, setIsLoaded] = useState(false);

  // Import Leaflet CSS dynamically
  React.useEffect(() => {
    const link = document.createElement('link');
    link.rel = 'stylesheet';
    link.href = 'https://unpkg.com/leaflet@1.9.4/dist/leaflet.css';
    link.integrity = 'sha256-p4NxAoJBhIIN+hmNHrzRCf9tD/miZyoHS5obTRR9BMY=';
    link.crossOrigin = '';
    document.head.appendChild(link);

    // Load Leaflet JavaScript
    if (!window.L) {
      const script = document.createElement('script');
      script.src = 'https://unpkg.com/leaflet@1.9.4/dist/leaflet.js';
      script.integrity = 'sha256-20nQCchB9co0qIjJZRGuk2/Z9VM+kNiyxNV1lvTlZBo=';
      script.crossOrigin = '';
      script.onload = () => setIsLoaded(true);
      document.head.appendChild(script);
    } else {
      setIsLoaded(true);
    }

    return () => {
      document.head.removeChild(link);
    };
  }, []);

  // Destination coordinates mapping for Indian destinations
  const destinationCoords = {
    'Rishikesh': [30.0869, 78.2676],
    'Manali': [32.2396, 77.1887],
    'Andaman Islands': [11.7401, 92.6586],
    'Kerala': [10.8505, 76.2711],
    'Rajasthan': [27.0238, 74.2179],
    'Pondicherry': [11.9416, 79.8083],
    'Goa': [15.2993, 74.1240],
    'Kashmir': [34.0837, 74.7973],
    'Ladakh': [34.1526, 77.5771],
    'Himachal Pradesh': [31.1048, 77.1734]
  };

  React.useEffect(() => {
    if (!isLoaded || map) return;

    const mapInstance = window.L.map('world-map', {
      center: [20.5937, 78.9629], // Center of India
      zoom: 5,
      minZoom: 2,
      maxZoom: 18,
      zoomControl: true,
      scrollWheelZoom: true,
      doubleClickZoom: true,
      touchZoom: true,
      boxZoom: true,
      keyboard: true,
      dragging: true
    });

    // Add beautiful tile layer
    window.L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
      attribution: '© <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
      maxZoom: 19
    }).addTo(mapInstance);

    // Add custom markers for destinations
    if (destinations && destinations.length > 0) {
      destinations.forEach(dest => {
      const coords = destinationCoords[dest.name] || [
        20 + (Math.random() - 0.5) * 30, // Random lat around India
        78 + (Math.random() - 0.5) * 20  // Random lng around India
      ];

      const isHighlighted = highlightedDestinations.includes(dest.id);
      
      // Create custom icon
      const customIcon = window.L.divIcon({
        className: 'custom-marker',
        html: `
          <div class="relative">
            <div class="w-8 h-8 ${isHighlighted ? 'bg-orange-500 ring-4 ring-orange-200' : 'bg-blue-500 hover:bg-blue-600'} 
                     rounded-full flex items-center justify-center shadow-lg cursor-pointer transition-all duration-200 
                     hover:scale-110 hover:shadow-xl">
              <div class="w-3 h-3 bg-white rounded-full"></div>
            </div>
            <div class="absolute -bottom-6 left-1/2 transform -translate-x-1/2 
                        bg-white px-2 py-1 rounded-md shadow-md text-xs font-medium 
                        whitespace-nowrap ${isHighlighted ? 'block' : 'hidden hover:block'}">
              ${dest.name}
            </div>
          </div>
        `,
        iconSize: [32, 32],
        iconAnchor: [16, 16],
        popupAnchor: [0, -16]
      });

      const marker = window.L.marker(coords, { icon: customIcon }).addTo(mapInstance);
      
      marker.on('click', () => {
        onDestinationClick(dest);
      });

      // Add popup with destination info
      marker.bindPopup(`
        <div class="text-center p-2">
          <img src="${dest.hero_image}" alt="${dest.name}" class="w-24 h-16 object-cover rounded-lg mb-2 mx-auto">
          <h3 class="font-bold text-sm">${dest.name}</h3>
          <p class="text-xs text-gray-600 mb-2">${dest.country}</p>
          <button onclick="window.openDestinationModal('${dest.id}')" 
                  class="bg-blue-500 text-white px-3 py-1 rounded text-xs hover:bg-blue-600">
            Explore
          </button>
        </div>
      `);
      });
    }

    // Add zoom controls with custom styling
    mapInstance.zoomControl.setPosition('bottomright');

    setMap(mapInstance);

    // Cleanup function
    return () => {
      if (mapInstance) {
        mapInstance.remove();
      }
    };
  }, [isLoaded, destinations, onDestinationClick, highlightedDestinations]);

  if (!isLoaded) {
    return (
      <div className="w-full h-full bg-gradient-to-br from-blue-50 to-blue-100 rounded-2xl flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500 mx-auto mb-4"></div>
          <p className="text-gray-600">Loading interactive map...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="relative w-full h-full rounded-2xl overflow-hidden shadow-lg">
      <div id="world-map" className="w-full h-full"></div>
      
      {/* Map Controls Overlay */}
      <div className="absolute top-4 left-4 glass-morphism rounded-lg p-3">
        <div className="flex items-center gap-2 text-sm text-gray-700">
          <Navigation className="w-4 h-4" />
          <span>Drag to explore • Scroll to zoom</span>
        </div>
      </div>

      {/* Custom CSS for map markers */}
      <style jsx>{`
        .custom-marker {
          background: none !important;
          border: none !important;
        }
        .leaflet-popup-content-wrapper {
          border-radius: 12px !important;
        }
        .leaflet-popup-tip {
          background: white !important;
        }
        .leaflet-control-zoom {
          border: none !important;
          box-shadow: 0 4px 12px rgba(0,0,0,0.15) !important;
          border-radius: 8px !important;
        }
        .leaflet-control-zoom a {
          border-radius: 8px !important;
          background: rgba(255,255,255,0.95) !important;
          backdrop-filter: blur(10px) !important;
          border: 1px solid rgba(255,255,255,0.2) !important;
          color: #374151 !important;
          font-weight: 600 !important;
          transition: all 0.2s ease !important;
        }
        .leaflet-control-zoom a:hover {
          background: rgba(255,255,255,1) !important;
          transform: scale(1.05) !important;
        }
      `}</style>
    </div>
  );
};

const DestinationModal = ({ destination, isOpen, onClose, onPlanTrip, onViewAllImages }) => {
  const [currentImageIndex, setCurrentImageIndex] = useState(0);
  const [activeTab, setActiveTab] = useState('overview');
  
  if (!isOpen || !destination) return null;

  // Enhanced gallery with multiple images per destination
  const getDestinationImages = (destination) => {
    const baseImages = [
      destination.hero_image,
      `https://images.unsplash.com/photo-1506905925346-21bda4d32df4?w=800&h=400&fit=crop`, // Landscape
      `https://images.unsplash.com/photo-1469474968028-56623f02e42e?w=800&h=400&fit=crop`, // Nature
      `https://images.unsplash.com/photo-1441974231531-c6227db76b6e?w=800&h=400&fit=crop`, // Forest
      `https://images.unsplash.com/photo-1500534314209-a25ddb2bd429?w=800&h=400&fit=crop`, // Adventure
      `https://images.unsplash.com/photo-1464822759844-d150baec0494?w=800&h=400&fit=crop`, // Mountains
    ];
    
    // Add destination-specific images
    if (destination.name.toLowerCase().includes('kerala')) {
      baseImages.push(
        `https://images.unsplash.com/photo-1602216056096-3b40cc0c9944?w=800&h=400&fit=crop`, // Backwaters
        `https://images.unsplash.com/photo-1578662996442-48f60103fc96?w=800&h=400&fit=crop`  // Houseboat
      );
    } else if (destination.name.toLowerCase().includes('goa')) {
      baseImages.push(
        `https://images.unsplash.com/photo-1571003123894-1f0594d2b5d9?w=800&h=400&fit=crop`, // Beach
        `https://images.unsplash.com/photo-1582719478250-c89cae4dc85b?w=800&h=400&fit=crop`  // Resort
      );
    } else if (destination.name.toLowerCase().includes('rajasthan')) {
      baseImages.push(
        `https://images.unsplash.com/photo-1477587458883-47145ed94245?w=800&h=400&fit=crop`, // Desert
        `https://images.unsplash.com/photo-1571896349842-33c89424de2d?w=800&h=400&fit=crop`  // Palace
      );
    }
    
    return baseImages.filter(img => img).slice(0, 8); // Limit to 8 images
  };
  
  const images = getDestinationImages(destination);
  
  const handleViewAllImages = () => {
    // Call parent function to show images in right panel
    if (onViewAllImages) {
      onViewAllImages(destination, images);
    }
    onClose();
  };
  
  const tabs = [
    { id: 'overview', label: 'Overview', icon: Eye },
    { id: 'stays', label: 'Stays', icon: Hotel },
    { id: 'restaurants', label: 'Restaurants', icon: Utensils },
    { id: 'activities', label: 'Things to Do', icon: MapPin },
    { id: 'reviews', label: 'Reviews', icon: MessageCircle }
  ];
  
  return (
    <AnimatePresence>
      {isOpen && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          className="fixed inset-0 bg-black/70 backdrop-blur-sm z-[100] flex items-center justify-center p-4"
          onClick={onClose}
        >
          <motion.div
            initial={{ scale: 0.95, opacity: 0, y: 20 }}
            animate={{ scale: 1, opacity: 1, y: 0 }}
            exit={{ scale: 0.95, opacity: 0, y: 20 }}
            className="card-premium max-w-5xl w-full max-h-[95vh] overflow-hidden shadow-2xl"
            onClick={(e) => e.stopPropagation()}
          >
            {/* Enhanced Hero Image Gallery Section */}
            <div className="relative h-96 overflow-hidden">
              <motion.img
                key={currentImageIndex}
                src={images[currentImageIndex]}
                alt={destination.name}
                className="w-full h-full object-cover"
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                transition={{ duration: 0.3 }}
              />
              
              {/* Image Navigation */}
              {images.length > 1 && (
                <>
                  <button
                    onClick={() => setCurrentImageIndex(prev => prev === 0 ? images.length - 1 : prev - 1)}
                    className="absolute left-4 top-1/2 transform -translate-y-1/2 glass-morphism rounded-full p-3 hover:bg-white/30 transition-all duration-200"
                  >
                    <ArrowLeft className="w-5 h-5 text-white" />
                  </button>
                  <button
                    onClick={() => setCurrentImageIndex(prev => prev === images.length - 1 ? 0 : prev + 1)}
                    className="absolute right-4 top-1/2 transform -translate-y-1/2 glass-morphism rounded-full p-3 hover:bg-white/30 transition-all duration-200"
                  >
                    <ChevronRight className="w-5 h-5 text-white" />
                  </button>
                  
                  {/* Image Dots */}
                  <div className="absolute bottom-4 left-1/2 transform -translate-x-1/2 flex gap-2">
                    {images.map((_, index) => (
                      <button
                        key={index}
                        onClick={() => setCurrentImageIndex(index)}
                        className={`w-3 h-3 rounded-full transition-all duration-200 ${
                          index === currentImageIndex ? 'bg-white scale-125' : 'bg-white/60 hover:bg-white/80'
                        }`}
                      />
                    ))}
                  </div>
                  
                  {/* View All Button */}
                  <button
                    onClick={handleViewAllImages}
                    className="absolute bottom-4 right-4 glass-morphism rounded-lg px-3 py-2 text-white text-sm font-medium hover:bg-white/20 transition-all duration-200 flex items-center gap-2"
                  >
                    <Image className="w-4 h-4" />
                    View All ({images.length})
                  </button>
                </>
              )}
              
              <div className="absolute inset-0 bg-gradient-to-t from-black/70 via-transparent to-transparent" />
              
              {/* Close Button */}
              <button
                onClick={onClose}
                className="absolute top-6 right-6 glass-morphism rounded-full p-3 hover:bg-white/20 transition-all duration-200 group"
              >
                <X className="w-6 h-6 text-white group-hover:scale-110 transition-transform duration-200" />
              </button>
          
          {/* Destination Info Overlay */}
          <div className="absolute bottom-6 left-6 right-6 text-white">
            <div className="flex items-center justify-between mb-3">
              <div className="flex items-center gap-3">
                <h1 className="text-3xl font-bold">{destination.name}</h1>
                <div className="bg-green-600 text-white px-3 py-1 rounded-full text-sm font-medium">
                  {destination.weather.temp}
                </div>
              </div>
              
              {/* Plan a Trip Button */}
              <motion.button
                onClick={() => {
                  onClose(); // Close the modal first
                  if (onPlanTrip) {
                    onPlanTrip(destination.name);
                  }
                }}
                className="bg-gradient-to-r from-green-600 to-orange-600 text-white px-4 py-2 rounded-xl hover:from-green-700 hover:to-orange-700 transition-colors duration-200 flex items-center gap-2 text-sm font-medium"
                whileHover={{ scale: 1.05 }}
                whileTap={{ scale: 0.95 }}
              >
                <Calendar className="w-4 h-4" />
                Plan Trip
              </motion.button>
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
      )}
    </AnimatePresence>
  );
};

// Sidebar Component with updated color palette
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
          className="w-80 h-full border-r shadow-2xl z-[55]"
          style={{
            backgroundColor: 'var(--light-50)',
            borderColor: 'var(--light-300)'
          }}
          onClick={e => e.stopPropagation()}
        >
          <div className="p-6 border-b" style={{ borderColor: 'var(--light-300)' }}>
            <div className="flex items-center justify-between">
              <h2 className="text-xl font-bold" style={{ color: 'var(--charcoal-900)' }}>Chat History</h2>
              <button
                onClick={onClose}
                className="p-2 rounded-lg transition-colors duration-200"
                style={{ 
                  color: 'var(--accent-600)',
                  backgroundColor: 'transparent'
                }}
                onMouseEnter={(e) => e.target.style.backgroundColor = 'var(--light-200)'}
                onMouseLeave={(e) => e.target.style.backgroundColor = 'transparent'}
              >
                <X className="w-5 h-5" />
              </button>
            </div>
          </div>

          <div className="p-4">
            <motion.button
              onClick={onNewChat}
              className="w-full flex items-center gap-3 p-4 text-white rounded-xl transition-all duration-200 mb-4 shadow-lg"
              style={{
                background: 'linear-gradient(135deg, var(--primary-500) 0%, var(--primary-600) 100%)',
                boxShadow: '0 4px 12px rgba(230, 149, 67, 0.3)'
              }}
              whileHover={{ scale: 1.02 }}
              whileTap={{ scale: 0.98 }}
            >
              <Plus className="w-5 h-5" />
              New Travel Chat
            </motion.button>

            <div className="space-y-2">
              {chatHistory.length === 0 ? (
                <div className="text-center py-8" style={{ color: 'var(--accent-500)' }}>
                  <MessageCircle className="w-12 h-12 mx-auto mb-3" style={{ color: 'var(--light-400)' }} />
                  <p>No previous chats</p>
                </div>
              ) : (
                chatHistory.map((chat, index) => (
                  <motion.button
                    key={chat.id}
                    onClick={() => onSelectChat(chat)}
                    className="w-full text-left p-3 rounded-lg transition-colors duration-200 border"
                    style={{
                      backgroundColor: 'var(--light-50)',
                      borderColor: 'var(--light-300)',
                      color: 'var(--charcoal-900)'
                    }}
                    onMouseEnter={(e) => {
                      e.target.style.backgroundColor = 'var(--light-200)';
                      e.target.style.borderColor = 'var(--primary-300)';
                    }}
                    onMouseLeave={(e) => {
                      e.target.style.backgroundColor = 'var(--light-50)';
                      e.target.style.borderColor = 'var(--light-300)';
                    }}
                    whileHover={{ scale: 1.01 }}
                  >
                    <div className="font-medium truncate">
                      {chat.title || 'Travel Planning Chat'}
                    </div>
                    <div className="text-sm mt-1" style={{ color: 'var(--accent-500)' }}>
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
          className="fixed inset-0 bg-black/70 backdrop-blur-sm z-[100] flex items-center justify-center p-4"
          onClick={onClose}
        >
          <motion.div
            variants={modalVariants}
            initial="hidden"
            animate="visible"
            exit="exit"
            className="card-premium max-w-2xl w-full max-h-[85vh] overflow-y-auto shadow-2xl z-[110]"
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
        className="fixed inset-0 bg-black/70 backdrop-blur-sm z-[80] flex items-center justify-center p-4"
        onClick={onClose}
      >
        <motion.div
          variants={modalVariants}
          initial="hidden"
          animate="visible"
          exit="exit"
          className="card-premium max-w-md w-full p-6"
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

const WhenModal = ({ isOpen, onClose, onSelect, currentDates }) => {
  const [checkIn, setCheckIn] = useState('');
  const [checkOut, setCheckOut] = useState('');

  const handleDateSelection = () => {
    if (checkIn && checkOut) {
      const dateRange = `${new Date(checkIn).toLocaleDateString()} - ${new Date(checkOut).toLocaleDateString()}`;
      onSelect(dateRange);
    }
  };

  return (
  <AnimatePresence>
    {isOpen && (
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        exit={{ opacity: 0 }}
        className="fixed inset-0 bg-black/70 backdrop-blur-sm z-[80] flex items-center justify-center p-4"
        onClick={onClose}
      >
        <motion.div
          variants={modalVariants}
          initial="hidden"
          animate="visible"
          exit="exit"
          className="card-premium max-w-md w-full p-6"
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
                value={checkIn}
                onChange={(e) => setCheckIn(e.target.value)}
                className="input-professional w-full"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Check-out</label>
              <input 
                type="date" 
                value={checkOut}
                onChange={(e) => setCheckOut(e.target.value)}
                className="input-professional w-full"
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
            onClick={handleDateSelection}
            disabled={!checkIn || !checkOut}
            className="btn-primary w-full mt-6 py-3 disabled:opacity-50"
          >
            Confirm Dates
          </button>
        </motion.div>
      </motion.div>
    )}
  </AnimatePresence>
  );
};

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
          className="fixed inset-0 bg-black/70 backdrop-blur-sm z-[80] flex items-center justify-center p-4"
          onClick={onClose}
        >
          <motion.div
            variants={modalVariants}
            initial="hidden"
            animate="visible"
            exit="exit"
            className="card-premium max-w-md w-full p-6"
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

const BudgetModal = ({ isOpen, onClose, onSelect, currentDestination }) => (
  <AnimatePresence>
    {isOpen && (
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        exit={{ opacity: 0 }}
        className="fixed inset-0 bg-black/70 backdrop-blur-sm z-[80] flex items-center justify-center p-4"
        onClick={onClose}
      >
        <motion.div
          variants={modalVariants}
          initial="hidden"
          animate="visible"
          exit="exit"
          className="card-premium max-w-md w-full p-6"
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
                const link = window.prompt('Enter a link to process:');
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
          <InteractiveWorldMap
            destinations={[destination]}
            onDestinationClick={onMapMarkerClick}
            highlightedDestinations={[destination.id]}
          />
        </div>
      </div>
    </div>
  </motion.div>
);
// Trip Planning Bar Component - FIXED POSITIONING
const TripPlanningBar = ({ tripDetails, onUpdateTrip, isVisible, onApplyFilters, onClose }) => {
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
                className="btn-primary text-sm font-medium px-4 py-2"
                whileHover={{ scale: 1.05 }}
                whileTap={{ scale: 0.95 }}
              >
                Apply
              </motion.button>
            )}
            
            <button 
              onClick={onClose}
              className="p-2 hover:bg-gray-100 rounded-lg transition-colors duration-200"
            >
              <X className="w-4 h-4 text-gray-500" />
            </button>
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
  const [questionChips, setQuestionChips] = useState([]);
  const [userProfile, setUserProfile] = useState({});
  const [sessionId] = useState(() => `session_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`);
  const [selectedDestination, setSelectedDestination] = useState(null);
  const [isDestinationModalOpen, setIsDestinationModalOpen] = useState(false);
  const [itinerary, setItinerary] = useState(null);
  const [showTripPlanner, setShowTripPlanner] = useState(false);
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
  const [currentTourImageIndex, setCurrentTourImageIndex] = useState(0);
  const [currentActivityImageIndex, setCurrentActivityImageIndex] = useState(0);
  const [currentDestinationImageIndex, setCurrentDestinationImageIndex] = useState(0);
  
  const messagesEndRef = useRef(null);
  const inputRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, recommendations]);

  // Extract destinations from text for map highlighting
  const extractDestinationsFromText = (text) => {
    const knownDestinations = [
      'Kerala', 'Goa', 'Rajasthan', 'Manali', 'Rishikesh', 'Kashmir', 'Ladakh', 
      'Andaman Islands', 'Pondicherry', 'Himachal Pradesh', 'Mumbai', 'Delhi', 
      'Bangalore', 'Chennai', 'Kolkata', 'Agra', 'Jaipur', 'Udaipur', 'Jodhpur',
      'Varanasi', 'Haridwar', 'Darjeeling', 'Shimla', 'Ooty', 'Munnar', 'Kochi',
      'Alleppey', 'Thekkady', 'Hampi', 'Mysore'
    ];
    
    const found = [];
    const textLower = text.toLowerCase();
    
    knownDestinations.forEach(destination => {
      if (textLower.includes(destination.toLowerCase())) {
        found.push(destination);
      }
    });
    
    return found;
  };

  const handleSendMessage = async () => {
    console.log('🚀 handleSendMessage called!');
    
    if (!inputMessage.trim() || isLoading) {
      console.log('❌ Cannot send: empty message or loading');
      return;
    }

    console.log('🔥 Message to send:', inputMessage);
    console.log('🔥 API URL:', `${BACKEND_URL}/api/chat`);

    const currentInput = inputMessage;
    setInputMessage('');
    setIsLoading(true);

    // Add user message immediately
    const userMessage = {
      id: `user_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
      role: 'user',
      content: currentInput
    };

    setMessages(prev => [...prev, userMessage]);

    try {
      console.log('📡 Making API call...');
      
      const response = await Promise.race([
        fetch(`${BACKEND_URL}/api/chat`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            message: currentInput,
            session_id: sessionId,
            user_profile: userProfile,
            trip_details: tripDetails
          })
        }),
        new Promise((_, reject) => 
          setTimeout(() => reject(new Error('Request timeout after 30 seconds')), 30000)
        )
      ]);

      console.log('✅ Response status:', response.status);
      console.log('✅ Response headers:', response.headers);
      
      if (!response.ok) {
        const errorText = await response.text();
        console.error('❌ Response error:', errorText);
        throw new Error(`HTTP error! status: ${response.status}, message: ${errorText}`);
      }

      const data = await response.json();
      console.log('✅ Response data:', data);
      console.log('✅ Response ui_actions:', data.ui_actions);
      console.log('✅ Response chat_text:', data.chat_text);

      // Add assistant response
      const assistantMessage = {
        id: `assistant_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
        role: 'assistant',
        content: data.chat_text || 'I received your message!'
      };

      setMessages(prev => [...prev, assistantMessage]);

      // Process UI actions for cards, itineraries, and question chips
      if (data.ui_actions && data.ui_actions.length > 0) {
        console.log('🎨 Processing UI actions:', data.ui_actions.length);
        console.log('🎨 UI Actions details:', data.ui_actions);
        
        const newRecommendations = [];
        const newQuestionChips = [];
        let newItinerary = null;
        const mentionedDestinations = [];
        
        data.ui_actions.forEach(action => {
          if (action.type === 'card_add' && action.payload) {
            newRecommendations.push(action.payload);
            console.log('🎴 Added card:', action.payload.title);
            
            // Extract destination for map highlighting if it's a destination card
            if (action.payload.category === 'destination' && action.payload.title) {
              const destinationName = action.payload.title.split(',')[0].trim(); // Get main name before comma
              mentionedDestinations.push(destinationName);
            }
          } else if (action.type === 'question_chip' && action.payload) {
            newQuestionChips.push(action.payload);
            console.log('💬 Added question chip:', action.payload.question);
          } else if (action.type === 'itinerary_display' && action.payload) {
            newItinerary = action.payload;
            console.log('🗓️ Added itinerary:', action.payload.id);
          } else if (action.type === 'trip_planner_card' && action.payload) {
            // Pre-populate trip planner with backend data
            console.log('🎯 Processing trip_planner_card action!', action.payload);
            const payload = action.payload;
            if (payload.current_destination) {
              setTripDetails(prev => ({
                ...prev,
                destination: payload.current_destination
              }));
            }
            if (payload.current_dates) {
              // Parse date range if provided
              const dateMatch = payload.current_dates.match(/(\d{4}-\d{2}-\d{2}) to (\d{4}-\d{2}-\d{2})/);
              if (dateMatch) {
                setTripDetails(prev => ({
                  ...prev,
                  dates: payload.current_dates,
                  startDate: dateMatch[1],
                  endDate: dateMatch[2]
                }));
              }
            }
            if (payload.current_budget) {
              setTripDetails(prev => ({
                ...prev,
                budget: payload.current_budget
              }));
            }
            console.log('🎯 About to set showTripPlanner to true');
            setShowTripPlanner(true);
            console.log('📋 Trip planner should now be showing with payload:', payload);
          }
        });

        if (newRecommendations.length > 0) {
          // Replace recommendations instead of appending to prevent continuous addition
          setRecommendations(newRecommendations);
        }
        
        if (newQuestionChips.length > 0) {
          setQuestionChips(newQuestionChips);
        }
        
        if (newItinerary) {
          setItinerary(newItinerary);
          // Connect to the rendering state and show in right panel
          setGeneratedItinerary(newItinerary.itinerary || []);
          setRightPanelContent('itinerary');
          console.log('🗓️ Set itinerary with', (newItinerary.itinerary || []).length, 'days');
        }

        // Update map highlighting for mentioned destinations
        if (mentionedDestinations.length > 0) {
          setHighlightedDestinations(prev => {
            const newHighlighted = [...new Set([...prev, ...mentionedDestinations])]; // Remove duplicates
            console.log('🗺️ Highlighting destinations on map:', newHighlighted);
            return newHighlighted;
          });
        }
      }

      // Also extract destinations from the assistant's text response for map highlighting
      if (data.chat_text) {
        const extractedDestinations = extractDestinationsFromText(data.chat_text);
        if (extractedDestinations.length > 0) {
          setHighlightedDestinations(prev => {
            const newHighlighted = [...new Set([...prev, ...extractedDestinations])];
            console.log('🗺️ Highlighting destinations from text:', extractedDestinations);
            return newHighlighted;
          });
        }
      }

    } catch (error) {
      console.error('❌ API Error:', error);
      
      const errorMessage = {
        id: `error_${Date.now()}`,
        role: 'assistant',
        content: `Sorry, I'm having trouble connecting. Error: ${error.message}`
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

  const handleQuestionChipClick = (questionChip) => {
    // Clear existing question chips and send the question as a new message
    setQuestionChips([]);
    setInputMessage(questionChip.question);
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

  const handlePersonalizationComplete = async (responses) => {
    console.log('Personalization completed:', responses);
    setShowPersonalizationModal(false);
    setIsLoading(true);
    
    const targetDestination = tripDetails.destination || 'your destination';
    
    // Add initial itinerary message to chat
    const initialMessage = {
      id: Date.now().toString(),
      role: 'assistant',
      content: `Perfect! Let me create a personalized itinerary for ${targetDestination} based on your preferences. This will take just a moment...`
    };
    setMessages(prev => [...prev, initialMessage]);
    
    try {
      // Create detailed trip planning message for AI agents
      const itineraryRequest = `Create a detailed ${tripDetails.dates || '5-day'} itinerary for ${targetDestination} with these preferences: ${Object.entries(responses).map(([key, value]) => `${key}: ${value}`).join(', ')}. Include daily activities, accommodations, dining, and transportation.`;
      
      // Send to backend AI agents for real itinerary generation
      const response = await fetch(`${BACKEND_URL}/api/chat`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          message: itineraryRequest,
          session_id: sessionId,
          user_profile: { ...userProfile, ...responses },
          trip_details: tripDetails
        })
      });
      
      if (response.ok) {
        const data = await response.json();
        
        // Add AI-generated response to chat
        const aiMessage = {
          id: Date.now().toString(),
          role: 'assistant',
          content: data.chat_text || `Here's your personalized ${tripDetails.dates || '5-day'} itinerary for ${targetDestination}!`
        };
        setMessages(prev => [...prev, aiMessage]);
        
        // Check if backend provided structured itinerary data
        if (data.itinerary && Array.isArray(data.itinerary)) {
          setGeneratedItinerary(data.itinerary);
        } else {
          // Parse itinerary from AI response or create structured version
          const aiGeneratedItinerary = parseItineraryFromAI(data.chat_text, tripDetails, targetDestination);
          setGeneratedItinerary(aiGeneratedItinerary);
        }
        
        // Process accommodations from AI response
        if (data.hotels && Array.isArray(data.hotels)) {
          setGeneratedAccommodations(data.hotels);
        } else {
          // Generate accommodations based on destination
          const accommodations = await generateAccommodationsFromAI(targetDestination, responses);
          setGeneratedAccommodations(accommodations);
        }
        
        // Process any UI actions (cards, recommendations)
        if (data.ui_actions && data.ui_actions.length > 0) {
          const newRecommendations = [];
          data.ui_actions.forEach(action => {
            if (action.type === 'card_add' && action.payload) {
              newRecommendations.push(action.payload);
            }
          });
          if (newRecommendations.length > 0) {
            setRecommendations(newRecommendations);
          }
        }
        
      } else {
        throw new Error('Failed to generate itinerary');
      }
      
    } catch (error) {
      console.error('Itinerary generation error:', error);
      
      // Fallback to enhanced mock itinerary if AI fails
      const fallbackItinerary = generateEnhancedMockItinerary(tripDetails, responses, targetDestination);
      const fallbackAccommodations = generateMockAccommodations(tripDetails, responses, targetDestination);
      
      setGeneratedItinerary(fallbackItinerary);
      setGeneratedAccommodations(fallbackAccommodations);
      
      const fallbackMessage = {
        id: Date.now().toString(),
        role: 'assistant',
        content: `I've created a wonderful ${tripDetails.dates || '5-day'} itinerary for ${targetDestination} based on your preferences! While I had a minor connectivity issue, I've crafted this plan with local insights and popular attractions.`
      };
      setMessages(prev => [...prev, fallbackMessage]);
    } finally {
      setIsLoading(false);
      setRightPanelContent('itinerary');
      setShowGeneratedContent(true);
    }
  };

  // Helper function to parse AI response into structured itinerary
  const parseItineraryFromAI = (aiText, tripDetails, destination) => {
    // This is a simplified parser - in production you'd use more sophisticated NLP
    const days = [];
    const dayPattern = /Day (\d+):?\s*([^Day]*)/gi;
    let match;
    let dayCount = 1;
    
    while ((match = dayPattern.exec(aiText)) !== null && dayCount <= 7) {
      const dayNumber = parseInt(match[1]) || dayCount;
      const content = match[2] || `Explore ${destination}`;
      
      days.push({
        day: dayNumber,
        title: `Day ${dayNumber} in ${destination}`,
        activities: [
          {
            time: "9:00 AM",
            title: content.substring(0, 50) + "...",
            description: content,
            location: destination,
            category: "sightseeing"
          }
        ]
      });
      dayCount++;
    }
    
    // If no structured days found, create a basic itinerary
    if (days.length === 0) {
      for (let i = 1; i <= 5; i++) {
        days.push({
          day: i,
          title: `Day ${i} in ${destination}`,
          activities: [
            {
              time: "9:00 AM",
              title: `Explore ${destination}`,
              description: `Discover the best of ${destination} with guided tours and local experiences.`,
              location: destination,
              category: "sightseeing"
            }
          ]
        });
      }
    }
    
    return days;
  };
  
  // Helper function to generate accommodations from AI
  const generateAccommodationsFromAI = async (destination, preferences) => {
    try {
      const accommodationRequest = `Recommend 3-5 hotels in ${destination} based on these preferences: ${Object.entries(preferences).map(([key, value]) => `${key}: ${value}`).join(', ')}`;
      
      const response = await fetch(`${BACKEND_URL}/api/chat`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          message: accommodationRequest,
          session_id: sessionId,
          user_profile: userProfile,
          trip_details: tripDetails
        })
      });
      
      if (response.ok) {
        const data = await response.json();
        if (data.hotels && Array.isArray(data.hotels)) {
          return data.hotels;
        }
      }
    } catch (error) {
      console.error('Failed to generate AI accommodations:', error);
    }
    
    // Return mock accommodations as fallback
    return generateMockAccommodations(tripDetails, preferences, destination);
  };
  
  // Enhanced mock itinerary generator as fallback
  const generateEnhancedMockItinerary = (tripDetails, preferences, destination) => {
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

  const generateMockAccommodations = (tripDetails, preferences, destination) => {
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
    console.log('🎯 Card action:', action, item.title || item.name);
    
    switch (action) {
      case 'explore':
        // Handle different card types for explore action
        if (item.category === 'destination') {
          // Find the full destination data and show in right panel
          const fullDestination = destinations.find(d => 
            d.name.toLowerCase().includes((item.title || item.name).split(',')[0].toLowerCase()) ||
            (item.title || item.name).toLowerCase().includes(d.name.toLowerCase())
          );
          
          if (fullDestination) {
            console.log('🗺️ Found destination:', fullDestination.name);
            setSelectedMapDestination(fullDestination);
            setRightPanelContent('destination');
            setHighlightedDestinations([fullDestination.id]);
          } else {
            console.log('❌ Destination not found for:', item.title || item.name);
          }
        } else if (item.category === 'hotel') {
          // Show hotel details in right panel
          console.log('🏨 Exploring hotel:', item.title || item.name);
          setSelectedTour(item); // Using selectedTour for hotels too
          setRightPanelContent('tour');
        } else if (item.category === 'tour') {
          // Show tour details in right panel
          console.log('🎪 Exploring tour:', item.title || item.name);
          setSelectedTour(item);
          setRightPanelContent('tour');
        } else if (item.category === 'activity') {
          // Show activity details in right panel
          console.log('🎭 Exploring activity:', item.title || item.name);
          setSelectedActivity(item);
          setRightPanelContent('activity');
        } else {
          // Default: show generic details in right panel
          console.log('🔍 Exploring item:', item.title || item.name);
          setSelectedTour(item);
          setRightPanelContent('tour');
        }
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
          content: `I'd love to help you book ${item.title || item.name}! First, let's complete your trip planning details so I can find the perfect accommodations for you.`
        };
        setMessages(prev => [...prev, bookingMessage]);
        setShowTripBar(true);
        break;
        
      case 'plan_trip':
        // Extract destination name from the item title
        const destinationName = (item.title || item.name).split(',')[0].trim();
        handlePlanTripFromModal(destinationName);
        break;
        
      case 'plan_tour':
        // Handle tour planning
        handlePlanTour(item);
        break;
        
      default:
        console.log('Unknown action:', action, item);
    }
  };

  const handlePlanTour = async (tourItem) => {
    console.log('🎭 Planning tour for:', tourItem.name || tourItem.title);
    
    // Close right panel and show chat interface
    setRightPanelContent('default');
    
    // Create a plan tour message
    const planTourMessage = `I want to plan ${tourItem.name || tourItem.title} in ${tourItem.location}`;
    
    // Add user message to chat immediately
    const userMessage = {
      id: `user_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
      role: 'user',
      content: planTourMessage
    };
    setMessages(prev => [...prev, userMessage]);
    
    // Show trip planning bar for personalization
    setShowTripBar(true);
    
    // Send to backend for processing
    try {
      setIsLoading(true);
      const response = await fetch(`${BACKEND_URL}/api/chat`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          message: planTourMessage,
          session_id: sessionId,
          user_profile: userProfile,
          trip_details: { 
            ...tripDetails, 
            tour: tourItem.name || tourItem.title,
            location: tourItem.location,
            duration: tourItem.duration,
            price: tourItem.price
          }
        })
      });
      
      if (response.ok) {
        const data = await response.json();
        
        // Add assistant response
        const assistantMessage = {
          id: `assistant_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
          role: 'assistant',
          content: data.chat_text || `Great choice! I'll help you plan ${tourItem.name}. Let me gather some details to create the perfect itinerary for you.`
        };
        setMessages(prev => [...prev, assistantMessage]);
        
        // Process any UI actions
        if (data.ui_actions && data.ui_actions.length > 0) {
          const newRecommendations = [];
          data.ui_actions.forEach(action => {
            if (action.type === 'card_add' && action.payload) {
              newRecommendations.push(action.payload);
            }
          });
          if (newRecommendations.length > 0) {
            setRecommendations(newRecommendations);
          }
        }
      } else {
        throw new Error('Failed to get response from server');
      }
      
    } catch (error) {
      console.error('Plan tour message error:', error);
      const errorMessage = {
        id: `error_${Date.now()}`,
        role: 'assistant',
        content: `I'd love to help you plan ${tourItem.name}! Let's start by gathering some details about your preferences.`
      };
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleViewAllImages = (destination, images) => {
    console.log('🖼️ Viewing all images for:', destination.name);
    setRightPanelContent('gallery');
    setSelectedMapDestination(destination);
    // Store images in the destination object for right panel access
    setSelectedMapDestination({
      ...destination,
      galleryImages: images
    });
  };

  const handlePlanTripFromModal = async (destinationName) => {
    console.log('🗓️ Planning trip for:', destinationName);
    
    // Create a plan trip message
    const planTripMessage = `Plan a trip to ${destinationName}`;
    
    // Add user message to chat immediately
    const userMessage = {
      id: `user_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
      role: 'user',
      content: planTripMessage
    };
    setMessages(prev => [...prev, userMessage]);
    
    // Show trip planning bar immediately
    setShowTripBar(true);
    
    // Send the message directly through API
    try {
      setIsLoading(true);
      const response = await axios.post(`${API}/chat`, {
        message: planTripMessage,
        session_id: sessionId,
        user_profile: userProfile,
        trip_details: { ...tripDetails, destination: destinationName }
      });

      const assistantMessage = {
        id: `assistant_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
        role: 'assistant',
        content: response.data.chat_text
      };

      setMessages(prev => [...prev, assistantMessage]);
      
      // Process any UI actions
      if (response.data.ui_actions && response.data.ui_actions.length > 0) {
        console.log('UI actions from plan trip:', response.data.ui_actions);
        // You could handle UI actions here if needed
      }
      
    } catch (error) {
      console.error('Plan trip message error:', error);
      const errorMessage = {
        id: `error_${Date.now()}`,
        role: 'assistant',
        content: 'Sorry, I had trouble processing your trip planning request. Please try again.'
      };
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleVoiceInput = () => {
    if (!('webkitSpeechRecognition' in window) && !('SpeechRecognition' in window)) {
      window.alert('Speech recognition is not supported in this browser');
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
    // Save current conversation to history if it has messages
    if (messages.length > 1) { // More than just the initial greeting
      const currentChat = {
        id: sessionId,
        title: generateChatTitle(messages),
        messages: [...messages],
        recommendations: [...recommendations],
        tripDetails: { ...tripDetails },
        timestamp: new Date().toISOString(),
        destination: tripDetails.destination || extractDestinationFromMessages(messages)
      };
      
      setChatHistory(prev => [currentChat, ...prev.slice(0, 9)]); // Keep last 10 chats
      console.log('💾 Saved current chat to history:', currentChat.title);
    }
    
    // Reset current conversation
    setMessages([
      {
        id: Date.now().toString(),
        role: 'assistant',
        content: 'Dreaming of a getaway? Tell me your travel wishlist and I\'ll guide you.\nAsk anything about your upcoming travels!'
      }
    ]);
    setRecommendations([]);
    setCurrentChips([]);
    setQuestionChips([]);
    setTripDetails({});
    setHighlightedDestinations([]);
    setItinerary(null);
    setGeneratedItinerary([]);
    // Don't reset right panel content - keep it as is (especially if showing map)
    // setRightPanelContent('default'); // REMOVED: This was causing map to disappear
    setShowTripBar(false);
    setIsSidebarOpen(false);
    
    // Generate new session ID
    const newSessionId = `session_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
    // Note: sessionId is a const, so we'll need to trigger a re-render differently
    console.log('🆕 Starting new chat session');
  };

  // Helper function to generate chat title from messages
  const generateChatTitle = (messages) => {
    // Find first user message that's not a greeting
    const userMessages = messages.filter(msg => msg.role === 'user');
    if (userMessages.length > 0) {
      const firstMessage = userMessages[0].content;
      // Extract key destinations or trip types
      const destinations = extractDestinationsFromText(firstMessage);
      if (destinations.length > 0) {
        return `Trip to ${destinations[0]}`;
      }
      // Return truncated first message
      return firstMessage.length > 30 ? firstMessage.substring(0, 30) + '...' : firstMessage;
    }
    return 'Travel Planning Chat';
  };

  // Helper function to extract destination from message history
  const extractDestinationFromMessages = (messages) => {
    for (const message of messages) {
      if (message.role === 'user') {
        const destinations = extractDestinationsFromText(message.content);
        if (destinations.length > 0) {
          return destinations[0];
        }
      }
    }
    return null;
  };

  // Enhanced select chat handler
  const handleSelectChat = (chat) => {
    // Save current conversation before switching
    if (messages.length > 1) {
      const currentChat = {
        id: sessionId,
        title: generateChatTitle(messages),
        messages: [...messages],
        recommendations: [...recommendations],
        tripDetails: { ...tripDetails },
        timestamp: new Date().toISOString(),
        destination: tripDetails.destination || extractDestinationFromMessages(messages)
      };
      
      setChatHistory(prev => {
        const filtered = prev.filter(c => c.id !== sessionId); // Remove if already exists
        return [currentChat, ...filtered.slice(0, 9)];
      });
    }

    // Load selected conversation
    setMessages(chat.messages || []);
    setRecommendations(chat.recommendations || []);
    setTripDetails(chat.tripDetails || {});
    if (chat.destination) {
      setHighlightedDestinations([chat.destination]);
    }
    
    console.log('📂 Loaded chat:', chat.title);
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
                className="p-1 hover:bg-white/50 rounded-lg transition-colors duration-200"
                title="Chat History"
              >
                <Menu className="w-4 h-4 text-gray-600" />
              </button>
              <Avatar />
              <div className="flex-1">
                <h1 className="text-2xl font-bold" style={{
                  background: 'linear-gradient(135deg, var(--primary-500) 0%, var(--primary-600) 100%)',
                  WebkitBackgroundClip: 'text',
                  backgroundClip: 'text',
                  WebkitTextFillColor: 'transparent',
                  color: 'transparent'
                }}>
                  Travello.ai
                </h1>
                <p className="text-sm" style={{ color: 'var(--accent-600)' }}>Your AI Travel Companion</p>
              </div>
            </div>
          </div>

          {/* Trip Planning Bar */}
          <TripPlanningBar 
            tripDetails={tripDetails}
            onUpdateTrip={setTripDetails}
            isVisible={showTripBar}
            onApplyFilters={handleApplyFilters}
            onClose={() => setShowTripBar(false)}
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
                          <h2 className="text-3xl font-bold text-gradient">
                            Ready for your next adventure?
                          </h2>
                          <p className="text-lg text-slate-600 leading-relaxed mt-4">
                            I'm your personal travel concierge, ready to craft the perfect Indian getaway just for you.
                            <br />
                            <span className="text-blue-600 font-medium">Tell me where you'd like to explore!</span>
                          </p>
                          
                          {/* Quick start suggestions */}
                          <div className="grid grid-cols-2 gap-3 mt-6">
                            <button 
                              onClick={() => {
                                setInputMessage("Plan a trip to Rishikesh");
                                setTimeout(() => handleSendMessage(), 100);
                              }}
                              className="btn-outline text-sm py-2 px-3 hover:bg-blue-50"
                            >
                              🏔️ Mountain Adventure
                            </button>
                            <button 
                              onClick={() => {
                                setInputMessage("Beach destinations in India");
                                setTimeout(() => handleSendMessage(), 100);
                              }}
                              className="btn-outline text-sm py-2 px-3 hover:bg-blue-50"
                            >
                              🏖️ Beach Paradise
                            </button>
                            <button 
                              onClick={() => {
                                setInputMessage("Cultural heritage tours");
                                setTimeout(() => handleSendMessage(), 100);
                              }}
                              className="btn-outline text-sm py-2 px-3 hover:bg-blue-50"
                            >
                              🏛️ Cultural Journey
                            </button>
                            <button 
                              onClick={() => {
                                setInputMessage("Weekend getaway ideas");
                                setTimeout(() => handleSendMessage(), 100);
                              }}
                              className="btn-outline text-sm py-2 px-3 hover:bg-blue-50"
                            >
                              ⚡ Quick Escape
                            </button>
                          </div>
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

            {/* Enhanced Recommendations Carousel */}
            {recommendations.length > 0 && (
              <ProfessionalCarousel
                items={recommendations}
                onAction={handleCardAction}
                title="Your Personalized Recommendations"
                itemsPerView={3}
              />
            )}

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

            {/* Question Chips - "You might want to ask" */}
            {questionChips.length > 0 && (
              <div className="mb-4">
                <motion.div
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  className="space-y-3"
                >
                  <div className="flex items-center justify-between">
                    <p className="text-sm font-medium text-slate-600">💡 You might want to ask:</p>
                    <button 
                      onClick={() => setQuestionChips([])}
                      className="text-slate-400 hover:text-slate-600 p-1 rounded-md hover:bg-slate-100 transition-colors duration-200"
                    >
                      <X className="w-4 h-4" />
                    </button>
                  </div>
                  <div className="flex flex-wrap gap-2">
                    <AnimatePresence>
                      {questionChips.map((questionChip, index) => (
                        <motion.div
                          key={`question_${questionChip.id}_${index}`}
                          initial={{ opacity: 0, scale: 0.9 }}
                          animate={{ opacity: 1, scale: 1 }}
                          exit={{ opacity: 0, scale: 0.9 }}
                          className="relative group"
                        >
                          <motion.button
                            onClick={() => handleQuestionChipClick(questionChip)}
                            className="card-elevated px-3 py-2 text-xs font-medium text-slate-700 hover:text-blue-700 bg-white hover:bg-blue-50 border border-slate-200 hover:border-blue-300 rounded-full transition-all duration-200 flex items-center gap-2 group-hover:shadow-md"
                            whileHover={{ scale: 1.05, y: -1 }}
                            whileTap={{ scale: 0.95 }}
                          >
                            <span className="text-blue-500">🤔</span>
                            <span className="max-w-[200px] truncate">{questionChip.question}</span>
                          </motion.button>
                          <button
                            onClick={(e) => {
                              e.stopPropagation();
                              setQuestionChips(prev => prev.filter((_, i) => i !== index));
                            }}
                            className="absolute -top-1 -right-1 w-5 h-5 bg-slate-400 hover:bg-slate-600 text-white rounded-full flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity duration-200"
                          >
                            <X className="w-3 h-3" />
                          </button>
                        </motion.div>
                      ))}
                    </AnimatePresence>
                  </div>
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
                  className="input-professional w-full pr-12"
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
                className="btn-primary p-4 disabled:opacity-50 disabled:cursor-not-allowed rounded-2xl"
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
            /* Professional Itinerary View - Mindtrip.ai Style */
            <div className="flex-1 overflow-y-auto bg-gradient-to-br from-slate-50 to-white">
              {/* Header Section */}
              <div className="sticky top-0 bg-white/95 backdrop-blur-sm border-b border-slate-200 p-6 z-10">
                <div className="flex items-center justify-between">
                  <div>
                    <h1 className="text-2xl font-bold text-slate-900 mb-1">Your Trip Itinerary</h1>
                    <p className="text-slate-600 text-sm">
                      {generatedItinerary.length} days • {tripDetails.destination || 'Your destination'}
                    </p>
                  </div>
                  <button
                    onClick={() => setRightPanelContent('default')}
                    className="p-2 hover:bg-slate-100 rounded-lg transition-colors"
                  >
                    <X className="w-5 h-5 text-slate-600" />
                  </button>
                </div>
              </div>

              {/* Itinerary Content */}
              <div className="p-6">
                {/* Trip Summary Cards */}
                <div className="grid grid-cols-3 gap-4 mb-8">
                  <div className="bg-white rounded-xl p-4 border border-slate-200 shadow-sm">
                    <div className="flex items-center gap-3">
                      <div className="w-10 h-10 bg-blue-100 rounded-lg flex items-center justify-center">
                        <Calendar className="w-5 h-5 text-blue-600" />
                      </div>
                      <div>
                        <p className="text-sm text-slate-600">Duration</p>
                        <p className="font-semibold text-slate-900">{generatedItinerary.length} Days</p>
                      </div>
                    </div>
                  </div>
                  
                  <div className="bg-white rounded-xl p-4 border border-slate-200 shadow-sm">
                    <div className="flex items-center gap-3">
                      <div className="w-10 h-10 bg-green-100 rounded-lg flex items-center justify-center">
                        <MapPin className="w-5 h-5 text-green-600" />
                      </div>
                      <div>
                        <p className="text-sm text-slate-600">Destination</p>
                        <p className="font-semibold text-slate-900">{tripDetails.destination || 'India'}</p>
                      </div>
                    </div>
                  </div>
                  
                  <div className="bg-white rounded-xl p-4 border border-slate-200 shadow-sm">
                    <div className="flex items-center gap-3">
                      <div className="w-10 h-10 bg-purple-100 rounded-lg flex items-center justify-center">
                        <Users className="w-5 h-5 text-purple-600" />
                      </div>
                      <div>
                        <p className="text-sm text-slate-600">Travelers</p>
                        <p className="font-semibold text-slate-900">
                          {(tripDetails.travelers?.adults || 2)} Adults
                          {(tripDetails.travelers?.children || 0) > 0 && `, ${tripDetails.travelers.children} Kids`}
                        </p>
                      </div>
                    </div>
                  </div>
                </div>

                {/* Day-by-Day Itinerary */}
                <div className="space-y-6">
                  {generatedItinerary.map((day, dayIndex) => (
                    <motion.div
                      key={day.day}
                      initial={{ opacity: 0, y: 20 }}
                      animate={{ opacity: 1, y: 0 }}
                      transition={{ delay: dayIndex * 0.1 }}
                      className="bg-white rounded-2xl border border-slate-200 shadow-sm overflow-hidden"
                    >
                      {/* Day Header */}
                      <div className="bg-gradient-to-r from-slate-900 to-slate-700 text-white p-5">
                        <div className="flex items-center justify-between">
                          <div>
                            <h3 className="text-lg font-semibold">Day {day.day}</h3>
                            <p className="text-slate-300 text-sm mt-1">
                              {day.title || `Exploring ${tripDetails.destination}`}
                            </p>
                          </div>
                          <div className="text-right">
                            <p className="text-slate-300 text-sm">Activities</p>
                            <p className="text-white font-semibold">{day.activities?.length || 3}</p>
                          </div>
                        </div>
                      </div>

                      {/* Activities List */}
                      <div className="p-5">
                        <div className="space-y-4">
                          {(day.activities || [
                            {
                              time: "9:00 AM",
                              title: "Morning Exploration",
                              description: `Start your day exploring the best of ${tripDetails.destination}`,
                              location: tripDetails.destination,
                              category: "sightseeing"
                            },
                            {
                              time: "1:00 PM",
                              title: "Local Cuisine Experience",
                              description: "Enjoy authentic local dishes at a recommended restaurant",
                              location: tripDetails.destination,
                              category: "dining"
                            },
                            {
                              time: "4:00 PM",
                              title: "Cultural Activities",
                              description: "Immerse yourself in local culture and traditions",
                              location: tripDetails.destination,
                              category: "cultural"
                            }
                          ]).map((activity, actIndex) => (
                            <div key={actIndex} className="flex gap-4 p-4 bg-slate-50 rounded-xl hover:bg-slate-100 transition-colors">
                              {/* Time Badge */}
                              <div className="flex-shrink-0">
                                <div className="bg-white border border-slate-200 rounded-lg px-3 py-2 min-w-[80px] text-center">
                                  <p className="text-sm font-medium text-slate-900">{activity.time}</p>
                                </div>
                              </div>
                              
                              {/* Activity Content */}
                              <div className="flex-1">
                                <div className="flex items-start justify-between mb-2">
                                  <h4 className="font-semibold text-slate-900 text-base">{activity.title}</h4>
                                  <span className={`px-2 py-1 rounded-full text-xs font-medium ${{
                                    'sightseeing': 'bg-blue-100 text-blue-700',
                                    'dining': 'bg-orange-100 text-orange-700',
                                    'cultural': 'bg-purple-100 text-purple-700',
                                    'adventure': 'bg-green-100 text-green-700',
                                    'shopping': 'bg-pink-100 text-pink-700'
                                  }[activity.category] || 'bg-gray-100 text-gray-700'}`}>
                                    {activity.category || 'Activity'}
                                  </span>
                                </div>
                                <p className="text-slate-600 text-sm mb-2">{activity.description}</p>
                                {activity.location && (
                                  <div className="flex items-center gap-1 text-slate-500 text-xs">
                                    <MapPin className="w-3 h-3" />
                                    <span>{activity.location}</span>
                                  </div>
                                )}
                              </div>
                            </div>
                          ))}
                        </div>
                      </div>
                    </motion.div>
                  ))}
                </div>

                {/* Accommodation Section */}
                {generatedAccommodations && generatedAccommodations.length > 0 && (
                  <div className="mt-8">
                    <h3 className="text-xl font-bold text-slate-900 mb-4">Recommended Accommodations</h3>
                    <div className="grid gap-4">
                      {generatedAccommodations.map((hotel, index) => (
                        <motion.div
                          key={hotel.id || index}
                          initial={{ opacity: 0, y: 20 }}
                          animate={{ opacity: 1, y: 0 }}
                          transition={{ delay: 0.2 + index * 0.1 }}
                          className="bg-white rounded-xl border border-slate-200 shadow-sm p-5 hover:shadow-md transition-shadow"
                        >
                          <div className="flex justify-between items-start mb-3">
                            <div>
                              <h4 className="font-semibold text-slate-900 text-lg">{hotel.name}</h4>
                              <div className="flex items-center gap-2 mt-1">
                                <div className="flex text-yellow-400">
                                  {[...Array(5)].map((_, i) => (
                                    <Star key={i} className={`w-4 h-4 ${i < Math.floor(hotel.rating || 4.5) ? 'fill-current' : ''}`} />
                                  ))}
                                </div>
                                <span className="text-sm text-slate-600">{hotel.rating || 4.5}/5</span>
                              </div>
                            </div>
                            <div className="text-right">
                              <p className="text-2xl font-bold text-slate-900">₹{hotel.price_estimate || 5000}</p>
                              <p className="text-sm text-slate-600">per night</p>
                            </div>
                          </div>
                          
                          <p className="text-slate-600 text-sm mb-4">{hotel.reason || hotel.description}</p>
                          
                          {hotel.amenities && hotel.amenities.length > 0 && (
                            <div className="flex flex-wrap gap-2 mb-4">
                              {hotel.amenities.slice(0, 4).map((amenity, i) => (
                                <span key={i} className="px-2 py-1 bg-slate-100 text-slate-700 text-xs rounded-md">
                                  {amenity}
                                </span>
                              ))}
                            </div>
                          )}
                          
                          <div className="flex gap-3">
                            <button className="flex-1 bg-slate-900 text-white font-medium py-2 px-4 rounded-lg hover:bg-slate-800 transition-colors">
                              Book Now
                            </button>
                            <button className="px-4 py-2 border border-slate-300 text-slate-700 font-medium rounded-lg hover:bg-slate-50 transition-colors">
                              View Details
                            </button>
                          </div>
                        </motion.div>
                      ))}
                    </div>
                  </div>
                )}

                {/* Action Buttons */}
                <div className="mt-8 flex gap-4">
                  <button className="flex-1 bg-gradient-to-r from-green-600 to-orange-600 text-white font-semibold py-3 px-6 rounded-xl hover:from-green-700 hover:to-orange-700 transition-all duration-200">
                    Save Itinerary
                  </button>
                  <button className="flex-1 border-2 border-slate-300 text-slate-700 font-semibold py-3 px-6 rounded-xl hover:border-slate-400 hover:bg-slate-50 transition-all duration-200">
                    Modify Plan
                  </button>
                </div>
              </div>
            </div>
          ) : rightPanelContent === 'destination' && selectedMapDestination ? (
            /* Destination Detail View - Updated with new color palette */
            <div className="flex-1 overflow-y-auto">
              {/* Back Button */}
              <div className="p-6 border-b" style={{ borderColor: 'var(--light-300)' }}>
                <button 
                  onClick={() => setRightPanelContent('default')}
                  className="flex items-center gap-2 text-sm font-medium rounded-lg px-3 py-2 transition-colors duration-200"
                  style={{ 
                    color: 'var(--accent-600)',
                    backgroundColor: 'transparent'
                  }}
                  onMouseEnter={(e) => e.target.style.backgroundColor = 'var(--light-200)'}
                  onMouseLeave={(e) => e.target.style.backgroundColor = 'transparent'}
                >
                  <ArrowLeft className="w-4 h-4" />
                  Back to Map
                </button>
              </div>

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
                  <p className="leading-relaxed mb-4" style={{ color: 'var(--charcoal-800)' }}>
                    {selectedMapDestination.description}
                  </p>
                  <div className="p-4 rounded-xl" style={{ backgroundColor: 'var(--primary-50)' }}>
                    <p className="font-medium" style={{ color: 'var(--primary-700)' }}>
                      <Heart className="w-4 h-4 inline mr-2" />
                      {selectedMapDestination.why_match}
                    </p>
                  </div>
                </div>

                <div className="mb-6">
                  <h3 className="text-xl font-bold mb-4" style={{ color: 'var(--charcoal-900)' }}>
                    Top Highlights
                  </h3>
                  <div className="space-y-3">
                    {selectedMapDestination.highlights.map((highlight, index) => (
                      <div key={index} className="flex items-center gap-3 p-3 rounded-xl border"
                           style={{ 
                             backgroundColor: 'var(--light-50)', 
                             borderColor: 'var(--light-300)' 
                           }}>
                        <MapPin className="w-5 h-5" style={{ color: 'var(--primary-600)' }} />
                        <span className="font-medium" style={{ color: 'var(--charcoal-800)' }}>
                          {highlight}
                        </span>
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
                    className="flex-1 text-white font-semibold py-3 px-6 rounded-xl transition-all duration-200 hover:scale-105"
                    style={{
                      background: 'linear-gradient(135deg, var(--primary-500) 0%, var(--primary-600) 100%)',
                      boxShadow: '0 4px 12px rgba(230, 149, 67, 0.3)'
                    }}
                  >
                    Explore More
                  </button>
                  <button 
                    onClick={() => setRightPanelContent('default')}
                    className="px-6 py-3 border rounded-xl font-medium transition-all duration-200"
                    style={{
                      borderColor: 'var(--light-300)',
                      color: 'var(--accent-600)',
                      backgroundColor: 'var(--light-50)'
                    }}
                    onMouseEnter={(e) => {
                      e.target.style.backgroundColor = 'var(--light-200)';
                      e.target.style.borderColor = 'var(--primary-300)';
                    }}
                    onMouseLeave={(e) => {
                      e.target.style.backgroundColor = 'var(--light-50)';
                      e.target.style.borderColor = 'var(--light-300)';
                    }}
                  >
                    Close
                  </button>
                </div>
              </div>
            </div>
          ) : rightPanelContent === 'tour' && selectedTour ? (
            /* Tour Detail View - Updated with new color palette */
            <div className="flex-1 overflow-y-auto">
              {/* Back Button */}
              <div className="p-6 border-b" style={{ borderColor: 'var(--light-300)' }}>
                <button
                  onClick={() => setRightPanelContent('default')}
                  className="flex items-center gap-2 text-sm font-medium rounded-lg px-3 py-2 transition-colors duration-200"
                  style={{ 
                    color: 'var(--accent-600)',
                    backgroundColor: 'transparent'
                  }}
                  onMouseEnter={(e) => e.target.style.backgroundColor = 'var(--light-200)'}
                  onMouseLeave={(e) => e.target.style.backgroundColor = 'transparent'}
                >
                  <ArrowLeft className="w-4 h-4" />
                  <span className="font-medium">Back to Tours</span>
                </button>
              </div>
              
              {/* Tour Details */}
              <div className="p-6">
                {/* Main Image */}
                <div className="relative h-48 rounded-2xl overflow-hidden mb-6">
                  <img
                    src={selectedTour.hero_image || selectedTour.image}
                    alt={selectedTour.name || selectedTour.title}
                    className="w-full h-full object-cover"
                  />
                  <div className="absolute inset-0 bg-gradient-to-t from-black/50 to-transparent" />
                  <div className="absolute bottom-4 left-4 text-white">
                    <h2 className="text-2xl font-bold mb-2">
                      {selectedTour.name || selectedTour.title}
                    </h2>
                    <div className="flex items-center gap-4 text-sm">
                      <span className="flex items-center gap-1">
                        <MapPin className="w-4 h-4" />
                        {selectedTour.location}
                      </span>
                      <span>•</span>
                      <span>{selectedTour.duration}</span>
                    </div>
                  </div>
                  
                  {/* Rating Badge */}
                  {selectedTour.rating && (
                    <div className="absolute top-4 right-4 px-3 py-1 rounded-full flex items-center gap-1"
                         style={{ backgroundColor: 'rgba(255,255,255,0.95)', backdropFilter: 'blur(10px)' }}>
                      <Star className="w-4 h-4" style={{ color: 'var(--primary-500)' }} fill="currentColor" />
                      <span className="font-bold" style={{ color: 'var(--charcoal-900)' }}>{selectedTour.rating}</span>
                    </div>
                  )}
                </div>
                
                {/* Tour Information */}
                <div className="mb-6">
                  <h3 className="text-xl font-bold mb-3" style={{ color: 'var(--charcoal-900)' }}>
                    Tour Details
                  </h3>
                  <p className="leading-relaxed mb-4" style={{ color: 'var(--charcoal-800)' }}>
                    {selectedTour.description || "Experience an amazing tour with professional guides and comfortable accommodations. This tour includes all major attractions and local cultural experiences."}
                  </p>
                  
                  {/* Tour Highlights */}
                  <div className="p-4 rounded-xl mb-4" style={{ backgroundColor: 'var(--primary-50)' }}>
                    <h4 className="font-semibold mb-2" style={{ color: 'var(--primary-700)' }}>
                      Tour Highlights
                    </h4>
                    <ul className="space-y-1" style={{ color: 'var(--primary-600)' }}>
                      <li>• Professional local guide</li>
                      <li>• All entrance fees included</li>
                      <li>• Comfortable transportation</li>
                      <li>• Small group experience</li>
                    </ul>
                  </div>
                  
                  {/* Price and Duration */}
                  <div className="flex items-center justify-between p-4 rounded-xl border"
                       style={{ backgroundColor: 'var(--light-50)', borderColor: 'var(--light-300)' }}>
                    <div>
                      <span className="text-sm" style={{ color: 'var(--accent-500)' }}>Duration</span>
                      <p className="font-bold" style={{ color: 'var(--charcoal-900)' }}>{selectedTour.duration}</p>
                    </div>
                    <div className="text-right">
                      <span className="text-sm" style={{ color: 'var(--accent-500)' }}>Price</span>
                      <p className="text-xl font-bold" style={{ color: 'var(--primary-600)' }}>
                        {selectedTour.price}
                      </p>
                    </div>
                  </div>
                </div>
                
                {/* Action Buttons */}
                <div className="flex gap-3">
                  <button 
                    onClick={() => {
                      // Add booking logic here
                      console.log('Booking tour:', selectedTour.name);
                    }}
                    className="flex-1 text-white font-semibold py-3 px-6 rounded-xl transition-all duration-200 hover:scale-105"
                    style={{
                      background: 'linear-gradient(135deg, var(--primary-500) 0%, var(--primary-600) 100%)',
                      boxShadow: '0 4px 12px rgba(230, 149, 67, 0.3)'
                    }}
                  >
                    Book Now
                  </button>
                  <button 
                    onClick={() => setRightPanelContent('default')}
                    className="px-6 py-3 border rounded-xl font-medium transition-all duration-200"
                    style={{
                      borderColor: 'var(--light-300)',
                      color: 'var(--accent-600)',
                      backgroundColor: 'var(--light-50)'
                    }}
                    onMouseEnter={(e) => {
                      e.target.style.backgroundColor = 'var(--light-200)';
                      e.target.style.borderColor = 'var(--primary-300)';
                    }}
                    onMouseLeave={(e) => {
                      e.target.style.backgroundColor = 'var(--light-50)';
                      e.target.style.borderColor = 'var(--light-300)';
                    }}
                  >
                    Close
                  </button>
                </div>
              </div>
            </div>
          ) : rightPanelContent === 'activity' && selectedActivity ? (
            /* Activity Detail View - Updated with new color palette */
            <div className="flex-1 overflow-y-auto">
              {/* Back Button */}
              <div className="p-6 border-b" style={{ borderColor: 'var(--light-300)' }}>
                <button
                  onClick={() => setRightPanelContent('default')}
                  className="flex items-center gap-2 text-sm font-medium rounded-lg px-3 py-2 transition-colors duration-200"
                  style={{ 
                    color: 'var(--accent-600)',
                    backgroundColor: 'transparent'
                  }}
                  onMouseEnter={(e) => e.target.style.backgroundColor = 'var(--light-200)'}
                  onMouseLeave={(e) => e.target.style.backgroundColor = 'transparent'}
                >
                  <ArrowLeft className="w-4 h-4" />
                  <span className="font-medium">Back to Activities</span>
                </button>
              </div>
              
              {/* Activity Details */}
              <div className="p-6">
                {/* Main Image */}
                <div className="relative h-48 rounded-2xl overflow-hidden mb-6">
                  <img
                    src={selectedActivity.hero_image || selectedActivity.image}
                    alt={selectedActivity.name || selectedActivity.title}
                    className="w-full h-full object-cover"
                  />
                  <div className="absolute inset-0 bg-gradient-to-t from-black/50 to-transparent" />
                  <div className="absolute bottom-4 left-4 text-white">
                    <h2 className="text-2xl font-bold mb-2">
                      {selectedActivity.name || selectedActivity.title}
                    </h2>
                    <div className="flex items-center gap-4 text-sm">
                      <span className="flex items-center gap-1">
                        <MapPin className="w-4 h-4" />
                        {selectedActivity.location}
                      </span>
                      <span>•</span>
                      <span>{selectedActivity.duration}</span>
                    </div>
                  </div>
                  
                  {/* Rating Badge */}
                  {selectedActivity.rating && (
                    <div className="absolute top-4 right-4 px-3 py-1 rounded-full flex items-center gap-1"
                         style={{ backgroundColor: 'rgba(255,255,255,0.95)', backdropFilter: 'blur(10px)' }}>
                      <Star className="w-4 h-4" style={{ color: 'var(--primary-500)' }} fill="currentColor" />
                      <span className="font-bold" style={{ color: 'var(--charcoal-900)' }}>{selectedActivity.rating}</span>
                    </div>
                  )}
                </div>
                
                {/* Activity Information */}
                <div className="mb-6">
                  <h3 className="text-xl font-bold mb-3" style={{ color: 'var(--charcoal-900)' }}>
                    Activity Details
                  </h3>
                  <p className="leading-relaxed mb-4" style={{ color: 'var(--charcoal-800)' }}>
                    {selectedActivity.description || "Join us for an exciting adventure activity with professional guides and safety equipment. This activity is perfect for thrill seekers and adventure enthusiasts."}
                  </p>
                  
                  {/* Activity Highlights */}
                  <div className="p-4 rounded-xl mb-4" style={{ backgroundColor: 'var(--primary-50)' }}>
                    <h4 className="font-semibold mb-2" style={{ color: 'var(--primary-700)' }}>
                      Activity Highlights
                    </h4>
                    <ul className="space-y-1" style={{ color: 'var(--primary-600)' }}>
                      <li>• Professional safety equipment provided</li>
                      <li>• Experienced certified instructors</li>
                      <li>• Photos and videos included</li>
                      <li>• Small group for personalized attention</li>
                    </ul>
                  </div>
                  
                  {/* Price and Duration */}
                  <div className="flex items-center justify-between p-4 rounded-xl border"
                       style={{ backgroundColor: 'var(--light-50)', borderColor: 'var(--light-300)' }}>
                    <div>
                      <span className="text-sm" style={{ color: 'var(--accent-500)' }}>Duration</span>
                      <p className="font-bold" style={{ color: 'var(--charcoal-900)' }}>{selectedActivity.duration}</p>
                    </div>
                    <div className="text-right">
                      <span className="text-sm" style={{ color: 'var(--accent-500)' }}>Price</span>
                      <p className="text-xl font-bold" style={{ color: 'var(--primary-600)' }}>
                        {selectedActivity.price}
                      </p>
                    </div>
                  </div>
                </div>
                
                {/* Action Buttons */}
                <div className="flex gap-3">
                  <button 
                    onClick={() => {
                      // Add booking logic here
                      console.log('Booking activity:', selectedActivity.name);
                    }}
                    className="flex-1 text-white font-semibold py-3 px-6 rounded-xl transition-all duration-200 hover:scale-105"
                    style={{
                      background: 'linear-gradient(135deg, var(--primary-500) 0%, var(--primary-600) 100%)',
                      boxShadow: '0 4px 12px rgba(230, 149, 67, 0.3)'
                    }}
                  >
                    Book Now
                  </button>
                  <button 
                    onClick={() => setRightPanelContent('default')}
                    className="px-6 py-3 border rounded-xl font-medium transition-all duration-200"
                    style={{
                      borderColor: 'var(--light-300)',
                      color: 'var(--accent-600)',
                      backgroundColor: 'var(--light-50)'
                    }}
                    onMouseEnter={(e) => {
                      e.target.style.backgroundColor = 'var(--light-200)';
                      e.target.style.borderColor = 'var(--primary-300)';
                    }}
                    onMouseLeave={(e) => {
                      e.target.style.backgroundColor = 'var(--light-50)';
                      e.target.style.borderColor = 'var(--light-300)';
                    }}
                  >
                    Close
                  </button>
                </div>
              </div>
            </div>
          ) : rightPanelContent === 'gallery' && selectedMapDestination ? (
            /* Image Gallery View */
            <div className="flex-1 overflow-y-auto">
              {/* Back Button */}
              <div className="p-4 border-b border-white/20">
                <button
                  onClick={() => setRightPanelContent('default')}
                  className="flex items-center gap-2 text-gray-600 hover:text-gray-800 transition-colors duration-200"
                >
                  <ArrowLeft className="w-5 h-5" />
                  <span className="font-medium">Back to Map</span>
                </button>
              </div>
              
              {/* Gallery Header */}
              <div className="p-6 border-b border-white/20">
                <h2 className="text-2xl font-bold text-gray-800 mb-2">
                  {selectedMapDestination.name} Gallery
                </h2>
                <p className="text-gray-600">
                  {selectedMapDestination.galleryImages?.length || 0} Images
                </p>
              </div>
              
              {/* Image Grid */}
              <div className="p-6">
                <div className="grid grid-cols-2 gap-4">
                  {selectedMapDestination.galleryImages?.map((image, index) => (
                    <motion.div
                      key={index}
                      initial={{ opacity: 0, scale: 0.9 }}
                      animate={{ opacity: 1, scale: 1 }}
                      transition={{ delay: index * 0.1 }}
                      className="relative aspect-video rounded-xl overflow-hidden group cursor-pointer"
                      onClick={() => {
                        // Open full-screen image view (you can implement this later)
                        console.log('Opening image:', index);
                      }}
                    >
                      <img
                        src={image}
                        alt={`${selectedMapDestination.name} ${index + 1}`}
                        className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-300"
                      />
                      <div className="absolute inset-0 bg-black/0 group-hover:bg-black/20 transition-colors duration-300" />
                      <div className="absolute bottom-2 right-2 bg-black/60 text-white text-xs px-2 py-1 rounded">
                        {index + 1} of {selectedMapDestination.galleryImages?.length}
                      </div>
                    </motion.div>
                  ))}
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
                  <InteractiveWorldMap
                    destinations={destinations}
                    onDestinationClick={handleMapMarkerClick}
                    highlightedDestinations={highlightedDestinations}
                  />
                </div>
              </div>

              {/* Popular Destinations */}
              <div className="flex-1 p-6 overflow-y-auto">
                <div className="space-y-6">
                  {/* Popular Tours for You - Enhanced Carousel */}
                  <div className="rounded-2xl p-6 border"
                       style={{ 
                         backgroundColor: 'var(--light-50)', 
                         borderColor: 'var(--light-300)',
                         boxShadow: '0 4px 20px rgba(35,35,35,0.08)'
                       }}>
                    <ProfessionalCarousel
                      items={[
                        { 
                          id: 'tour_1',
                          name: 'River Rafting + Paragliding Combo', 
                          title: 'River Rafting + Paragliding Combo',
                          location: 'Manali, Himachal Pradesh',
                          hero_image: 'https://images.unsplash.com/photo-1464822759844-d150baec0494?w=400&h=300&fit=crop',
                          price: '₹2,199',
                          duration: 'Full Day',
                          rating: 4.8,
                          description: 'Experience the thrill of river rafting combined with the adventure of paragliding in the beautiful valleys of Manali.',
                          category: 'Adventure'
                        },
                        { 
                          id: 'tour_2',
                          name: '8-Day Enchanting Kerala Expedition', 
                          title: '8-Day Enchanting Kerala Expedition',
                          location: 'Kerala (Kochi to Trivandrum)',
                          hero_image: 'https://images.unsplash.com/photo-1602216056096-3b40cc0c9944?w=400&h=300&fit=crop',
                          price: '₹25,999',
                          duration: '8 Days',
                          rating: 4.7,
                          description: 'Discover the backwaters, spice plantations, and cultural heritage of God\'s Own Country in this comprehensive Kerala tour.',
                          category: 'Cultural'
                        },
                        { 
                          id: 'tour_3',
                          name: '16km White Water Rafting + Camp', 
                          title: '16km White Water Rafting + Camp',
                          location: 'Rishikesh, Uttarakhand',
                          hero_image: 'https://images.unsplash.com/photo-1544551763-77ef2d0cfc6c?w=400&h=300&fit=crop',
                          price: '₹3,000',
                          duration: '2 Days',
                          rating: 4.6,
                          description: 'Challenge yourself with thrilling white water rafting followed by a night of camping under the stars.',
                          category: 'Adventure'
                        },
                        { 
                          id: 'tour_4',
                          name: 'Rajasthan Heritage & Desert Safari', 
                          title: 'Rajasthan Heritage & Desert Safari',
                          location: 'Rajasthan (Jaipur to Jaisalmer)',
                          hero_image: 'https://images.unsplash.com/photo-1477587458883-47145ed94245?w=400&h=300&fit=crop',
                          price: '₹15,999',
                          duration: '7 Days',
                          rating: 4.9,
                          description: 'Explore magnificent palaces, forts, and experience the magic of Thar Desert with camel safari.',
                          category: 'Heritage'
                        }
                      ]}
                      onAction={(action, item) => {
                        if (action === 'explore') {
                          console.log('Exploring tour:', item.name);
                          setSelectedTour(item);
                          setRightPanelContent('tour');
                        }
                      }}
                      title="Popular Tours for You"
                      itemsPerView={2}
                    />
                  </div>

                  {/* Activities for You - Enhanced Carousel */}
                  <div className="rounded-2xl p-6 border"
                       style={{ 
                         backgroundColor: 'var(--light-50)', 
                         borderColor: 'var(--light-300)',
                         boxShadow: '0 4px 20px rgba(35,35,35,0.08)'
                       }}>
                    <ProfessionalCarousel
                      items={[
                        { 
                          id: 'activity_1',
                          name: 'Paragliding in Manali', 
                          title: 'Paragliding in Manali',
                          location: 'Solang Valley, Manali',
                          hero_image: 'https://images.unsplash.com/photo-1540979388789-6cee28a1cdc9?w=400&h=300&fit=crop',
                          price: '₹3,000',
                          duration: '15 minutes',
                          rating: 4.8,
                          description: 'Soar high above the stunning Himalayas with professional paragliding instructors in Solang Valley.',
                          category: 'Adventure'
                        },
                        { 
                          id: 'activity_2',
                          name: 'Scuba Diving with Free Videography', 
                          title: 'Scuba Diving with Free Videography',
                          location: 'Pondicherry',
                          hero_image: 'https://images.unsplash.com/photo-1582719478250-c89cae4dc85b?w=400&h=300&fit=crop',
                          price: '₹6,400',
                          duration: '2 Hours',
                          rating: 4.9,
                          description: 'Explore the underwater world of Bay of Bengal with professional diving gear and free videography.',
                          category: 'Water Sports'
                        },
                        { 
                          id: 'activity_3',
                          name: 'Ganga Aarti & River Cruise', 
                          title: 'Ganga Aarti & River Cruise',
                          location: 'Varanasi, Uttar Pradesh',
                          hero_image: 'https://images.unsplash.com/photo-1561361513-2d000a50f0dc?w=400&h=300&fit=crop',
                          price: '₹1,500',
                          duration: '3 Hours',
                          rating: 4.7,
                          description: 'Witness the spiritual Ganga Aarti ceremony followed by a peaceful river cruise at sunset.',
                          category: 'Cultural'
                        },
                        { 
                          id: 'activity_4',
                          name: 'Desert Camel Safari & Folk Dance', 
                          title: 'Desert Camel Safari & Folk Dance',
                          location: 'Jaisalmer, Rajasthan',
                          hero_image: 'https://images.unsplash.com/photo-1571003123894-1f0594d2b5d9?w=400&h=300&fit=crop',
                          price: '₹2,800',
                          duration: '4 Hours',
                          rating: 4.6,
                          description: 'Experience the golden sands of Thar Desert with camel safari and traditional Rajasthani folk performances.',
                          category: 'Cultural'
                        }
                      ]}
                      onAction={(action, item) => {
                        if (action === 'explore') {
                          console.log('Exploring activity:', item.name);
                          setSelectedActivity(item);
                          setRightPanelContent('activity');
                        }
                      }}
                      title="Activities for You"
                      itemsPerView={2}
                    />
                  </div>
                </div>
              </div>
            </>
          )}
        </div>
      </div>

      {/* Trip Planner Form */}
      {showTripPlanner && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 max-w-md w-full mx-4">
            <h2 className="text-xl font-bold mb-4">Plan Your Perfect Trip</h2>
            <form onSubmit={async (e) => {
              e.preventDefault();
              setIsLoading(true);
              try {
                const formData = new FormData(e.target);
                const tripData = {
                  destination: formData.get('destination') || tripDetails.destination,
                  start_date: formData.get('start_date'),
                  end_date: formData.get('end_date'),
                  adults: parseInt(formData.get('adults')) || 2,
                  children: parseInt(formData.get('children')) || 0,
                  budget_per_night: parseInt(formData.get('budget_per_night')) || 8000,
                  session_id: sessionId
                };
                
                console.log('🎯 Submitting trip planner:', tripData);
                
                // Store trip details for later use
                setTripDetails({
                  destination: tripData.destination,
                  startDate: tripData.start_date,
                  endDate: tripData.end_date,
                  adults: tripData.adults,
                  children: tripData.children,
                  budget: tripData.budget_per_night
                });
                
                // Add chat message about moving to personalization
                const assistantMessage = {
                  id: `assistant_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
                  role: 'assistant',
                  content: `Perfect! I have all your trip details for ${tripData.destination}. Now let's personalize your experience based on your interests so I can create the perfect itinerary variants for you!`
                };
                setMessages(prev => [...prev, assistantMessage]);
                
                // Close trip planner and open personalization form
                setShowTripPlanner(false);
                setShowPersonalizationModal(true);
                console.log('🎯 Opening personalization form for:', tripData);
              } catch (error) {
                console.error('Trip planner submission failed:', error);
              } finally {
                setIsLoading(false);
              }
            }}>
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium mb-1">Destination</label>
                  <input 
                    name="destination" 
                    type="text" 
                    defaultValue={tripDetails.destination}
                    className="w-full p-2 border rounded"
                    required
                  />
                </div>
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium mb-1">Start Date</label>
                    <input 
                      name="start_date" 
                      type="date" 
                      className="w-full p-2 border rounded"
                      required
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium mb-1">End Date</label>
                    <input 
                      name="end_date" 
                      type="date" 
                      className="w-full p-2 border rounded"
                      required
                    />
                  </div>
                </div>
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium mb-1">Adults</label>
                    <input 
                      name="adults" 
                      type="number" 
                      min="1" 
                      defaultValue="2"
                      className="w-full p-2 border rounded"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium mb-1">Children</label>
                    <input 
                      name="children" 
                      type="number" 
                      min="0" 
                      defaultValue="0"
                      className="w-full p-2 border rounded"
                    />
                  </div>
                </div>
                <div>
                  <label className="block text-sm font-medium mb-1">Budget per night (₹)</label>
                  <input 
                    name="budget_per_night" 
                    type="number" 
                    min="1000" 
                    defaultValue="8000"
                    className="w-full p-2 border rounded"
                  />
                </div>
                <div className="flex gap-4 mt-6">
                  <button 
                    type="submit" 
                    disabled={isLoading}
                    className="flex-1 bg-orange-500 text-white py-2 px-4 rounded hover:bg-orange-600 disabled:opacity-50"
                  >
                    {isLoading ? 'Creating Itineraries...' : 'Create My Itineraries'}
                  </button>
                  <button 
                    type="button" 
                    onClick={() => setShowTripPlanner(false)}
                    className="px-4 py-2 border border-gray-300 rounded hover:bg-gray-50"
                  >
                    Cancel
                  </button>
                </div>
              </div>
            </form>
          </div>
        </div>
      )}

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
        onPlanTrip={handlePlanTripFromModal}
        onViewAllImages={handleViewAllImages}
      />

      {/* Sidebar */}
      <Sidebar
        isOpen={isSidebarOpen}
        onClose={() => setIsSidebarOpen(false)}
        chatHistory={chatHistory}
        onNewChat={handleNewChat}
        onSelectChat={handleSelectChat}
      />
    </div>
  );
}

export default App;