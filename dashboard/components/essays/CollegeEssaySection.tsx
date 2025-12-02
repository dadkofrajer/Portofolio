"use client";

import { useState } from 'react';
import { College } from '@/lib/essays/types';
import EssayCard from './EssayCard';
import { Building2, ChevronDown, ChevronUp, Plus } from 'lucide-react';

interface CollegeEssaySectionProps {
  college: College;
  onEdit?: (id: string) => void;
  onDelete?: (id: string) => void;
  onAdd?: (collegeId: string) => void;
}

export default function CollegeEssaySection({ 
  college, 
  onEdit, 
  onDelete, 
  onAdd 
}: CollegeEssaySectionProps) {
  const [isExpanded, setIsExpanded] = useState(true);

  const completedCount = college.essays.filter(essay => essay.status === 'complete').length;
  const totalCount = college.essays.length;

  return (
    <div className="mb-6">
      {/* College Header */}
      <div className="bg-[#1a1a1a] rounded-xl p-4 border border-[#60a5fa]/20 shadow-[0_0_15px_rgba(96,165,250,0.1)]">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3 flex-1">
            <button
              onClick={() => setIsExpanded(!isExpanded)}
              className="text-gray-400 hover:text-white transition-colors"
              aria-label={isExpanded ? 'Collapse' : 'Expand'}
            >
              {isExpanded ? <ChevronDown size={20} /> : <ChevronUp size={20} />}
            </button>
            <Building2 size={20} className="text-[#60a5fa]" />
            <div>
              <h3 className="text-white text-lg font-semibold">{college.name}</h3>
              <p className="text-sm text-gray-400">{completedCount} of {totalCount} essays complete</p>
            </div>
          </div>
          {onAdd && (
            <button
              onClick={() => onAdd(college.id)}
              className="flex items-center gap-2 bg-[#60a5fa] text-white px-4 py-2 rounded-lg hover:bg-[#3b82f6] transition-colors text-sm font-medium"
            >
              <Plus size={16} />
              Add Essay
            </button>
          )}
        </div>
      </div>

      {/* Essays List */}
      {isExpanded && (
        <div className="mt-4 space-y-4 ml-8">
          {college.essays.length === 0 ? (
            <div className="bg-[#1a1a1a] rounded-xl p-6 border border-[#60a5fa]/20 shadow-[0_0_15px_rgba(96,165,250,0.1)]">
              <p className="text-gray-400 text-center">No essays for this college yet. Click "Add Essay" to create one.</p>
            </div>
          ) : (
            college.essays.map((essay) => (
              <EssayCard
                key={essay.id}
                essay={essay}
                onEdit={onEdit}
                onDelete={onDelete}
              />
            ))
          )}
        </div>
      )}
    </div>
  );
}

