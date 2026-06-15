/**
 * Auth layout — bypasses AppShell so sign-in / sign-up
 * render as full-page screens with no sidebar or topbar.
 */
export default function AuthLayout({ children }: { children: React.ReactNode }) {
  return <>{children}</>;
}
