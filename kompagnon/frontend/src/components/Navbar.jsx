import React from 'react';
import { Link } from 'react-router-dom';
import { BeakerIcon } from '@heroicons/react/24/outline';

export default function Navbar() {
  return (
    <nav className="bg-kompagnon-900 text-white shadow-lg">
      <div className="max-w-7xl mx-auto px-4 py-4 flex items-center justify-between">
        <Link to="/" className="flex items-center gap-2 text-xl font-bold">
          <BeakerIcon className="w-6 h-6" />
          KOMPAGNON
        </Link>
        <div className="text-sm text-kompagnon-100">
          Automation System v1.0
        </div>
      </div>
    </nav>
  );
}
