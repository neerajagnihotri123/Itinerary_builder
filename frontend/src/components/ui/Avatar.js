import React from 'react';
import { motion } from 'framer-motion';
import { Plane } from 'lucide-react';

const Avatar = () => (
  <motion.div
    className="w-12 h-12 rounded-full flex items-center justify-center shadow-lg"
    style={{ 
      background: 'linear-gradient(135deg, var(--primary-500) 0%, var(--primary-600) 100%)',
      boxShadow: '0 8px 24px rgba(230, 149, 67, 0.4)'
    }}
  >
    <Plane className="w-6 h-6" style={{ color: 'var(--light-50)' }} />
  </motion.div>
);

export default Avatar;