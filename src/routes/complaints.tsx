import { createFileRoute, Outlet } from "@tanstack/react-router";
export const Route = createFileRoute("/complaints")({
  head: () => ({
    meta: [
      { title: "Complaints — CivicPulse AI" },
      { name: "description", content: "Search and manage public grievances." },
      { property: "og:title", content: "Complaints — CivicPulse AI" },
      { property: "og:description", content: "Search and manage public grievances." },
      { property: "og:type", content: "website" },
      { name: "twitter:card", content: "summary_large_image" },
    ],
  }),
  component: Outlet,
});
