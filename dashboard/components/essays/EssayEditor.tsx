"use client";

import { useState, useEffect, useCallback, useRef } from 'react';
import { Essay } from '@/lib/essays/types';
import { countWords, calculateStatus } from '@/lib/essays/utils';
import { ArrowLeft, Save, Link as LinkIcon } from 'lucide-react';
import { useRouter } from 'next/navigation';

interface EssayEditorProps {
  essay: Essay;
  onSave?: (updatedEssay: Essay) => void;
}

export default function EssayEditor({ essay: initialEssay, onSave }: EssayEditorProps) {
  const router = useRouter();
  const [essay, setEssay] = useState<Essay>(initialEssay);
  const [wordCount, setWordCount] = useState(essay.wordCount);
  const [isSaving, setIsSaving] = useState(false);
  const [lastSaved, setLastSaved] = useState<Date | null>(null);
  const [hasUnsavedChanges, setHasUnsavedChanges] = useState(false);
  const autoSaveTimerRef = useRef<NodeJS.Timeout | null>(null);

  // Update word count when content changes
  useEffect(() => {
    const count = countWords(essay.content);
    setWordCount(count);
    
    // Auto-update status based on word count
    const newStatus = calculateStatus(count, essay.wordLimit);
    if (newStatus !== essay.status) {
      setEssay(prev => ({ ...prev, status: newStatus }));
    }
  }, [essay.content, essay.wordLimit, essay.status]);

  const performSave = useCallback(async (isAutoSave = false) => {
    if (isSaving) return; // Prevent multiple simultaneous saves
    
    setIsSaving(true);
    
    // Update word count and status
    const currentContent = essay.content;
    const finalWordCount = countWords(currentContent);
    const finalStatus = calculateStatus(finalWordCount, essay.wordLimit);
    
    const updatedEssay: Essay = {
      ...essay,
      wordCount: finalWordCount,
      status: finalStatus,
      updatedAt: new Date(),
      lastEdited: new Date(),
    };

    if (onSave) {
      onSave(updatedEssay);
    } else {
      // TODO: Save to API or local storage
      console.log('Saving essay:', updatedEssay);
    }

    // Simulate save delay for better UX
    await new Promise(resolve => setTimeout(resolve, 300));
    setIsSaving(false);
    setHasUnsavedChanges(false);
    setLastSaved(new Date());
  }, [essay, onSave, isSaving]);

  // Auto-save functionality - debounced save after user stops typing
  useEffect(() => {
    if (!hasUnsavedChanges) return;

    // Clear existing timer
    if (autoSaveTimerRef.current) {
      clearTimeout(autoSaveTimerRef.current);
    }

    // Set new timer
    autoSaveTimerRef.current = setTimeout(() => {
      performSave(true); // true = auto-save
    }, 2000); // Auto-save 2 seconds after user stops typing

    return () => {
      if (autoSaveTimerRef.current) {
        clearTimeout(autoSaveTimerRef.current);
      }
    };
  }, [essay.content, essay.googleDocUrl, hasUnsavedChanges, performSave]);

  const handleContentChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    const newContent = e.target.value;
    setEssay(prev => ({
      ...prev,
      content: newContent,
      updatedAt: new Date(),
      lastEdited: new Date(),
    }));
    setHasUnsavedChanges(true);
  };

  const handleGoogleDocChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setEssay(prev => ({
      ...prev,
      googleDocUrl: e.target.value,
      updatedAt: new Date(),
    }));
    setHasUnsavedChanges(true);
  };

  const handleSave = () => {
    performSave(false); // Manual save
  };

  const handleBack = () => {
    router.push('/essays');
  };

  const formatLastSaved = (date: Date): string => {
    const seconds = Math.floor((new Date().getTime() - date.getTime()) / 1000);
    if (seconds < 60) return 'just now';
    if (seconds < 3600) return `${Math.floor(seconds / 60)}m ago`;
    if (seconds < 86400) return `${Math.floor(seconds / 3600)}h ago`;
    return date.toLocaleDateString();
  };

  const isOverLimit = wordCount > essay.wordLimit;
  const wordCountColor = isOverLimit ? 'text-red-400' : wordCount >= essay.wordLimit * 0.9 ? 'text-green-400' : 'text-gray-300';

  return (
    <div className="min-h-screen bg-[#0f0f0f]">
      {/* Header */}
      <div className="bg-[#1a1a1a] border-b border-[#60a5fa]/20 p-6">
        <div className="max-w-4xl mx-auto">
          <div className="flex items-center justify-between mb-4">
            <button
              onClick={handleBack}
              className="flex items-center gap-2 text-gray-400 hover:text-white transition-colors"
            >
              <ArrowLeft size={20} />
              <span>Back to Essays</span>
            </button>
            <div className="flex items-center gap-4">
              {hasUnsavedChanges && !isSaving && (
                <span className="text-sm text-gray-400">Unsaved changes</span>
              )}
              {isSaving && (
                <span className="text-sm text-[#60a5fa]">Saving...</span>
              )}
              {lastSaved && !hasUnsavedChanges && !isSaving && (
                <span className="text-sm text-green-400">
                  Saved {formatLastSaved(lastSaved)}
                </span>
              )}
              <button
                onClick={handleSave}
                disabled={isSaving}
                className={`flex items-center gap-2 px-4 py-2 rounded-lg transition-colors text-sm font-medium ${
                  isSaving
                    ? 'bg-gray-600 text-gray-400 cursor-not-allowed'
                    : 'bg-[#60a5fa] text-white hover:bg-[#3b82f6]'
                }`}
              >
                <Save size={16} />
                {isSaving ? 'Saving...' : 'Save'}
              </button>
            </div>
          </div>

          <h1 className="text-white text-2xl font-semibold mb-2">{essay.title}</h1>
          <p className="text-gray-300 mb-4">{essay.prompt}</p>
          
          <div className="flex items-center gap-6 text-sm text-gray-400">
            <span>Word Limit: {essay.wordLimit}</span>
            <span className={wordCountColor}>Word Count: {wordCount}</span>
            {isOverLimit && (
              <span className="text-red-400 font-medium">
                Over limit by {wordCount - essay.wordLimit} words
              </span>
            )}
            {essay.collegeName && (
              <span>College: {essay.collegeName}</span>
            )}
          </div>
        </div>
      </div>

      {/* Editor Content */}
      <div className="max-w-4xl mx-auto p-6">
        {/* Google Doc Link Section */}
        <div className="bg-[#1a1a1a] rounded-xl p-6 border border-[#60a5fa]/20 shadow-[0_0_15px_rgba(96,165,250,0.1)] mb-6">
          <div className="flex items-center gap-2 mb-3">
            <LinkIcon size={20} className="text-[#60a5fa]" />
            <h3 className="text-white text-lg font-semibold">Google Doc Link</h3>
          </div>
          <input
            type="url"
            value={essay.googleDocUrl || ''}
            onChange={handleGoogleDocChange}
            placeholder="https://docs.google.com/document/d/..."
            className="w-full bg-[#0f0f0f] border border-gray-700 rounded-lg px-4 py-2 text-gray-300 placeholder-gray-500 focus:outline-none focus:border-[#60a5fa] transition-colors"
          />
          <p className="text-sm text-gray-400 mt-2">
            Link your Google Doc to sync your essay content
          </p>
        </div>

        {/* Text Editor */}
        <div className="bg-[#1a1a1a] rounded-xl p-6 border border-[#60a5fa]/20 shadow-[0_0_15px_rgba(96,165,250,0.1)]">
          <h3 className="text-white text-lg font-semibold mb-4">Essay Content</h3>
          <textarea
            value={essay.content}
            onChange={handleContentChange}
            placeholder="Start writing your essay here..."
            className={`w-full h-[600px] bg-[#0f0f0f] border rounded-lg px-4 py-3 text-gray-300 placeholder-gray-500 focus:outline-none transition-colors resize-none ${
              isOverLimit
                ? 'border-red-500 focus:border-red-400'
                : 'border-gray-700 focus:border-[#60a5fa]'
            }`}
            style={{ fontFamily: 'inherit', fontSize: '16px', lineHeight: '1.6' }}
          />
          
          {/* Word Count Footer */}
          <div className="mt-4 flex items-center justify-between text-sm">
            <div className="flex items-center gap-4">
              <span className={wordCountColor}>
                {wordCount} / {essay.wordLimit} words
              </span>
              {wordCount >= essay.wordLimit * 0.9 && wordCount <= essay.wordLimit && (
                <span className="text-green-400">✓ Within limit</span>
              )}
            </div>
            <span className="text-gray-400">
              Last edited: {new Intl.DateTimeFormat('en-US', {
                month: '2-digit',
                day: '2-digit',
                year: 'numeric',
                hour: '2-digit',
                minute: '2-digit'
              }).format(essay.lastEdited)}
            </span>
          </div>
        </div>

        {/* AI Features Placeholder */}
        <div className="bg-[#1a1a1a] rounded-xl p-6 border border-[#60a5fa]/20 shadow-[0_0_15px_rgba(96,165,250,0.1)] mt-6">
          <h3 className="text-white text-lg font-semibold mb-2">AI Features</h3>
          <p className="text-gray-400 text-sm">
            AI-powered feedback and suggestions will be available here in a future update.
          </p>
        </div>
      </div>
    </div>
  );
}

