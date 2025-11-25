"use client";

import { LayoutDashboard, BarChart3, Search, Settings, User } from "lucide-react";

interface MenuItem {
  icon: React.ReactNode;
  label: string;
  active?: boolean;
}

export default function Sidebar() {
  const menuItems: MenuItem[] = [
    { icon: <LayoutDashboard size={20} />, label: "Dashboard" },
    { icon: <BarChart3 size={20} />, label: "Analytics" },
    { icon: <Search size={20} />, label: "Projects", active: true },
    { icon: <Settings size={20} />, label: "Settings" },
    { icon: <User size={20} />, label: "Profile" },
  ];

  return (
    <div className="w-64 bg-[#1a1a1a] min-h-screen p-6">
      <nav className="space-y-2">
        {menuItems.map((item, index) => (
          <div
            key={index}
            className={`flex items-center gap-3 px-4 py-3 rounded-lg transition-colors ${
              item.active
                ? "bg-[#2a2a2a] text-white border-l-4 border-[#60a5fa]"
                : "text-gray-400 hover:text-gray-300"
            }`}
          >
            {item.icon}
            <span className="text-sm font-medium">{item.label}</span>
          </div>
        ))}
      </nav>
    </div>
  );
}

