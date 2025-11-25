/**
 * UI Design System Reference
 * 
 * This file contains all design tokens, patterns, and utilities
 * to maintain visual consistency across the application.
 * 
 * Import this file or reference it when building new pages/components.
 */

// ============================================================================
// COLOR PALETTE
// ============================================================================

export const colors = {
  // Primary Colors
  background: "#0f0f0f",        // Main background
  foreground: "#ededed",        // Main text color
  cardBg: "#1a1a1a",            // Card/sidebar background
  cardBgHover: "#2a2a2a",       // Hover state for cards/nav items
  
  // Accent Colors
  accentBlue: "#60a5fa",        // Primary accent (blue)
  accentBlueLight: "rgba(96, 165, 250, 0.2)",  // Blue with 20% opacity for borders
  accentBlueGlow: "rgba(96, 165, 250, 0.1)",   // Blue glow for shadows
  
  // Status Colors
  green: "#22c55e",             // Success/green status
  greenText: "#22c55e",         // Green text (e.g., text-green-400)
  blue: "#3b82f6",              // Blue status (e.g., bg-blue-500)
  pink: "#ec4899",              // Pink status (e.g., bg-pink-500)
  
  // Text Colors
  textPrimary: "#ffffff",       // Primary text (white)
  textSecondary: "#d1d5db",     // Secondary text (gray-300)
  textTertiary: "#9ca3af",      // Tertiary text (gray-400)
  textMuted: "#6b7280",         // Muted text (gray-500)
  
  // Border Colors
  borderPrimary: "#374151",     // Primary border (gray-700)
  borderSecondary: "#1f2937",   // Secondary border (gray-800)
  borderDark: "#333333",        // Dark border for charts/grids
  
  // Chart Colors (from MonthlyGrowthChart)
  chartCyan: "#00ffff",
  chartGreen: "#00ff00",
  chartMagenta: "#ff00ff",
  chartPurple: "#8000ff",
} as const;

// ============================================================================
// TYPOGRAPHY
// ============================================================================

export const typography = {
  // Font Families
  fontSans: "Arial, Helvetica, sans-serif",
  fontMono: "var(--font-geist-mono)",
  
  // Font Sizes
  sizes: {
    xs: "0.75rem",      // 12px - text-xs
    sm: "0.875rem",     // 14px - text-sm
    base: "1rem",       // 16px - text-base
    lg: "1.125rem",     // 18px - text-lg
    xl: "1.25rem",      // 20px - text-xl
    "2xl": "1.5rem",    // 24px - text-2xl
    "3xl": "1.875rem",  // 30px - text-3xl
  },
  
  // Font Weights
  weights: {
    normal: "400",
    medium: "500",
    semibold: "600",
    bold: "700",
  },
  
  // Common Text Styles
  styles: {
    heading: "text-white text-lg font-semibold",
    headingLarge: "text-white text-xl font-semibold",
    headingSmall: "text-white text-base font-semibold",
    body: "text-gray-300",
    bodySecondary: "text-gray-400",
    label: "text-sm text-gray-400",
    value: "text-3xl font-bold text-white",
  },
} as const;

// ============================================================================
// SPACING
// ============================================================================

export const spacing = {
  // Padding
  p2: "0.5rem",    // 8px - p-2
  p3: "0.75rem",   // 12px - p-3
  p4: "1rem",      // 16px - p-4
  p6: "1.5rem",    // 24px - p-6 (most common for cards)
  p8: "2rem",      // 32px - p-8 (main content padding)
  
  // Margin
  m2: "0.5rem",    // 8px - m-2
  m4: "1rem",      // 16px - m-4
  m6: "1.5rem",    // 24px - m-6
  
  // Gap
  gap2: "0.5rem",  // 8px - gap-2
  gap3: "0.75rem", // 12px - gap-3
  gap4: "1rem",    // 16px - gap-4
  gap6: "1.5rem",  // 24px - gap-6 (most common for grids)
  
  // Common Spacing Patterns
  cardPadding: "p-6",
  sectionSpacing: "mb-6",
  gridGap: "gap-6",
} as const;

// ============================================================================
// BORDER RADIUS
// ============================================================================

export const borderRadius = {
  sm: "0.125rem",   // 2px - rounded-sm
  md: "0.375rem",   // 6px - rounded-md
  lg: "0.5rem",     // 8px - rounded-lg
  xl: "0.75rem",    // 12px - rounded-xl (most common for cards)
  full: "9999px",   // rounded-full
} as const;

// ============================================================================
// SHADOWS & EFFECTS
// ============================================================================

export const shadows = {
  // Card Shadow (blue glow effect)
  cardGlow: "shadow-[0_0_15px_rgba(96,165,250,0.1)]",
  
  // Border with blue accent
  cardBorder: "border border-[#60a5fa]/20",
  
  // Common Card Style Combination
  cardStyle: "bg-[#1a1a1a] rounded-xl p-6 border border-[#60a5fa]/20 shadow-[0_0_15px_rgba(96,165,250,0.1)]",
} as const;

// ============================================================================
// COMPONENT PATTERNS
// ============================================================================

