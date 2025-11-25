# Design System Reference Guide

This document provides a quick reference for maintaining UI consistency across the application.

## Quick Start

Import the design system in your components:

```tsx
import { componentPatterns, colors, typography, commonClasses } from '@/design-system';
```

## Color Palette

### Primary Colors
- **Background**: `#0f0f0f` - Main page background
- **Foreground**: `#ededed` - Main text color
- **Card Background**: `#1a1a1a` - Cards, sidebars, containers
- **Card Hover**: `#2a2a2a` - Hover states

### Accent Colors
- **Accent Blue**: `#60a5fa` - Primary accent color
- **Blue Border**: `rgba(96, 165, 250, 0.2)` - 20% opacity for borders
- **Blue Glow**: `rgba(96, 165, 250, 0.1)` - Shadow glow effect

### Status Colors
- **Green**: `#22c55e` - Success/positive status
- **Blue**: `#3b82f6` - Info/neutral status
- **Pink**: `#ec4899` - Warning/special status

### Text Colors
- **Primary**: `#ffffff` (white) - Main headings
- **Secondary**: `#d1d5db` (gray-300) - Body text
- **Tertiary**: `#9ca3af` (gray-400) - Labels, secondary text
- **Muted**: `#6b7280` (gray-500) - Disabled/muted text

## Typography

### Font Sizes
- `text-xs`: 12px
- `text-sm`: 14px (labels, small text)
- `text-base`: 16px (default)
- `text-lg`: 18px (section headings)
- `text-xl`: 20px (page headings)
- `text-2xl`: 24px
- `text-3xl`: 30px (large values/numbers)

### Font Weights
- `font-normal`: 400
- `font-medium`: 500
- `font-semibold`: 600 (headings)
- `font-bold`: 700 (large values)

### Common Text Styles
```tsx
// Heading
className="text-white text-lg font-semibold"

// Large Heading
className="text-white text-xl font-semibold"

// Body Text
className="text-gray-300"

// Secondary Text
className="text-gray-400"

// Label
className="text-sm text-gray-400"

// Large Value
className="text-3xl font-bold text-white"
```

## Spacing

### Padding
- `p-2`: 8px
- `p-3`: 12px
- `p-4`: 16px
- `p-6`: 24px (standard for cards)
- `p-8`: 32px (main content area)

### Margin
- `m-2`: 8px
- `m-4`: 16px
- `m-6`: 24px (section spacing)

### Gap
- `gap-2`: 8px
- `gap-3`: 12px
- `gap-4`: 16px
- `gap-6`: 24px (standard for grids)

## Border Radius

- `rounded-sm`: 2px
- `rounded-md`: 6px
- `rounded-lg`: 8px
- `rounded-xl`: 12px (standard for cards)
- `rounded-full`: 9999px (circular)

## Shadows & Effects

### Card Shadow
```tsx
className="shadow-[0_0_15px_rgba(96,165,250,0.1)]"
```

### Card Border
```tsx
className="border border-[#60a5fa]/20"
```

### Complete Card Style
```tsx
className="bg-[#1a1a1a] rounded-xl p-6 border border-[#60a5fa]/20 shadow-[0_0_15px_rgba(96,165,250,0.1)]"
```

## Component Patterns

### Card Component
```tsx
<div className="bg-[#1a1a1a] rounded-xl p-6 border border-[#60a5fa]/20 shadow-[0_0_15px_rgba(96,165,250,0.1)]">
  <h3 className="text-white text-lg font-semibold mb-4">Card Title</h3>
  <div className="text-gray-300">Card content</div>
</div>
```

### Stat Card
```tsx
<div className="relative bg-[#1a1a1a] rounded-xl p-6 border border-[#60a5fa]/20 shadow-[0_0_15px_rgba(96,165,250,0.1)]">
  <div className="text-sm text-[#60a5fa] mb-2">Label</div>
  <div className="text-3xl font-bold text-white">Value</div>
  <Icon size={16} className="absolute bottom-3 right-3 text-gray-400" />
</div>
```

