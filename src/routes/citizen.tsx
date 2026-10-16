import { createFileRoute } from "@tanstack/react-router";
import { CivicDashboard } from "@/components/civic-dashboards";
export const Route = createFileRoute("/citizen")({
  head: () => ({
    meta: [
      { title: "Citizen Dashboard — CivicPulse AI" },
      { name: "description", content: "Report and track public grievances." },
      { property: "og:title", content: "Citizen Dashboard — CivicPulse AI" },
      { property: "og:description", content: "Report and track public grievances." },
      { property: "og:type", content: "website" },
      { name: "twitter:card", content: "summary_large_image" },
    ],
  }),
  component: () => <CivicDashboard role="citizen" />,
});
