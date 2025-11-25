import { ArrowUpRight, ArrowDownLeft, Menu } from "lucide-react";

interface StatCardProps {
  value: string;
  label: string;
  labelColor?: "green" | "blue";
  icon?: "arrow-up" | "arrow-down" | "menu" | null;
}

export default function StatCard({
  value,
  label,
  labelColor = "blue",
  icon = null,
}: StatCardProps) {
  const labelColorClass =
    labelColor === "green" ? "text-green-400" : "text-[#60a5fa]";

  const renderIcon = () => {
    if (!icon) return null;
    switch (icon) {
      case "arrow-up":
        return (
          <ArrowUpRight
            size={16}
            className="absolute bottom-3 right-3 text-gray-400"
          />
        );
      case "arrow-down":
        return (
          <ArrowDownLeft
            size={16}
            className="absolute bottom-3 right-3 text-gray-400"
          />
        );
      case "menu":
        return (
          <Menu
            size={16}
            className="absolute bottom-3 right-3 text-gray-400"
          />
        );
      default:
        return null;
    }
  };

  return (
    <div className="relative bg-[#1a1a1a] rounded-xl p-6 border border-[#60a5fa]/20 shadow-[0_0_15px_rgba(96,165,250,0.1)]">
      <div className={`text-sm ${labelColorClass} mb-2`}>{label}</div>
      <div className="text-3xl font-bold text-white">{value}</div>
      {renderIcon()}
    </div>
  );
}

