const API = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8001/api';
const BACKEND_URL = process.env.REACT_APP_BACKEND_URL?.replace('/api', '') || 'http://localhost:8001';

export const getProxiedImageUrl = (imageUrl) => {
  if (!imageUrl) return null;
  
  // If it's already a proxied URL, return as is
  if (imageUrl.includes('/api/image-proxy')) return imageUrl;
  
  // For external URLs that might have CORS issues, use proxy
  if (imageUrl.startsWith('http') && !imageUrl.includes(BACKEND_URL)) {
    return `${API}/image-proxy?url=${encodeURIComponent(imageUrl)}`;
  }
  
  return imageUrl;
};

// Helper function to get valid fallback images
export const getFallbackImageUrl = (category, destination) => {
  const fallbackImages = {
    // Destination-based fallbacks
    'goa': 'https://images.unsplash.com/photo-1512343879784-a960bf40e7f2?w=400&h=300&fit=crop',
    'kerala': 'https://images.unsplash.com/photo-1602216056096-3b40cc0c9944?w=400&h=300&fit=crop',
    'mumbai': 'https://images.unsplash.com/photo-1595655406003-65bb1acc49ad?w=400&h=300&fit=crop',
    'delhi': 'https://images.unsplash.com/photo-1587474260584-136574528ed5?w=400&h=300&fit=crop',
    'rajasthan': 'https://images.unsplash.com/photo-1477587458883-47145ed94245?w=400&h=300&fit=crop',
    
    // Category-based fallbacks
    'adventure': 'https://images.unsplash.com/photo-1544966503-7cc51d6d6657?w=400&h=300&fit=crop',
    'culture': 'https://images.unsplash.com/photo-1564677051169-a46a76359e41?w=400&h=300&fit=crop',
    'dining': 'https://images.unsplash.com/photo-1555396273-367ea4eb4db5?w=400&h=300&fit=crop',
    'accommodation': 'https://images.unsplash.com/photo-1564013799919-ab600027ffc6?w=400&h=300&fit=crop',
    'transport': 'https://images.unsplash.com/photo-1544620347-c4fd4a3d5957?w=400&h=300&fit=crop',
    'nature': 'https://images.unsplash.com/photo-1506905925346-21bda4d32df4?w=400&h=300&fit=crop',
    'beach': 'https://images.unsplash.com/photo-1507525428034-b723cf961d3e?w=400&h=300&fit=crop',
    'shopping': 'https://images.unsplash.com/photo-1472851294608-062f824d29cc?w=400&h=300&fit=crop',
    'nightlife': 'https://images.unsplash.com/photo-1514525253161-7a46d19cd819?w=400&h=300&fit=crop',
    
    // Default fallback
    'default': 'https://images.unsplash.com/photo-1488646953014-85cb44e25828?w=400&h=300&fit=crop'
  };
  
  // Try destination first, then category, then default
  const key = destination?.toLowerCase() || category?.toLowerCase() || 'default';
  return fallbackImages[key] || fallbackImages['default'];
};