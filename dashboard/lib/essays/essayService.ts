import { Essay, College } from './types';
import { countWords, calculateStatus } from './utils';
import { getMockEssays } from './mockData';

const STORAGE_KEY = 'essays_data';

/**
 * Get essays from localStorage or return mock data
 */
export function loadEssays(): Essay[] {
  if (typeof window === 'undefined') {
    return getMockEssays();
  }

  try {
    const stored = localStorage.getItem(STORAGE_KEY);
    if (stored) {
      const essays = JSON.parse(stored);
      // Convert date strings back to Date objects
      return essays.map((essay: any) => ({
        ...essay,
        lastEdited: new Date(essay.lastEdited),
        createdAt: new Date(essay.createdAt),
        updatedAt: new Date(essay.updatedAt),
      }));
    }
  } catch (error) {
    console.error('Error loading essays from localStorage:', error);
  }

  // Return mock data if nothing in storage
  return getMockEssays();
}

/**
 * Save essays to localStorage
 */
export function saveEssays(essays: Essay[]): void {
  if (typeof window === 'undefined') return;

  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(essays));
  } catch (error) {
    console.error('Error saving essays to localStorage:', error);
  }
}

/**
 * Get all essays
 */
export function getAllEssays(): Essay[] {
  return loadEssays();
}

/**
 * Get general essays (essays without collegeId)
 */
export function getGeneralEssays(): Essay[] {
  return loadEssays().filter(essay => !essay.collegeId);
}

/**
 * Get college essays grouped by college
 */
export function getCollegeEssays(): College[] {
  const essays = loadEssays();
  const collegeMap = new Map<string, College>();
  
  essays
    .filter(essay => essay.collegeId)
    .forEach(essay => {
      if (!essay.collegeId || !essay.collegeName) return;
      
      if (!collegeMap.has(essay.collegeId)) {
        collegeMap.set(essay.collegeId, {
          id: essay.collegeId,
          name: essay.collegeName,
          essays: [],
        });
      }
      
      collegeMap.get(essay.collegeId)!.essays.push(essay);
    });
  
  return Array.from(collegeMap.values());
}

/**
 * Get essay by ID
 */
export function getEssayById(id: string): Essay | undefined {
  return loadEssays().find(essay => essay.id === id);
}

/**
 * Create a new essay
 */
export function createEssay(essayData: Omit<Essay, 'id' | 'wordCount' | 'status' | 'createdAt' | 'updatedAt' | 'lastEdited'>): Essay {
  const essays = loadEssays();
  const newEssay: Essay = {
    ...essayData,
    id: `essay-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
    wordCount: countWords(essayData.content),
    status: calculateStatus(countWords(essayData.content), essayData.wordLimit),
    createdAt: new Date(),
    updatedAt: new Date(),
    lastEdited: new Date(),
  };

  essays.push(newEssay);
  saveEssays(essays);
  return newEssay;
}

/**
 * Update an existing essay
 */
export function updateEssay(id: string, updates: Partial<Essay>): Essay | null {
  const essays = loadEssays();
  const index = essays.findIndex(essay => essay.id === id);
  
  if (index === -1) {
    return null;
  }

  const updatedEssay: Essay = {
    ...essays[index],
    ...updates,
    id, // Ensure ID doesn't change
    updatedAt: new Date(),
    lastEdited: new Date(),
  };

  // Recalculate word count and status if content changed
  if (updates.content !== undefined) {
    updatedEssay.wordCount = countWords(updates.content);
    updatedEssay.status = calculateStatus(updatedEssay.wordCount, updatedEssay.wordLimit);
  }

  essays[index] = updatedEssay;
  saveEssays(essays);
  return updatedEssay;
}

/**
 * Delete an essay
 */
export function deleteEssay(id: string): boolean {
  const essays = loadEssays();
  const index = essays.findIndex(essay => essay.id === id);
  
  if (index === -1) {
    return false;
  }

  essays.splice(index, 1);
  saveEssays(essays);
  return true;
}

/**
 * Add a college to the essays (creates a college entry if needed)
 */
export function addCollege(collegeName: string): string {
  const essays = loadEssays();
  const collegeId = `college-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
  
  // College will be created when first essay is added
  return collegeId;
}

