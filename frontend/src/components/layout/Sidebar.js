import React from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { X, Plus, MessageCircle } from 'lucide-react';

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

export default Sidebar;