export const componentPatterns = {
  // Card Component
  card: {
    base: "bg-[#1a1a1a] rounded-xl p-6 border border-[#60a5fa]/20 shadow-[0_0_15px_rgba(96,165,250,0.1)]",
    header: "text-white text-lg font-semibold mb-4",
    content: "text-gray-300",
  },
  
  // Stat Card
  statCard: {
    container: "relative bg-[#1a1a1a] rounded-xl p-6 border border-[#60a5fa]/20 shadow-[0_0_15px_rgba(96,165,250,0.1)]",
    label: "text-sm mb-2",
    value: "text-3xl font-bold text-white",
    icon: "absolute bottom-3 right-3 text-gray-400",
  },
  
  // Sidebar Navigation
  sidebar: {
    container: "w-64 bg-[#1a1a1a] min-h-screen p-6",
    navItem: "flex items-center gap-3 px-4 py-3 rounded-lg transition-colors",
    navItemActive: "bg-[#2a2a2a] text-white border-l-4 border-[#60a5fa]",
    navItemInactive: "text-gray-400 hover:text-gray-300",
  },
  
  // Table
  table: {
    container: "overflow-x-auto",
    table: "w-full text-sm",
    thead: "text-gray-400 border-b border-gray-700",
    th: "text-left pb-2",
    tbody: "border-b border-gray-800",
    td: "py-3 text-gray-300",
  },
  
  // Button (if needed)
  button: {
    primary: "bg-[#60a5fa] text-white px-4 py-2 rounded-lg hover:bg-[#3b82f6] transition-colors",
    secondary: "bg-[#2a2a2a] text-white px-4 py-2 rounded-lg hover:bg-[#3a3a3a] transition-colors",
  },
  
  // Main Layout
  layout: {
    container: "flex min-h-screen bg-[#0f0f0f]",
    main: "flex-1 p-8",
    section: "mb-6",
  },
  
  // Grid Layouts
  grid: {
    statCards: "grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6",
    twoColumn: "grid grid-cols-1 lg:grid-cols-2 gap-6",
  },
} as const;

// ============================================================================
// ICON SIZES
// ============================================================================

export const iconSizes = {
  sm: 16,   // Small icons (e.g., in stat cards)
  md: 20,   // Medium icons (e.g., in sidebar)
  lg: 24,   // Large icons
  xl: 32,   // Extra large icons
} as const;

// ============================================================================
// STATUS COLORS
// ============================================================================

export const statusColors = {
  blue: {
    bg: "bg-blue-500",
    text: "text-[#60a5fa]",
    border: "border-blue-500",
  },
  green: {
    bg: "bg-green-500",
    text: "text-green-400",
    border: "border-green-500",
  },
  pink: {
    bg: "bg-pink-500",
    text: "text-pink-400",
    border: "border-pink-500",
  },
} as const;

// ============================================================================
// UTILITY FUNCTIONS
// ============================================================================

/**
 * Get status color classes based on status type
 */
export function getStatusColor(status: "blue" | "green" | "pink") {
  return statusColors[status];
}

/**
 * Get label color class for stat cards
 */
export function getLabelColor(color: "green" | "blue") {
  return color === "green" ? "text-green-400" : "text-[#60a5fa]";
}

// ============================================================================
// COMMON CLASS COMBINATIONS
// ============================================================================

export const commonClasses = {
  // Text
  textPrimary: "text-white",
  textSecondary: "text-gray-300",
  textTertiary: "text-gray-400",
  textMuted: "text-gray-500",
  
  // Backgrounds
  bgPrimary: "bg-[#0f0f0f]",
  bgCard: "bg-[#1a1a1a]",
  bgCardHover: "bg-[#2a2a2a]",
  
  // Borders
  borderCard: "border border-[#60a5fa]/20",
  borderDivider: "border-b border-gray-700",
  borderDividerLight: "border-b border-gray-800",
  
  // Transitions
  transition: "transition-colors",
  transitionAll: "transition-all",
  
  // Common Spacing
  spacingCard: "p-6",
  spacingSection: "mb-6",
  spacingGrid: "gap-6",
} as const;

// ============================================================================
// BREAKPOINTS (Tailwind defaults)
// ============================================================================

export const breakpoints = {
  sm: "640px",   // @media (min-width: 640px)
  md: "768px",   // @media (min-width: 768px)
  lg: "1024px",  // @media (min-width: 1024px)
  xl: "1280px",  // @media (min-width: 1280px)
  "2xl": "1536px", // @media (min-width: 1536px)
} as const;

// ============================================================================
// EXPORT SUMMARY
// ============================================================================

/**
 * Quick Reference:
 * 
 * Colors: colors.background, colors.accentBlue, colors.cardBg, etc.
 * Typography: typography.styles.heading, typography.sizes.lg, etc.
 * Spacing: spacing.p6, spacing.gap6, etc.
 * Components: componentPatterns.card.base, componentPatterns.statCard.container, etc.
 * Common Classes: commonClasses.textPrimary, commonClasses.bgCard, etc.
 * 
 * Example Usage:
 * ```tsx
 * import { componentPatterns, colors, typography } from '@/design-system';
 * 
 * <div className={componentPatterns.card.base}>
 *   <h3 className={componentPatterns.card.header}>Title</h3>
 *   <p className={componentPatterns.card.content}>Content</p>
 * </div>
 * ```
 */

