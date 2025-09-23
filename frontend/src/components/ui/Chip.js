import React from 'react';

const Chip = ({ chip, onClick }) => (
  <button
    onClick={() => onClick(chip)}
    className="inline-flex items-center px-3 py-1.5 rounded-full text-sm font-medium transition-all duration-200 whitespace-nowrap bg-slate-100 text-slate-700 hover:bg-slate-200"
  >
    <span className="mr-2">{chip.icon}</span>
    {chip.label}
  </button>
);

export default Chip;