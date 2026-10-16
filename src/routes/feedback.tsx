import { createFileRoute } from "@tanstack/react-router";
import { SimplePage } from "@/components/civic-pages";
export const Route = createFileRoute("/feedback")({
  head: () => ({
    meta: [
      { title: "Feedback — CivicPulse AI" },
      { name: "description", content: "Rate your civic grievance resolution experience." },
      { property: "og:title", content: "Feedback — CivicPulse AI" },
      { property: "og:description", content: "Rate your civic grievance resolution experience." },
      { property: "og:type", content: "website" },
      { name: "twitter:card", content: "summary_large_image" },
    ],
  }),
  component: () => <SimplePage type="feedback" />,
});
