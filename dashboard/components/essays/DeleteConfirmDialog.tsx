"use client";

import { X, Trash2, AlertTriangle } from 'lucide-react';
import { Essay } from '@/lib/essays/types';

interface DeleteConfirmDialogProps {
  isOpen: boolean;
  onClose: () => void;
  onConfirm: () => void;
  essay: Essay | null;
}

export default function DeleteConfirmDialog({ isOpen, onClose, onConfirm, essay }: DeleteConfirmDialogProps) {
  if (!isOpen || !essay) return null;

  const handleConfirm = () => {
    onConfirm();
    onClose();
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm">
      <div className="bg-[#1a1a1a] rounded-xl border border-red-500/20 shadow-[0_0_15px_rgba(239,68,68,0.1)] w-full max-w-md m-4">
        {/* Header */}
        <div className="flex items-center gap-3 p-6 border-b border-gray-700">
          <div className="p-2 bg-red-500/20 rounded-lg">
            <AlertTriangle size={24} className="text-red-400" />
          </div>
          <div className="flex-1">
            <h2 className="text-white text-xl font-semibold">Delete Essay</h2>
            <p className="text-gray-400 text-sm mt-1">This action cannot be undone</p>
          </div>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-white transition-colors"
            aria-label="Close dialog"
          >
            <X size={24} />
          </button>
        </div>

        {/* Content */}
        <div className="p-6">
          <p className="text-gray-300 mb-4">
            Are you sure you want to delete <span className="text-white font-semibold">"{essay.title}"</span>?
          </p>
          {essay.collegeName && (
            <p className="text-sm text-gray-400 mb-4">
              College: {essay.collegeName}
            </p>
          )}
          <p className="text-sm text-red-400">
            All content and progress will be permanently lost.
          </p>
        </div>

        {/* Actions */}
        <div className="flex items-center justify-end gap-3 p-6 border-t border-gray-700">
          <button
            onClick={onClose}
            className="px-4 py-2 text-gray-400 hover:text-white transition-colors"
          >
            Cancel
          </button>
          <button
            onClick={handleConfirm}
            className="flex items-center gap-2 bg-red-600 text-white px-4 py-2 rounded-lg hover:bg-red-700 transition-colors text-sm font-medium"
          >
            <Trash2 size={16} />
            Delete Essay
          </button>
        </div>
      </div>
    </div>
  );
}

