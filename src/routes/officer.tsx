import { createFileRoute } from "@tanstack/react-router";
import { CivicDashboard } from "@/components/civic-dashboards";
export const Route = createFileRoute("/officer")({
  head: () => ({
    meta: [
      { title: "Officer Dashboard — CivicPulse AI" },
      { name: "description", content: "Assigned civic complaints and field updates." },
      { property: "og:title", content: "Officer Dashboard — CivicPulse AI" },
      { property: "og:description", content: "Assigned civic complaints and field updates." },
      { property: "og:type", content: "website" },
      { name: "twitter:card", content: "summary_large_image" },
    ],
  }),
  component: () => <CivicDashboard role="officer" />,
});
