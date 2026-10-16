import { createFileRoute } from "@tanstack/react-router";
import { SimplePage } from "@/components/civic-pages";
export const Route = createFileRoute("/notifications")({
  head: () => ({
    meta: [
      { title: "Notifications — CivicPulse AI" },
      { name: "description", content: "Complaint updates and alerts." },
      { property: "og:title", content: "Notifications — CivicPulse AI" },
      { property: "og:description", content: "Complaint updates and alerts." },
      { property: "og:type", content: "website" },
      { name: "twitter:card", content: "summary_large_image" },
    ],
  }),
  component: () => <SimplePage type="notifications" />,
});
