"use client";

import { Essay } from '@/lib/essays/types';
import { formatDate } from '@/lib/essays/utils';
import { Pencil, Trash2 } from 'lucide-react';
import StatusBadge from './StatusBadge';
import { useRouter } from 'next/navigation';

interface EssayCardProps {
  essay: Essay;
  onEdit?: (id: string) => void;
  onDelete?: (id: string) => void;
}

export default function EssayCard({ essay, onEdit, onDelete }: EssayCardProps) {
  const router = useRouter();

  const handleEdit = () => {
    if (onEdit) {
      onEdit(essay.id);
    } else {
      router.push(`/essays/${essay.id}/edit`);
    }
  };

  const handleDelete = () => {
    if (onDelete) {
      onDelete(essay.id);
    }
  };

  return (
    <div className="bg-[#1a1a1a] rounded-xl p-6 border border-[#60a5fa]/20 shadow-[0_0_15px_rgba(96,165,250,0.1)] hover:bg-[#2a2a2a] transition-colors">
      <div className="mb-4">
        <h3 className="text-white text-lg font-semibold mb-2">{essay.title}</h3>
        <p className="text-gray-300 text-sm mb-4 line-clamp-2">{essay.prompt}</p>
      </div>

      <div className="flex items-center gap-4 mb-4 text-sm text-gray-400">
        <span>Word Limit: {essay.wordLimit}</span>
        <span>Word Count: {essay.wordCount}</span>
        <span>Last edited: {formatDate(essay.lastEdited)}</span>
      </div>

      <div className="flex items-center justify-between">
        <StatusBadge status={essay.status} />
        <div className="flex items-center gap-2">
          <button
            onClick={handleEdit}
            className="flex items-center gap-2 bg-[#60a5fa] text-white px-4 py-2 rounded-lg hover:bg-[#3b82f6] transition-colors text-sm font-medium"
          >
            <Pencil size={16} />
            Edit
          </button>
          {onDelete && (
            <button
              onClick={handleDelete}
              className="flex items-center gap-2 bg-red-600 text-white px-4 py-2 rounded-lg hover:bg-red-700 transition-colors text-sm font-medium"
              aria-label="Delete essay"
            >
              <Trash2 size={16} />
              Delete
            </button>
          )}
        </div>
      </div>
    </div>
  );
}

