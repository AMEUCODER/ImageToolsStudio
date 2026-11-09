import type { ReactNode } from 'react'

const Svg = ({ children, size = 20 }: { children: ReactNode; size?: number }) => (
  <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.6"
    strokeLinecap="round" strokeLinejoin="round" aria-hidden="true" focusable="false">{children}</svg>
)

/** One icon per known tool; unknown tools get a neutral grid, so a new tool folder needs no UI change. */
export function ToolIcon({ name }: { name: string }) {
  switch (name) {
    case 'blur':
      return <Svg><circle cx="12" cy="12" r="3" /><circle cx="12" cy="12" r="7.5" strokeDasharray="2 3.2" /></Svg>
    case 'auto_enhance':
      return <Svg><path d="M11 3l1.9 5.1L18 10l-5.1 1.9L11 17l-1.9-5.1L4 10l5.1-1.9z" /><path d="M18.5 15v5M16 17.5h5" /></Svg>
    case 'crop':
      return <Svg><path d="M6 3v13a2 2 0 0 0 2 2h13M3 6h13a2 2 0 0 1 2 2v13" /></Svg>
    case 'rotate_flip':
      return <Svg><path d="M4 12a8 8 0 1 0 2.6-5.9M4 4v4.5h4.5" /></Svg>
    case 'adjust':
      return <Svg><path d="M4 7h8M18 7h2M4 17h2M12 17h8" /><circle cx="15" cy="7" r="2.4" /><circle cx="9" cy="17" r="2.4" /></Svg>
    case 'watermark':
      return <Svg><rect x="3.5" y="4.5" width="17" height="15" rx="2" /><path d="M8.5 9h7M12 9v6.5" /></Svg>
    case 'face_blur':
      return <Svg><circle cx="12" cy="12" r="8" strokeDasharray="3 2.6" /><path d="M9 10.5v.4M15 10.5v.4M9.2 15c1.6 1.3 4 1.3 5.6 0" /></Svg>
    default:
      return <Svg><path d="M4 4h6.5v6.5H4zM13.5 4H20v6.5h-6.5zM4 13.5h6.5V20H4zM13.5 13.5H20V20h-6.5z" /></Svg>
  }
}

export const OpenIcon = () => <Svg><rect x="3.5" y="4.5" width="17" height="15" rx="2" /><circle cx="9" cy="10" r="1.6" /><path d="M4 17l5-4.5 3.5 3 3-2.5 4.5 4" /></Svg>
export const DownloadIcon = () => <Svg><path d="M12 4v11M7.5 11L12 15.5 16.5 11M5 20h14" /></Svg>
export const UndoIcon = () => <Svg><path d="M9 14L4 9l5-5M4 9h9.5a6 6 0 0 1 0 12H11" /></Svg>
export const CompareIcon = () => <Svg><path d="M12 3v18M7.5 8L3.5 12l4 4M16.5 8l4 4-4 4" /></Svg>
export const ResetIcon = () => <Svg><path d="M4 12a8 8 0 1 0 2.6-5.9M4 4v4.5h4.5" /></Svg>
export const InstallIcon = () => <Svg><rect x="4" y="3.5" width="16" height="17" rx="2.5" /><path d="M12 8v6M9.2 11.5L12 14.3l2.8-2.8" /></Svg>
export const KeyIcon = () => <Svg><circle cx="8" cy="15" r="3.5" /><path d="M10.5 12.5L19 4M16 7l2.5 2.5M13.5 9.5L15.5 11.5" /></Svg>
export const SunIcon = () => <Svg><circle cx="12" cy="12" r="4" /><path d="M12 3v2M12 19v2M3 12h2M19 12h2M5.6 5.6l1.4 1.4M17 17l1.4 1.4M18.4 5.6L17 7M7 17l-1.4 1.4" /></Svg>
export const MoonIcon = () => <Svg><path d="M20 14.5A8 8 0 0 1 9.5 4 8 8 0 1 0 20 14.5z" /></Svg>
export const SpinnerIcon = () => <svg className="spin" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.4" strokeLinecap="round" aria-hidden="true"><path d="M12 3a9 9 0 1 0 9 9" /></svg>

/** Half-filled circle with registration ticks. It is the logo, and the grip of the compare slider. */
export function RegistrationMark({ size = 24 }: { size?: number }) {
  return (
    <svg width={size} height={size} viewBox="0 0 64 64" fill="none" aria-hidden="true" focusable="false">
      <path d="M32 16a16 16 0 0 1 0 32z" fill="var(--accent)" />
      <circle cx="32" cy="32" r="16" stroke="currentColor" strokeWidth="4" />
      <path d="M32 4v15M32 45v15M4 32h15M45 32h15" stroke="currentColor" strokeWidth="4" strokeLinecap="round" />
    </svg>
  )
}
