import React, { useState, useEffect } from 'react';
import { getProxiedImageUrl, getFallbackImageUrl } from '../../utils/imageUtils';

const SafeImage = ({ src, alt, className, onError, category, destination, ...props }) => {
  const [currentSrc, setCurrentSrc] = useState(getProxiedImageUrl(src));
  const [hasError, setHasError] = useState(false);
  
  useEffect(() => {
    setCurrentSrc(getProxiedImageUrl(src));
    setHasError(false);
  }, [src]);
  
  const handleError = (e) => {
    if (!hasError) {
      setHasError(true);
      // Use proper fallback image
      setCurrentSrc(getFallbackImageUrl(category, destination));
    }
    if (onError) onError(e);
  };
  
  return (
    <img
      src={currentSrc}
      alt={alt}
      className={className}
      onError={handleError}
      {...props}
    />
  );
};

export default SafeImage;