"use client";

import { useState } from 'react';
import { X, Plus } from 'lucide-react';
import { Essay } from '@/lib/essays/types';

interface CreateEssayModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSubmit: (essayData: Omit<Essay, 'id' | 'wordCount' | 'status' | 'createdAt' | 'updatedAt' | 'lastEdited'>) => void;
  collegeId?: string;
  collegeName?: string;
}

export default function CreateEssayModal({ isOpen, onClose, onSubmit, collegeId, collegeName }: CreateEssayModalProps) {
  const [title, setTitle] = useState('');
  const [prompt, setPrompt] = useState('');
  const [wordLimit, setWordLimit] = useState(650);
  const [content, setContent] = useState('');
  const [googleDocUrl, setGoogleDocUrl] = useState('');

  if (!isOpen) return null;

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!title.trim() || !prompt.trim()) {
      alert('Please fill in the title and prompt fields.');
      return;
    }

    onSubmit({
      title: title.trim(),
      prompt: prompt.trim(),
      content: content.trim(),
      wordLimit: Number(wordLimit) || 650,
      collegeId: collegeId,
      collegeName: collegeName,
      googleDocUrl: googleDocUrl.trim() || undefined,
    });

    // Reset form
    setTitle('');
    setPrompt('');
    setWordLimit(650);
    setContent('');
    setGoogleDocUrl('');
    onClose();
  };

  const handleClose = () => {
    // Reset form on close
    setTitle('');
    setPrompt('');
    setWordLimit(650);
    setContent('');
    setGoogleDocUrl('');
    onClose();
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm">
      <div className="bg-[#1a1a1a] rounded-xl border border-[#60a5fa]/20 shadow-[0_0_15px_rgba(96,165,250,0.1)] w-full max-w-2xl max-h-[90vh] overflow-y-auto m-4">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-gray-700">
          <h2 className="text-white text-xl font-semibold">
            {collegeName ? `Add Essay for ${collegeName}` : 'Create New Essay'}
          </h2>
          <button
            onClick={handleClose}
            className="text-gray-400 hover:text-white transition-colors"
            aria-label="Close modal"
          >
            <X size={24} />
          </button>
        </div>

        {/* Form */}
        <form onSubmit={handleSubmit} className="p-6 space-y-4">
          {/* Title */}
          <div>
            <label htmlFor="title" className="block text-sm font-medium text-gray-300 mb-2">
              Essay Title *
            </label>
            <input
              type="text"
              id="title"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              placeholder="e.g., Common Application Essay"
              className="w-full bg-[#0f0f0f] border border-gray-700 rounded-lg px-4 py-2 text-gray-300 placeholder-gray-500 focus:outline-none focus:border-[#60a5fa] transition-colors"
              required
            />
          </div>

          {/* Prompt */}
          <div>
            <label htmlFor="prompt" className="block text-sm font-medium text-gray-300 mb-2">
              Essay Prompt *
            </label>
            <textarea
              id="prompt"
              value={prompt}
              onChange={(e) => setPrompt(e.target.value)}
              placeholder="Enter the essay prompt or question..."
              rows={4}
              className="w-full bg-[#0f0f0f] border border-gray-700 rounded-lg px-4 py-2 text-gray-300 placeholder-gray-500 focus:outline-none focus:border-[#60a5fa] transition-colors resize-none"
              required
            />
          </div>

          {/* Word Limit */}
          <div>
            <label htmlFor="wordLimit" className="block text-sm font-medium text-gray-300 mb-2">
              Word Limit
            </label>
            <input
              type="number"
              id="wordLimit"
              value={wordLimit}
              onChange={(e) => setWordLimit(Number(e.target.value) || 650)}
              min="1"
              className="w-full bg-[#0f0f0f] border border-gray-700 rounded-lg px-4 py-2 text-gray-300 placeholder-gray-500 focus:outline-none focus:border-[#60a5fa] transition-colors"
            />
          </div>

          {/* Google Doc URL */}
          <div>
            <label htmlFor="googleDocUrl" className="block text-sm font-medium text-gray-300 mb-2">
              Google Doc URL (Optional)
            </label>
            <input
              type="url"
              id="googleDocUrl"
              value={googleDocUrl}
              onChange={(e) => setGoogleDocUrl(e.target.value)}
              placeholder="https://docs.google.com/document/d/..."
              className="w-full bg-[#0f0f0f] border border-gray-700 rounded-lg px-4 py-2 text-gray-300 placeholder-gray-500 focus:outline-none focus:border-[#60a5fa] transition-colors"
            />
          </div>

          {/* Initial Content (Optional) */}
          <div>
            <label htmlFor="content" className="block text-sm font-medium text-gray-300 mb-2">
              Initial Content (Optional)
            </label>
            <textarea
              id="content"
              value={content}
              onChange={(e) => setContent(e.target.value)}
              placeholder="Start writing your essay here (optional)..."
              rows={6}
              className="w-full bg-[#0f0f0f] border border-gray-700 rounded-lg px-4 py-2 text-gray-300 placeholder-gray-500 focus:outline-none focus:border-[#60a5fa] transition-colors resize-none"
            />
          </div>

          {/* Actions */}
          <div className="flex items-center justify-end gap-3 pt-4 border-t border-gray-700">
            <button
              type="button"
              onClick={handleClose}
              className="px-4 py-2 text-gray-400 hover:text-white transition-colors"
            >
              Cancel
            </button>
            <button
              type="submit"
              className="flex items-center gap-2 bg-[#60a5fa] text-white px-4 py-2 rounded-lg hover:bg-[#3b82f6] transition-colors text-sm font-medium"
            >
              <Plus size={16} />
              Create Essay
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

