export type EssayStatus = 'not_started' | 'in_progress' | 'complete';

export interface Essay {
  id: string;
  title: string;
  prompt: string;
  content: string;
  wordLimit: number;
  wordCount: number;
  status: EssayStatus;
  lastEdited: Date;
  collegeId?: string; // null for general essays
  collegeName?: string; // null for general essays
  googleDocUrl?: string;
  createdAt: Date;
  updatedAt: Date;
}

export interface College {
  id: string;
  name: string;
  essays: Essay[];
}

