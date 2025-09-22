import React from 'react';

const ConflictWarnings = ({ conflicts, warnings, onResolve }) => {
  if (!conflicts?.length && !warnings?.length) return null;

  return (
    <div className="bg-yellow-50 border border-yellow-200 rounded-xl p-4 mb-4">
      <div className="flex items-center gap-2 mb-3">
        <span className="text-yellow-600">⚠️</span>
        <h3 className="font-semibold text-yellow-800">Itinerary Issues Detected</h3>
      </div>
      
      {conflicts?.length > 0 && (
        <div className="mb-3">
          <h4 className="font-medium text-red-700 mb-2">Conflicts ({conflicts.length})</h4>
          {conflicts.slice(0, 3).map((conflict, index) => (
            <div key={index} className="bg-red-50 border-l-4 border-l-red-400 p-2 mb-2">
              <p className="text-sm text-red-700">{conflict.message}</p>
              {conflict.suggestion && (
                <p className="text-xs text-red-600 mt-1">💡 {conflict.suggestion}</p>
              )}
            </div>
          ))}
        </div>
      )}
      
      {warnings?.length > 0 && (
        <div className="mb-3">
          <h4 className="font-medium text-yellow-700 mb-2">Warnings ({warnings.length})</h4>
          {warnings.slice(0, 2).map((warning, index) => (
            <div key={index} className="bg-yellow-50 border-l-4 border-l-yellow-400 p-2 mb-2">
              <p className="text-sm text-yellow-700">{warning.message}</p>
              {warning.suggestion && (
                <p className="text-xs text-yellow-600 mt-1">💡 {warning.suggestion}</p>
              )}
            </div>
          ))}
        </div>
      )}
      
      <button
        onClick={onResolve}
        className="bg-orange-500 text-white px-4 py-2 rounded-lg text-sm hover:bg-orange-600 transition-colors"
      >
        Auto-Resolve Issues
      </button>
    </div>
  );
};

export default ConflictWarnings;