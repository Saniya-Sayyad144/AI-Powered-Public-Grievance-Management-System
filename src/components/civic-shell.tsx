import { useEffect, useState, type ReactNode } from "react";
import { Link, useNavigate, useRouterState } from "@tanstack/react-router";
import {
  Bell,
  ChevronDown,
  ClipboardList,
  FileText,
  LayoutDashboard,
  LogOut,
  Menu,
  MessageSquareText,
  Settings,
  ShieldCheck,
  UserRound,
  X,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { civicApi, type CivicRole } from "@/lib/civic-api";
import { useCivic } from "./civic-context";

const labels: Record<CivicRole, string> = {
  citizen: "Citizen",
  admin: "Administrator",
  officer: "Field Officer",
};
const dashboards: Record<CivicRole, "/citizen" | "/admin" | "/officer"> = {
  citizen: "/citizen",
  admin: "/admin",
  officer: "/officer",
};
const links = [
  {
    label: "Overview",
    icon: LayoutDashboard,
    key: "dashboard",
    roles: ["citizen", "admin", "officer"],
  },
  { label: "My complaints", icon: FileText, to: "/complaints", roles: ["citizen"] },
  { label: "All complaints", icon: ClipboardList, to: "/complaints", roles: ["admin"] },
  { label: "Assigned to me", icon: ClipboardList, to: "/complaints", roles: ["officer"] },
  {
    label: "Notifications",
    icon: Bell,
    to: "/notifications",
    roles: ["citizen", "admin", "officer"],
  },
  { label: "Feedback", icon: MessageSquareText, to: "/feedback", roles: ["citizen"] },
  {
    label: "Profile settings",
    icon: Settings,
    to: "/profile",
    roles: ["citizen", "admin", "officer"],
  },
] as const;

export function CivicShell({ children }: { children: ReactNode }) {
  const { role, user, loading, notifications, notificationItems, setUser } = useCivic();
  const [open, setOpen] = useState(false);
  const [signingOut, setSigningOut] = useState(false);
  const pathname = useRouterState({ select: (state) => state.location.pathname });
  const navigate = useNavigate();

  useEffect(() => {
    if (loading) return;
    if (!user) {
      void navigate({ to: "/login" });
      return;
    }
    const requestedRole =
      pathname === "/admin"
        ? "admin"
        : pathname === "/officer"
          ? "officer"
          : pathname === "/citizen"
            ? "citizen"
            : null;
    if (requestedRole && requestedRole !== role) void navigate({ to: dashboards[role] });
  }, [loading, navigate, pathname, role, user]);

  async function signOut() {
    setSigningOut(true);
    await civicApi.logout().catch(() => undefined);
    try {
      setUser(null);
      setSigningOut(false);
      await navigate({ to: "/login" });
    } finally {
      setSigningOut(false);
    }
  }

  if (loading || !user)
    return (
      <main className="grid min-h-screen place-items-center text-sm text-muted-foreground">
        {loading ? "Loading your CivicPulse account…" : "Redirecting to sign in…"}
      </main>
    );

  return (
    <div className="min-h-screen bg-background">
      {open && (
        <button
          aria-label="Close menu"
          onClick={() => setOpen(false)}
          className="fixed inset-0 z-30 bg-foreground/30 lg:hidden"
        />
      )}
      <aside
        className={`fixed inset-y-0 left-0 z-40 flex w-64 flex-col bg-nav text-nav-foreground transition-transform lg:translate-x-0 ${open ? "translate-x-0" : "-translate-x-full"}`}
      >
        <div className="flex h-18 items-center gap-3 border-b border-nav-foreground/10 px-5">
          <div className="grid size-9 place-items-center rounded-lg bg-brand">
            <ShieldCheck className="size-5" />
          </div>
          <div>
            <b className="font-display">CivicPulse AI</b>
            <p className="text-[9px] tracking-[.12em] text-nav-muted">SMARTER CIVIC RESPONSE</p>
          </div>
          <Button
            variant="ghost"
            size="icon"
            className="ml-auto text-nav-muted lg:hidden"
            onClick={() => setOpen(false)}
          >
            <X />
          </Button>
        </div>
        <div className="px-3 py-5">
          <p className="mb-2 px-3 text-[10px] font-bold tracking-[.14em] text-nav-muted">
            {labels[role].toUpperCase()} PORTAL
          </p>
          <nav className="space-y-1">
            {links
              .filter((item) => (item.roles as readonly string[]).includes(role))
              .map((item) => {
                const to = "key" in item ? dashboards[role] : item.to;
                const active = pathname === to;
                return (
                  <Link
                    key={item.label}
                    to={to}
                    onClick={() => setOpen(false)}
                    className={`flex items-center gap-3 rounded-md px-3 py-2.5 text-sm ${active ? "bg-nav-foreground/12" : "text-nav-muted hover:bg-nav-foreground/7 hover:text-nav-foreground"}`}
                  >
                    <item.icon className="size-4" />
                    {item.label}
                    {item.label === "Notifications" && notifications > 0 && (
                      <span className="ml-auto rounded-full bg-coral px-1.5 text-[9px] text-primary-foreground">
                        {notifications}
                      </span>
                    )}
                  </Link>
                );
              })}
          </nav>
        </div>
        <div className="mt-auto border-t border-nav-foreground/10 p-4">
          <div className="flex items-center gap-3 rounded-md bg-nav-foreground/8 p-3">
            <div className="grid size-8 place-items-center rounded-full bg-brand font-bold">
              {user.name
                .split(/\s+/)
                .map((part) => part[0])
                .slice(0, 2)
                .join("")
                .toUpperCase()}
            </div>
            <div className="min-w-0">
              <p className="truncate text-xs font-bold">{user.name}</p>
              <p className="text-[10px] text-nav-muted">{labels[role]}</p>
            </div>
          </div>
          <button
            disabled={signingOut}
            onClick={() => void signOut()}
            className="mt-3 flex items-center gap-2 px-2 text-xs text-nav-muted disabled:opacity-60"
          >
            <LogOut className="size-3" />
            {signingOut ? "Signing out…" : "Sign out"}
          </button>
        </div>
      </aside>
      <div className="lg:pl-64">
        <header className="sticky top-0 z-20 flex h-18 items-center border-b bg-background/92 px-4 backdrop-blur sm:px-6">
          <Button variant="ghost" size="icon" className="lg:hidden" onClick={() => setOpen(true)}>
            <Menu />
          </Button>
          <div className="ml-auto flex items-center gap-2">
            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <Button variant="outline" size="icon" className="relative">
                  <Bell />
                  {notifications > 0 && (
                    <span className="absolute -right-1 -top-1 grid size-4 place-items-center rounded-full bg-coral text-[9px] text-primary-foreground">
                      {notifications}
                    </span>
                  )}
                </Button>
              </DropdownMenuTrigger>
              <DropdownMenuContent align="end" className="w-80">
                <DropdownMenuLabel>Recent notifications</DropdownMenuLabel>
                <DropdownMenuSeparator />
                {notificationItems.length ? (
                  notificationItems.slice(0, 5).map((item) => (
                    <DropdownMenuItem key={item.id} asChild>
                      {item.complaint_id ? (
                        <Link
                          to="/complaints/$complaintId"
                          params={{ complaintId: item.complaint_id }}
                        >
                          <span className="block min-w-0">
                            <span className="block truncate text-xs font-semibold">
                              {item.title}
                            </span>
                            <span className="block truncate text-[10px] text-muted-foreground">
                              {item.message}
                            </span>
                          </span>
                        </Link>
                      ) : (
                        <Link to="/notifications">{item.message}</Link>
                      )}
                    </DropdownMenuItem>
                  ))
                ) : (
                  <DropdownMenuItem disabled>No notifications</DropdownMenuItem>
                )}
              </DropdownMenuContent>
            </DropdownMenu>
            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <Button variant="ghost">
                  <UserRound />
                  <span className="hidden sm:inline">{labels[role]}</span>
                  <ChevronDown />
                </Button>
              </DropdownMenuTrigger>
              <DropdownMenuContent align="end">
                <DropdownMenuLabel>{user.name}</DropdownMenuLabel>
                <DropdownMenuItem asChild>
                  <Link to="/profile">Account settings</Link>
                </DropdownMenuItem>
              </DropdownMenuContent>
            </DropdownMenu>
          </div>
        </header>
        <main className="mx-auto max-w-[1500px] p-4 sm:p-6 lg:p-8">{children}</main>
      </div>
    </div>
  );
}
