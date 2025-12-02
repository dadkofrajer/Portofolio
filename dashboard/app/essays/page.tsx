"use client";

import { useRouter } from "next/navigation";
import Sidebar from "@/components/Sidebar";
import GeneralEssaySection from "@/components/essays/GeneralEssaySection";
import CollegeEssaySection from "@/components/essays/CollegeEssaySection";
import { useEssays } from "@/contexts/EssayContext";
import { Building2 } from "lucide-react";

export default function EssaysPage() {
  const router = useRouter();
  const { generalEssays, collegeEssays, removeEssay, isLoading } = useEssays();

  const handleEdit = (id: string) => {
    router.push(`/essays/${id}/edit`);
  };

  const handleDelete = (id: string) => {
    if (confirm('Are you sure you want to delete this essay? This action cannot be undone.')) {
      const success = removeEssay(id);
      if (success) {
        // Essay deleted successfully
        console.log('Essay deleted:', id);
      }
    }
  };

  const handleAddGeneral = () => {
    // TODO: Implement add general essay functionality
    console.log('Add general essay');
  };

  const handleAddCollege = (collegeId: string) => {
    // TODO: Implement add college essay functionality
    console.log('Add essay for college:', collegeId);
  };

  if (isLoading) {
    return (
      <div className="flex min-h-screen bg-[#0f0f0f]">
        <Sidebar />
        <main className="flex-1 p-8 flex items-center justify-center">
          <p className="text-gray-400">Loading essays...</p>
        </main>
      </div>
    );
  }

  return (
    <div className="flex min-h-screen bg-[#0f0f0f]">
      <Sidebar />
      <main className="flex-1 p-8">
        <div className="mb-6">
          <h1 className="text-white text-2xl font-semibold mb-2">Essay Manager</h1>
          <p className="text-gray-400">Manage your college application essays</p>
        </div>

        {/* General Essays Section */}
        <GeneralEssaySection
          essays={generalEssays}
          onEdit={handleEdit}
          onDelete={handleDelete}
          onAdd={handleAddGeneral}
        />

        {/* College-Specific Essays Section */}
        <div className="mb-8">
          <div className="flex items-center gap-2 mb-4">
            <Building2 size={24} className="text-[#60a5fa]" />
            <h2 className="text-white text-xl font-semibold">College-Specific Essays</h2>
          </div>

          {collegeEssays.length === 0 ? (
            <div className="bg-[#1a1a1a] rounded-xl p-6 border border-[#60a5fa]/20 shadow-[0_0_15px_rgba(96,165,250,0.1)]">
              <p className="text-gray-400 text-center">No college-specific essays yet.</p>
            </div>
          ) : (
            <div>
              {collegeEssays.map((college) => (
                <CollegeEssaySection
                  key={college.id}
                  college={college}
                  onEdit={handleEdit}
                  onDelete={handleDelete}
                  onAdd={handleAddCollege}
                />
              ))}
            </div>
          )}
        </div>
      </main>
    </div>
  );
}

