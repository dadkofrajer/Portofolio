"use client";

import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';
import { Essay, College } from '@/lib/essays/types';
import {
  getAllEssays,
  getGeneralEssays,
  getCollegeEssays,
  getEssayById,
  createEssay,
  updateEssay,
  deleteEssay,
  saveEssays,
} from '@/lib/essays/essayService';

interface EssayContextType {
  // State
  essays: Essay[];
  generalEssays: Essay[];
  collegeEssays: College[];
  isLoading: boolean;

  // Actions
  refreshEssays: () => void;
  getEssay: (id: string) => Essay | undefined;
  addEssay: (essayData: Omit<Essay, 'id' | 'wordCount' | 'status' | 'createdAt' | 'updatedAt' | 'lastEdited'>) => Essay;
  editEssay: (id: string, updates: Partial<Essay>) => Essay | null;
  removeEssay: (id: string) => boolean;
}

const EssayContext = createContext<EssayContextType | undefined>(undefined);

export function EssayProvider({ children }: { children: React.ReactNode }) {
  const [essays, setEssays] = useState<Essay[]>([]);
  const [generalEssays, setGeneralEssays] = useState<Essay[]>([]);
  const [collegeEssays, setCollegeEssays] = useState<College[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  const refreshEssays = useCallback(() => {
    setIsLoading(true);
    try {
      const allEssays = getAllEssays();
      setEssays(allEssays);
      setGeneralEssays(getGeneralEssays());
      setCollegeEssays(getCollegeEssays());
    } catch (error) {
      console.error('Error refreshing essays:', error);
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    refreshEssays();
  }, [refreshEssays]);

  const getEssay = useCallback((id: string): Essay | undefined => {
    return getEssayById(id);
  }, []);

  const addEssay = useCallback((essayData: Omit<Essay, 'id' | 'wordCount' | 'status' | 'createdAt' | 'updatedAt' | 'lastEdited'>): Essay => {
    const newEssay = createEssay(essayData);
    refreshEssays();
    return newEssay;
  }, [refreshEssays]);

  const editEssay = useCallback((id: string, updates: Partial<Essay>): Essay | null => {
    const updated = updateEssay(id, updates);
    if (updated) {
      refreshEssays();
    }
    return updated;
  }, [refreshEssays]);

  const removeEssay = useCallback((id: string): boolean => {
    const success = deleteEssay(id);
    if (success) {
      refreshEssays();
    }
    return success;
  }, [refreshEssays]);

  const value: EssayContextType = {
    essays,
    generalEssays,
    collegeEssays,
    isLoading,
    refreshEssays,
    getEssay,
    addEssay,
    editEssay,
    removeEssay,
  };

  return (
    <EssayContext.Provider value={value}>
      {children}
    </EssayContext.Provider>
  );
}

export function useEssays() {
  const context = useContext(EssayContext);
  if (context === undefined) {
    throw new Error('useEssays must be used within an EssayProvider');
  }
  return context;
}

