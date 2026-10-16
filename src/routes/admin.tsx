import { createFileRoute } from "@tanstack/react-router";
import { CivicDashboard } from "@/components/civic-dashboards";
export const Route = createFileRoute("/admin")({
  head: () => ({
    meta: [
      { title: "Admin Dashboard — CivicPulse AI" },
      { name: "description", content: "Citywide grievance operations and AI recommendations." },
      { property: "og:title", content: "Admin Dashboard — CivicPulse AI" },
      {
        property: "og:description",
        content: "Citywide grievance operations and AI recommendations.",
      },
      { property: "og:type", content: "website" },
      { name: "twitter:card", content: "summary_large_image" },
    ],
  }),
  component: () => <CivicDashboard role="admin" />,
});
