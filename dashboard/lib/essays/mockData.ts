import { Essay, College } from './types';
import { countWords, calculateStatus } from './utils';

// Helper to create dates
const createDate = (month: number, day: number, year: number): Date => {
  return new Date(year, month - 1, day);
};

// Mock essays data
const mockEssays: Essay[] = [
  // General Essays
  {
    id: 'essay-1',
    title: 'Common Application Essay',
    prompt: 'Some students have a background, identity, interest, or talent that is so meaningful they believe their application would be incomplete without it. If this sounds like you, then please share your story.',
    content: '',
    wordLimit: 650,
    wordCount: 0,
    status: 'not_started',
    lastEdited: createDate(11, 18, 2025),
    createdAt: createDate(11, 15, 2025),
    updatedAt: createDate(11, 18, 2025),
  },
  // College-specific essays
  {
    id: 'essay-2',
    title: 'Roadblock Essay',
    prompt: 'Describe a roadblock you encountered and how you overcame it.',
    content: '',
    wordLimit: 650,
    wordCount: 0,
    status: 'not_started',
    lastEdited: createDate(11, 20, 2025),
    collegeId: 'college-1',
    collegeName: 'Georgia Institute of Technology-Main Campus',
    createdAt: createDate(11, 20, 2025),
    updatedAt: createDate(11, 20, 2025),
  },
  {
    id: 'essay-3',
    title: 'Why This College',
    prompt: 'Why are you interested in attending this college?',
    content: 'I have always been fascinated by technology and innovation. This college offers the perfect combination of rigorous academics and hands-on research opportunities that align with my career goals.',
    wordLimit: 500,
    wordCount: countWords('I have always been fascinated by technology and innovation. This college offers the perfect combination of rigorous academics and hands-on research opportunities that align with my career goals.'),
    status: calculateStatus(countWords('I have always been fascinated by technology and innovation. This college offers the perfect combination of rigorous academics and hands-on research opportunities that align with my career goals.'), 500),
    lastEdited: createDate(11, 22, 2025),
    collegeId: 'college-1',
    collegeName: 'Georgia Institute of Technology-Main Campus',
    createdAt: createDate(11, 21, 2025),
    updatedAt: createDate(11, 22, 2025),
  },
  {
    id: 'essay-4',
    title: 'Academic Interest',
    prompt: 'What academic area interests you most and why?',
    content: '',
    wordLimit: 300,
    wordCount: 0,
    status: 'not_started',
    lastEdited: createDate(11, 19, 2025),
    collegeId: 'college-2',
    collegeName: 'Harvard University',
    createdAt: createDate(11, 19, 2025),
    updatedAt: createDate(11, 19, 2025),
  },
];

// Group essays by college
export function getMockEssays(): Essay[] {
  return mockEssays;
}

export function getGeneralEssays(): Essay[] {
  return mockEssays.filter(essay => !essay.collegeId);
}

export function getCollegeEssays(): College[] {
  const collegeMap = new Map<string, College>();
  
  mockEssays
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

export function getEssayById(id: string): Essay | undefined {
  return mockEssays.find(essay => essay.id === id);
}

