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
      className={`inline-block h-2 w-2 rounded-full ${ok ? "bg-primary" : "bg-error"}`}
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
    <div className="flex h-screen overflow-hidden">
      {/* Sidebar */}
      <aside className="flex w-16 flex-col items-center gap-4 border-r border-border bg-surface py-4">
        <div className="mb-4 text-xl font-bold text-primary">L</div>
        {NAV_ITEMS.map(({ to, icon: Icon, label }) => (
          <NavLink
            key={to}
            to={to}
            end={to === "/dashboard"}
            className={({ isActive }) =>
              `flex h-10 w-10 items-center justify-center rounded-lg transition-colors ${
                isActive
                  ? "bg-primary/10 text-primary"
                  : "text-text-secondary hover:bg-border hover:text-text-primary"
              }`
            }
            title={label}
          >
            <Icon size={20} />
          </NavLink>
        ))}
      </aside>

      {/* Main area */}
      <div className="flex flex-1 flex-col overflow-hidden">
        {/* Top bar */}
        <header className="flex h-12 items-center justify-between border-b border-border bg-surface px-6">
          <h1 className="text-sm font-semibold tracking-wide text-text-secondary uppercase">
            Landscraper
          </h1>
          <div className="flex items-center gap-4 text-xs">
            <div className="flex items-center gap-1.5">
              <StatusDot ok={isHealthy} />
              <span className="text-text-secondary">System</span>
            </div>
            <div className="flex items-center gap-1.5">
              <StatusDot ok={tracingEnabled} />
              <span className="text-text-secondary">Tracing</span>
            </div>
            <div
              className={`rounded-full px-2.5 py-0.5 text-xs font-medium ${
                cycleStatus === "idle"
                  ? "bg-border text-text-secondary"
                  : cycleStatus === "triggered"
                    ? "bg-primary/20 text-primary"
                    : "bg-hot/20 text-hot"
              }`}
            >
              {cycleStatus}
            </div>
          </div>
        </header>

        {/* Content */}
        <main className="flex-1 overflow-y-auto p-6">
          <Outlet />
        </main>
      </div>
    </div>
  );
}
