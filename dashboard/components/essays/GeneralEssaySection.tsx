"use client";

import { Essay } from '@/lib/essays/types';
import EssayCard from './EssayCard';
import { Plus } from 'lucide-react';

interface GeneralEssaySectionProps {
  essays: Essay[];
  onEdit?: (id: string) => void;
  onDelete?: (id: string) => void;
  onAdd?: () => void;
}

export default function GeneralEssaySection({ 
  essays, 
  onEdit, 
  onDelete, 
  onAdd 
}: GeneralEssaySectionProps) {
  return (
    <div className="mb-8">
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-white text-xl font-semibold">General Essays</h2>
        {onAdd && (
          <button
            onClick={onAdd}
            className="flex items-center gap-2 bg-[#2a2a2a] text-white px-4 py-2 rounded-lg hover:bg-[#3a3a3a] transition-colors text-sm font-medium"
          >
            <Plus size={16} />
            Add Essay
          </button>
        )}
      </div>

      {essays.length === 0 ? (
        <div className="bg-[#1a1a1a] rounded-xl p-6 border border-[#60a5fa]/20 shadow-[0_0_15px_rgba(96,165,250,0.1)]">
          <p className="text-gray-400 text-center">No general essays yet. Click "Add Essay" to create one.</p>
        </div>
      ) : (
        <div className="space-y-4">
          {essays.map((essay) => (
            <EssayCard
              key={essay.id}
              essay={essay}
              onEdit={onEdit}
              onDelete={onDelete}
            />
          ))}
        </div>
      )}
    </div>
  );
}

