interface Project {
  name: string;
  statusColor: "blue" | "green" | "pink";
  percentage: string;
  deadline: string;
}

export default function ProjectStatus() {
  const projects: Project[] = [
    { name: "Project Alpha", statusColor: "blue", percentage: "08%", deadline: "12h" },
    { name: "Project Beta", statusColor: "green", percentage: "09%", deadline: "02h" },
    { name: "Project Gamma", statusColor: "pink", percentage: "01%", deadline: "03h" },
  ];

  const getStatusColor = (color: string) => {
    switch (color) {
      case "blue":
        return "bg-blue-500";
      case "green":
        return "bg-green-500";
      case "pink":
        return "bg-pink-500";
      default:
        return "bg-gray-500";
    }
  };

  // Donut chart calculation
  const percentage = 89;
  const radius = 50;
  const circumference = 2 * Math.PI * radius;
  const offset = circumference - (percentage / 100) * circumference;

  return (
    <div className="bg-[#1a1a1a] rounded-xl p-6 border border-[#60a5fa]/20 shadow-[0_0_15px_rgba(96,165,250,0.1)]">
      <h3 className="text-white text-lg font-semibold mb-6">Project Status</h3>
      
      {/* Donut Chart */}
      <div className="flex justify-center mb-6">
        <div className="relative w-32 h-32">
          <svg className="transform -rotate-90" width="128" height="128">
            <circle
              cx="64"
              cy="64"
              r={radius}
              fill="none"
              stroke="#2a2a2a"
              strokeWidth="12"
            />
            <circle
              cx="64"
              cy="64"
              r={radius}
              fill="none"
              stroke="#22c55e"
              strokeWidth="12"
              strokeDasharray={circumference}
              strokeDashoffset={offset}
              strokeLinecap="round"
            />
          </svg>
          <div className="absolute inset-0 flex items-center justify-center">
            <span className="text-white text-2xl font-bold">{percentage}%</span>
          </div>
        </div>
      </div>

      {/* Table */}
      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="text-gray-400 border-b border-gray-700">
              <th className="text-left pb-2">Project Name</th>
              <th className="text-left pb-2">Status</th>
              <th className="text-left pb-2">Status</th>
              <th className="text-left pb-2">Deadline</th>
            </tr>
          </thead>
          <tbody>
            {projects.map((project, index) => (
              <tr key={index} className="border-b border-gray-800">
                <td className="py-3 text-gray-300">{project.name}</td>
                <td className="py-3">
                  <div className={`w-2 h-2 rounded-full ${getStatusColor(project.statusColor)}`}></div>
                </td>
                <td className="py-3 text-gray-300">{project.percentage}</td>
                <td className="py-3 text-gray-300">{project.deadline}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

