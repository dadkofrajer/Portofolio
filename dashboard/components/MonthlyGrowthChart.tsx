export default function MonthlyGrowthChart() {
  // Sample data points for the 4 lines
  const line1 = [
    { x: 200, y: 20 },
    { x: 300, y: 45 },
    { x: 400, y: 35 },
    { x: 500, y: 60 },
    { x: 600, y: 55 },
  ];

  const line2 = [
    { x: 200, y: 30 },
    { x: 300, y: 50 },
    { x: 400, y: 70 },
    { x: 500, y: 65 },
    { x: 600, y: 80 },
  ];

  const line3 = [
    { x: 200, y: 15 },
    { x: 300, y: 25 },
    { x: 400, y: 40 },
    { x: 500, y: 50 },
    { x: 600, y: 45 },
  ];

  const line4 = [
    { x: 200, y: 40 },
    { x: 300, y: 35 },
    { x: 400, y: 50 },
    { x: 500, y: 75 },
    { x: 600, y: 90 },
  ];

  // Convert to SVG coordinates (assuming 400x200 viewBox)
  const width = 400;
  const height = 200;
  const padding = 40;
  const chartWidth = width - padding * 2;
  const chartHeight = height - padding * 2;

  const scaleX = (x: number) => {
    const minX = 200;
    const maxX = 600;
    return padding + ((x - minX) / (maxX - minX)) * chartWidth;
  };

  const scaleY = (y: number) => {
    const minY = 0;
    const maxY = 110;
    return height - padding - (y / maxY) * chartHeight;
  };

  const createPath = (points: { x: number; y: number }[]) => {
    return points
      .map((point, i) => `${i === 0 ? "M" : "L"} ${scaleX(point.x)} ${scaleY(point.y)}`)
      .join(" ");
  };

  return (
    <div className="bg-[#1a1a1a] rounded-xl p-6 border border-[#60a5fa]/20 shadow-[0_0_15px_rgba(96,165,250,0.1)]">
      <h3 className="text-white text-lg font-semibold mb-4">Monthly Growth</h3>
      <div className="w-full h-64">
        <svg
          viewBox="0 0 400 200"
          className="w-full h-full"
          preserveAspectRatio="xMidYMid meet"
        >
          {/* Grid lines */}
          {[0, 20, 40, 60, 80, 100, 110].map((y) => (
            <line
              key={y}
              x1={padding}
              y1={scaleY(y)}
              x2={width - padding}
              y2={scaleY(y)}
              stroke="#333"
              strokeWidth="0.5"
            />
          ))}
          {[200, 300, 400, 500, 600].map((x) => (
            <line
              key={x}
              x1={scaleX(x)}
              y1={padding}
              x2={scaleX(x)}
              y2={height - padding}
              stroke="#333"
              strokeWidth="0.5"
            />
          ))}

          {/* Y-axis labels */}
          {[0, 20, 40, 60, 80, 100, 110].map((y) => (
            <text
              key={y}
              x={padding - 10}
              y={scaleY(y) + 4}
              fill="#666"
              fontSize="10"
              textAnchor="end"
            >
              {y}
            </text>
          ))}

          {/* X-axis labels */}
          {[200, 300, 400, 500, 600].map((x) => (
            <text
              key={x}
              x={scaleX(x)}
              y={height - padding + 20}
              fill="#666"
              fontSize="10"
              textAnchor="middle"
            >
              {x}
            </text>
          ))}

          {/* Lines */}
          <path
            d={createPath(line1)}
            fill="none"
            stroke="#00ffff"
            strokeWidth="2"
          />
          <path
            d={createPath(line2)}
            fill="none"
            stroke="#00ff00"
            strokeWidth="2"
          />
          <path
            d={createPath(line3)}
            fill="none"
            stroke="#ff00ff"
            strokeWidth="2"
          />
          <path
            d={createPath(line4)}
            fill="none"
            stroke="#8000ff"
            strokeWidth="2"
          />
        </svg>
      </div>
    </div>
  );
}

