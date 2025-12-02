import { EssayStatus } from './types';

/**
 * Count words in a text string
 */
export function countWords(text: string): number {
  if (!text || text.trim().length === 0) return 0;
  return text.trim().split(/\s+/).filter(word => word.length > 0).length;
}

/**
 * Calculate essay status based on word count and limit
 */
export function calculateStatus(wordCount: number, wordLimit: number): EssayStatus {
  if (wordCount === 0) return 'not_started';
  if (wordCount >= wordLimit * 0.9) return 'complete';
  return 'in_progress';
}

/**
 * Format date to MM/DD/YYYY format
 */
export function formatDate(date: Date): string {
  return new Intl.DateTimeFormat('en-US', {
    month: '2-digit',
    day: '2-digit',
    year: 'numeric'
  }).format(date);
}

/**
 * Get status label text
 */
export function getStatusLabel(status: EssayStatus): string {
  switch (status) {
    case 'not_started':
      return 'Not Started';
    case 'in_progress':
      return 'In Progress';
    case 'complete':
      return 'Complete';
    default:
      return 'Unknown';
  }
}

