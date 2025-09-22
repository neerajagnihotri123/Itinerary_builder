import React from 'react';

const PricingBreakdown = ({ pricingData, onCheckout, isLoading = false }) => {
  if (!pricingData) return null;

  const {
    base_total,
    adjusted_total,
    final_total,
    total_savings,
    line_items = [],
    discounts_applied = [],
    demand_analysis = {},
    competitor_comparison = {},
    justification = ""
  } = pricingData;

  return (
    <div className="bg-white rounded-2xl border border-slate-200 overflow-hidden shadow-lg">
      {/* Header */}
      <div className="bg-gradient-to-r from-green-500 to-green-600 text-white p-6">
        <div className="flex items-center justify-between">
          <div>
            <h3 className="text-xl font-bold">Smart Pricing Breakdown</h3>
            <p className="text-green-100 text-sm mt-1">
              {justification || "Dynamic pricing applied based on current market conditions"}
            </p>
          </div>
          {total_savings > 0 && (
            <div className="text-right">
              <div className="text-2xl font-bold">₹{total_savings.toLocaleString()}</div>
              <div className="text-green-100 text-sm">You Save</div>
            </div>
          )}
        </div>
      </div>

      {/* Line Items */}
      <div className="p-6">
        <h4 className="font-semibold text-slate-900 mb-4">Price Components</h4>
        <div className="space-y-3">
          {line_items.map((item, index) => (
            <div key={item.id || index} className="flex items-center justify-between py-2 border-b border-slate-100">
              <div className="flex-1">
                <div className="font-medium text-slate-900">{item.title}</div>
                <div className="text-sm text-slate-600 capitalize">
                  {item.category?.replace('_', ' ')}
                  {item.demand_level && (
                    <span className={`ml-2 px-2 py-0.5 rounded-full text-xs ${
                      item.demand_level === 'high' ? 'bg-red-100 text-red-700' :
                      item.demand_level === 'low' ? 'bg-green-100 text-green-700' :
                      'bg-yellow-100 text-yellow-700'
                    }`}>
                      {item.demand_level} demand
                    </span>
                  )}
                </div>
              </div>
              <div className="text-right">
                {item.base_price !== item.current_price && (
                  <div className="text-xs text-slate-500 line-through">₹{item.base_price?.toLocaleString()}</div>
                )}
                <div className="font-semibold text-slate-900">₹{item.current_price?.toLocaleString()}</div>
              </div>
            </div>
          ))}
        </div>

        {/* Discounts */}
        {discounts_applied.length > 0 && (
          <div className="mt-6 p-4 bg-green-50 rounded-xl">
            <h5 className="font-semibold text-green-800 mb-2">Discounts Applied</h5>
            {discounts_applied.map((discount, index) => (
              <div key={index} className="flex items-center justify-between text-sm">
                <span className="text-green-700">{discount.description}</span>
                <span className="font-semibold text-green-700">-₹{discount.amount?.toLocaleString()}</span>
              </div>
            ))}
          </div>
        )}

        {/* Total Summary */}
        <div className="mt-6 pt-4 border-t border-slate-200">
          <div className="space-y-2">
            <div className="flex justify-between text-sm text-slate-600">
              <span>Subtotal</span>
              <span>₹{base_total?.toLocaleString()}</span>
            </div>
            {adjusted_total !== base_total && (
              <div className="flex justify-between text-sm text-slate-600">
                <span>Market Adjustments</span>
                <span>₹{(adjusted_total - base_total)?.toLocaleString()}</span>
              </div>
            )}
            <div className="flex justify-between text-lg font-bold text-slate-900 pt-2 border-t">
              <span>Total Amount</span>
              <span>₹{final_total?.toLocaleString()}</span>
            </div>
          </div>
        </div>

        {/* Checkout Button */}
        <button
          onClick={onCheckout}
          disabled={isLoading}
          className="w-full mt-6 bg-gradient-to-r from-orange-600 to-orange-700 text-white font-bold py-4 px-6 rounded-xl hover:from-orange-700 hover:to-orange-800 transform hover:scale-[1.02] transition-all duration-200 shadow-lg hover:shadow-xl disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {isLoading ? (
            <div className="flex items-center justify-center gap-2">
              <div className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
              Processing...
            </div>
          ) : (
            <>🚀 Proceed to Checkout</>
          )}
        </button>
      </div>
    </div>
  );
};

export default PricingBreakdown;