"use client";

import { useParams, useRouter } from 'next/navigation';
import { useEffect } from 'react';
import EssayEditor from '@/components/essays/EssayEditor';
import { useEssays } from '@/contexts/EssayContext';
import { Essay } from '@/lib/essays/types';

export default function EditEssayPage() {
  const params = useParams();
  const router = useRouter();
  const { getEssay, editEssay } = useEssays();
  const essayId = params.id as string;
  
  const essay = getEssay(essayId);

  // Redirect if essay not found
  useEffect(() => {
    if (!essay && essayId) {
      router.push('/essays');
    }
  }, [essay, essayId, router]);

  if (!essay) {
    return (
      <div className="min-h-screen bg-[#0f0f0f] flex items-center justify-center">
        <div className="text-center">
          <p className="text-gray-400 mb-4">Essay not found</p>
          <button
            onClick={() => router.push('/essays')}
            className="text-[#60a5fa] hover:text-[#3b82f6] transition-colors"
          >
            Back to Essays
          </button>
        </div>
      </div>
    );
  }

  const handleSave = (updatedEssay: Essay) => {
    const result = editEssay(essayId, updatedEssay);
    if (result) {
      // Successfully saved
      console.log('Essay saved:', result);
      // Optionally redirect back to essays list
      // router.push('/essays');
    }
  };

  return (
    <EssayEditor essay={essay} onSave={handleSave} />
  );
}

