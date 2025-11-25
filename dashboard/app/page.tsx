import Sidebar from "@/components/Sidebar";
import StatCard from "@/components/StatCard";
import MonthlyGrowthChart from "@/components/MonthlyGrowthChart";
import ProjectStatus from "@/components/ProjectStatus";

export default function Home() {
  return (
    <div className="flex min-h-screen bg-[#0f0f0f]">
      <Sidebar />
      <main className="flex-1 p-8">
        <div className="mb-6">
          <h2 className="text-white text-xl font-semibold mb-4">Stat Cards</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            <StatCard
              value="98,765"
              label="Total Users"
              labelColor="green"
            />
            <StatCard
              value="645"
              label="Total"
              labelColor="blue"
              icon="arrow-up"
            />
            <StatCard
              value="$1.2M"
              label="Revenue"
              labelColor="blue"
              icon="arrow-down"
            />
            <StatCard
              value="$12"
              label="Revenue"
              labelColor="blue"
              icon="menu"
            />
          </div>
        </div>
        
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <MonthlyGrowthChart />
          <ProjectStatus />
        </div>
      </main>
    </div>
  );
}
