import { NavLink, Outlet } from "react-router-dom";
import {
  LayoutDashboard,
  Search,
  GitBranch,
} from "lucide-react";
import { useHealth, useTracingStatus, useCycleStatus } from "@/lib/hooks";

const NAV_ITEMS = [
  { to: "/dashboard", icon: LayoutDashboard, label: "Dashboard" },
  { to: "/dashboard/leads", icon: Search, label: "Leads" },
  { to: "/dashboard/pipeline", icon: GitBranch, label: "Pipeline" },
];

function StatusDot({ ok }: { ok: boolean }) {
  return (
    <span
      className={`inline-block h-2 w-2 rounded-full ${ok ? "bg-secondary" : "bg-error"}`}
    />
  );
}

export default function Layout() {
  const health = useHealth();
  const tracing = useTracingStatus();
  const cycle = useCycleStatus();

  const isHealthy = health.data?.status === "ok";
  const tracingEnabled = tracing.data?.enabled ?? false;
  const cycleStatus = cycle.data?.status ?? "idle";

  return (
    <div className="flex h-screen overflow-hidden bg-background">
      {/* Sidebar */}
      <aside className="flex w-56 flex-col border-r border-border bg-surface">
        {/* Logo */}
        <div className="flex items-center gap-3 border-b border-border px-4 py-4">
          <img src="/dashboard/logo.png" alt="Landscraper" className="h-9 w-9 rounded-lg object-cover" />
          <div>
            <h1 className="text-sm font-bold tracking-tight text-primary">Landscraper</h1>
            <p className="text-[10px] text-text-secondary">New Construction Intelligence</p>
          </div>
        </div>

        {/* Nav */}
        <nav className="flex-1 px-3 py-4 space-y-1">
          {NAV_ITEMS.map(({ to, icon: Icon, label }) => (
            <NavLink
              key={to}
              to={to}
              end={to === "/dashboard"}
              className={({ isActive }) =>
                `flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium transition-colors ${
                  isActive
                    ? "bg-primary/10 text-primary"
                    : "text-text-secondary hover:bg-surface-raised hover:text-text-primary"
                }`
              }
            >
              <Icon size={18} />
              {label}
            </NavLink>
          ))}
        </nav>

        {/* Status footer */}
        <div className="border-t border-border px-4 py-3 space-y-2">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-1.5">
              <StatusDot ok={isHealthy} />
              <span className="text-xs text-text-secondary">System</span>
            </div>
            <div className="flex items-center gap-1.5">
              <StatusDot ok={tracingEnabled} />
              <span className="text-xs text-text-secondary">Tracing</span>
            </div>
          </div>
          <div className="flex justify-center">
            <span
              className={`rounded-full px-2.5 py-0.5 text-[10px] font-semibold uppercase tracking-wide ${
                cycleStatus === "idle"
                  ? "bg-surface-raised text-text-secondary"
                  : cycleStatus === "triggered" || cycleStatus === "running"
                    ? "bg-cta/10 text-cta"
                    : cycleStatus === "completed" || cycleStatus === "complete"
                      ? "bg-secondary/10 text-secondary"
                      : "bg-error/10 text-error"
              }`}
            >
              {cycleStatus}
            </span>
          </div>
        </div>
      </aside>

      {/* Main area */}
      <div className="flex flex-1 flex-col overflow-hidden">
        <main className="flex-1 overflow-y-auto p-6">
          <Outlet />
        </main>
      </div>
    </div>
  );
}
