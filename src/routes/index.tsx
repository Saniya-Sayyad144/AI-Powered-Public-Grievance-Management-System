import { createFileRoute, Link } from "@tanstack/react-router";
import {
  ArrowRight,
  BrainCircuit,
  CheckCircle2,
  Construction,
  Droplets,
  Lamp,
  Menu,
  ShieldCheck,
  Trash2,
  Waves,
} from "lucide-react";
import { Button } from "@/components/ui/button";
export const Route = createFileRoute("/")({
  head: () => ({
    meta: [
      { title: "CivicPulse AI — Public Grievance Portal" },
      {
        name: "description",
        content:
          "Report, track, and resolve civic grievances with transparent AI-assisted workflows.",
      },
      { property: "og:title", content: "CivicPulse AI — Public Grievance Portal" },
      {
        property: "og:description",
        content:
          "Report, track, and resolve civic grievances with transparent AI-assisted workflows.",
      },
      { property: "og:type", content: "website" },
      { name: "twitter:card", content: "summary_large_image" },
    ],
  }),
  component: Landing,
});
const cats = [
  { name: "Roads", text: "Potholes, damaged roads", icon: Construction },
  { name: "Garbage", text: "Collection and dumping", icon: Trash2 },
  { name: "Water supply", text: "Leaks and quality", icon: Droplets },
  { name: "Drainage", text: "Blockages and flooding", icon: Waves },
  { name: "Streetlights", text: "Outages and damage", icon: Lamp },
];
function Landing() {
  return (
    <main className="min-h-screen bg-background">
      <header className="border-b bg-panel">
        <div className="mx-auto flex h-18 max-w-7xl items-center px-4 sm:px-6">
          <Link to="/" className="flex items-center gap-3">
            <span className="grid size-9 place-items-center rounded-lg bg-nav text-primary-foreground">
              <ShieldCheck className="size-5" />
            </span>
            <div>
              <b className="font-display">CivicPulse AI</b>
              <p className="text-[9px] tracking-[.12em] text-muted-foreground">
                SMARTER CIVIC RESPONSE
              </p>
            </div>
          </Link>
          <nav className="ml-auto hidden items-center gap-6 text-sm font-semibold md:flex">
            <a href="#how">How it works</a>
            <a href="#categories">Categories</a>
            <Link to="/track">Track complaint</Link>
            <Link to="/login" className="rounded-md border px-4 py-2">
              Sign in
            </Link>
          </nav>
          <Button variant="ghost" size="icon" className="ml-auto md:hidden">
            <Menu />
          </Button>
        </div>
      </header>
      <section className="overflow-hidden border-b bg-nav text-nav-foreground">
        <div className="mx-auto grid max-w-7xl items-center gap-10 px-4 py-16 sm:px-6 lg:grid-cols-[1.15fr_.85fr] lg:py-24">
          <div>
            <span className="inline-flex items-center gap-2 rounded-full border border-nav-foreground/15 px-3 py-1.5 text-xs text-nav-muted">
              <BrainCircuit className="size-3 text-brand" />
              AI-assisted civic services
            </span>
            <h1 className="mt-6 max-w-3xl font-display text-4xl font-bold leading-[1.08] sm:text-6xl">
              Your voice.
              <br />
              <span className="text-brand">A better city.</span>
            </h1>
            <p className="mt-5 max-w-xl text-base leading-7 text-nav-muted">
              Report civic problems in minutes, follow every action, and help local teams resolve
              what matters—faster and transparently.
            </p>
            <div className="mt-8 flex flex-wrap gap-3">
              <Link
                to="/report"
                className="inline-flex h-11 items-center gap-2 rounded-md bg-brand px-5 text-sm font-bold text-primary-foreground"
              >
                Report a complaint <ArrowRight className="size-4" />
              </Link>
              <Link
                to="/track"
                className="inline-flex h-11 items-center rounded-md border border-nav-foreground/20 px-5 text-sm font-bold"
              >
                Track complaint
              </Link>
            </div>
            <div className="mt-10 flex flex-wrap gap-6 text-xs text-nav-muted">
              <span>
                <CheckCircle2 className="mr-2 inline size-4 text-status-done" />
                Transparent tracking
              </span>
              <span>
                <CheckCircle2 className="mr-2 inline size-4 text-status-done" />
                Smart department routing
              </span>
              <span>
                <CheckCircle2 className="mr-2 inline size-4 text-status-done" />
                Verified resolutions
              </span>
            </div>
          </div>
          <div className="panel rounded-xl p-5 text-foreground">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-[10px] font-bold text-primary">LIVE CITY PULSE</p>
                <h2 className="mt-1 font-display text-xl font-bold">Issues being resolved</h2>
              </div>
              <span className="rounded-full bg-status-done/10 px-2 py-1 text-[10px] font-bold text-status-done">
                ● LIVE
              </span>
            </div>
            <div className="mt-5 grid grid-cols-3 gap-3">
              {[
                ["2,482", "Filed"],
                ["1,938", "Resolved"],
                ["78%", "On time"],
              ].map(([v, l]) => (
                <div key={l} className="rounded-md bg-panel-subtle p-3">
                  <p className="font-display text-xl font-bold">{v}</p>
                  <p className="text-[10px] text-muted-foreground">{l}</p>
                </div>
              ))}
            </div>
            <div className="mt-5 space-y-3">
              {[
                "Water leak repaired · Ward 8",
                "Pothole team dispatched · Ward 12",
                "Streetlights restored · Sector 7",
              ].map((x, i) => (
                <div key={x} className="flex items-center gap-3 rounded-md border p-3">
                  <span
                    className={`size-2 rounded-full ${i === 0 ? "bg-status-done" : "bg-primary"}`}
                  />
                  <p className="text-xs font-semibold">{x}</p>
                  <span className="ml-auto text-[10px] text-muted-foreground">{i * 7 + 4}m</span>
                </div>
              ))}
            </div>
          </div>
        </div>
      </section>
      <section id="categories" className="mx-auto max-w-7xl px-4 py-16 sm:px-6">
        <div className="text-center">
          <p className="text-[10px] font-extrabold tracking-[.16em] text-primary">
            COMMON CATEGORIES
          </p>
          <h2 className="mt-2 font-display text-3xl font-bold">What would you like to report?</h2>
          <p className="mt-2 text-sm text-muted-foreground">
            Choose a category and our AI will route it to the right department.
          </p>
        </div>
        <div className="mt-9 grid gap-3 sm:grid-cols-2 lg:grid-cols-5">
          {cats.map((c) => (
            <Link
              to="/report"
              key={c.name}
              className="panel rounded-lg p-5 transition-transform hover:-translate-y-1"
            >
              <span className="grid size-10 place-items-center rounded-md bg-brand-soft text-primary">
                <c.icon className="size-5" />
              </span>
              <h3 className="mt-4 font-bold">{c.name}</h3>
              <p className="mt-1 text-xs text-muted-foreground">{c.text}</p>
              <ArrowRight className="mt-5 size-4 text-primary" />
            </Link>
          ))}
        </div>
      </section>
    </main>
  );
}