### Sidebar Navigation Item
```tsx
// Active
<div className="flex items-center gap-3 px-4 py-3 rounded-lg bg-[#2a2a2a] text-white border-l-4 border-[#60a5fa]">
  <Icon size={20} />
  <span className="text-sm font-medium">Label</span>
</div>

// Inactive
<div className="flex items-center gap-3 px-4 py-3 rounded-lg text-gray-400 hover:text-gray-300 transition-colors">
  <Icon size={20} />
  <span className="text-sm font-medium">Label</span>
</div>
```

### Table
```tsx
<div className="overflow-x-auto">
  <table className="w-full text-sm">
    <thead>
      <tr className="text-gray-400 border-b border-gray-700">
        <th className="text-left pb-2">Header</th>
      </tr>
    </thead>
    <tbody>
      <tr className="border-b border-gray-800">
        <td className="py-3 text-gray-300">Content</td>
      </tr>
    </tbody>
  </table>
</div>
```

## Layout Patterns

### Main Layout
```tsx
<div className="flex min-h-screen bg-[#0f0f0f]">
  <Sidebar />
  <main className="flex-1 p-8">
    {/* Content */}
  </main>
</div>
```

### Grid Layouts
```tsx
// Stat Cards Grid (1 col mobile, 2 col tablet, 4 col desktop)
<div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
  {/* Cards */}
</div>

// Two Column Grid (1 col mobile, 2 col desktop)
<div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
  {/* Cards */}
</div>
```

## Icon Sizes

- **Small**: 16px - Used in stat cards, small indicators
- **Medium**: 20px - Used in sidebar navigation
- **Large**: 24px - Used in buttons, headers
- **Extra Large**: 32px - Used for prominent icons

## Status Colors

### Usage in Components
```tsx
// Blue Status
<div className="w-2 h-2 rounded-full bg-blue-500"></div>

// Green Status
<div className="w-2 h-2 rounded-full bg-green-500"></div>

// Pink Status
<div className="w-2 h-2 rounded-full bg-pink-500"></div>
```

### Text Colors
```tsx
// Blue Text
className="text-[#60a5fa]"

// Green Text
className="text-green-400"
```

## Common Class Combinations

### Text
- Primary: `text-white`
- Secondary: `text-gray-300`
- Tertiary: `text-gray-400`
- Muted: `text-gray-500`

### Backgrounds
- Primary: `bg-[#0f0f0f]`
- Card: `bg-[#1a1a1a]`
- Card Hover: `bg-[#2a2a2a]`

### Borders
- Card Border: `border border-[#60a5fa]/20`
- Divider: `border-b border-gray-700`
- Light Divider: `border-b border-gray-800`

### Transitions
- Colors: `transition-colors`
- All: `transition-all`

## Breakpoints

- **sm**: 640px
- **md**: 768px
- **lg**: 1024px
- **xl**: 1280px
- **2xl**: 1536px

## Best Practices

1. **Always use the card pattern** for containers: `bg-[#1a1a1a] rounded-xl p-6 border border-[#60a5fa]/20 shadow-[0_0_15px_rgba(96,165,250,0.1)]`

2. **Consistent spacing**: Use `gap-6` for grids, `p-6` for card padding, `mb-6` for sections

3. **Text hierarchy**: Use `text-white` for headings, `text-gray-300` for body, `text-gray-400` for labels

4. **Icons**: Use lucide-react icons with consistent sizes (16px for small, 20px for medium)

5. **Hover states**: Always include `transition-colors` for interactive elements

6. **Responsive design**: Use Tailwind's responsive prefixes (`md:`, `lg:`) for breakpoints

## Example: Building a New Page

```tsx
import { componentPatterns } from '@/design-system';
import { SomeIcon } from 'lucide-react';

export default function NewPage() {
  return (
    <div className="flex min-h-screen bg-[#0f0f0f]">
      <Sidebar />
      <main className="flex-1 p-8">
        {/* Section */}
        <div className="mb-6">
          <h2 className="text-white text-xl font-semibold mb-4">Section Title</h2>
          
          {/* Grid */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            {/* Cards */}
            <div className={componentPatterns.card.base}>
              <h3 className={componentPatterns.card.header}>Card Title</h3>
              <p className={componentPatterns.card.content}>Card content</p>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}
```

