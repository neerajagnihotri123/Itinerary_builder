import React, { useState } from 'react';
import { X } from 'lucide-react';

const CheckoutModal = ({ isOpen, onClose, cartData, onPayment }) => {
  const [paymentMethod, setPaymentMethod] = useState('card');
  const [isProcessing, setIsProcessing] = useState(false);

  const handlePayment = async () => {
    setIsProcessing(true);
    try {
      await onPayment(paymentMethod);
    } finally {
      setIsProcessing(false);
    }
  };

  if (!isOpen || !cartData) return null;

  return (
    <div className="fixed inset-0 bg-black/70 backdrop-blur-sm z-[90] flex items-center justify-center p-4">
      <div className="bg-white rounded-2xl max-w-2xl w-full max-h-[90vh] overflow-y-auto">
        {/* Header */}
        <div className="p-6 border-b border-slate-200">
          <div className="flex items-center justify-between">
            <h2 className="text-2xl font-bold text-slate-900">Checkout</h2>
            <button onClick={onClose} className="p-2 hover:bg-slate-100 rounded-lg">
              <X className="w-5 h-5 text-slate-600" />
            </button>
          </div>
        </div>

        <div className="p-6">
          {/* Order Summary */}
          <div className="mb-6">
            <h3 className="font-semibold text-slate-900 mb-3">Order Summary</h3>
            <div className="bg-slate-50 rounded-xl p-4">
              <div className="flex justify-between items-center mb-2">
                <span className="text-slate-600">Trip Duration</span>
                <span className="font-medium">{cartData.itinerary_summary?.total_days} days</span>
              </div>
              <div className="flex justify-between items-center mb-2">
                <span className="text-slate-600">Total Activities</span>
                <span className="font-medium">{cartData.itinerary_summary?.total_activities}</span>
              </div>
              <div className="flex justify-between items-center mb-4">
                <span className="text-slate-600">Destinations</span>
                <span className="font-medium">{cartData.itinerary_summary?.destinations?.length}</span>
              </div>
              <div className="border-t border-slate-200 pt-4">
                <div className="flex justify-between items-center text-lg font-bold">
                  <span>Total Amount</span>
                  <span>₹{cartData.payment_summary?.total?.toLocaleString()}</span>
                </div>
              </div>
            </div>
          </div>

          {/* Payment Method */}
          <div className="mb-6">
            <h3 className="font-semibold text-slate-900 mb-3">Payment Method</h3>
            <div className="space-y-3">
              {[
                { id: 'card', label: 'Credit/Debit Card', icon: '💳' },
                { id: 'upi', label: 'UPI Payment', icon: '📱' },
                { id: 'netbanking', label: 'Net Banking', icon: '🏦' },
                { id: 'wallet', label: 'Digital Wallet', icon: '👛' }
              ].map((method) => (
                <label key={method.id} className="flex items-center p-3 border border-slate-200 rounded-lg cursor-pointer hover:bg-slate-50">
                  <input
                    type="radio"
                    name="paymentMethod"
                    value={method.id}
                    checked={paymentMethod === method.id}
                    onChange={(e) => setPaymentMethod(e.target.value)}
                    className="mr-3"
                  />
                  <span className="mr-2">{method.icon}</span>
                  <span className="font-medium">{method.label}</span>
                </label>
              ))}
            </div>
          </div>

          {/* Terms */}
          <div className="mb-6 p-4 bg-yellow-50 rounded-xl">
            <p className="text-sm text-yellow-800">
              <strong>Note:</strong> This is a demo checkout. No actual payment will be processed. 
              You'll receive booking confirmations for testing purposes.
            </p>
          </div>

          {/* Action Buttons */}
          <div className="flex gap-4">
            <button
              onClick={onClose}
              className="flex-1 px-6 py-3 border border-slate-300 text-slate-700 font-semibold rounded-xl hover:bg-slate-50 transition-colors"
            >
              Cancel
            </button>
            <button
              onClick={handlePayment}
              disabled={isProcessing}
              className="flex-1 px-6 py-3 bg-gradient-to-r from-green-600 to-green-700 text-white font-semibold rounded-xl hover:from-green-700 hover:to-green-800 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {isProcessing ? (
                <div className="flex items-center justify-center gap-2">
                  <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
                  Processing...
                </div>
              ) : (
                `Pay ₹${cartData.payment_summary?.total?.toLocaleString()}`
              )}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default CheckoutModal;