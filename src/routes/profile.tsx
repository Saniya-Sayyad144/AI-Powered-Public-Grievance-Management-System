import { createFileRoute } from "@tanstack/react-router";
import { SimplePage } from "@/components/civic-pages";
export const Route = createFileRoute("/profile")({
  head: () => ({
    meta: [
      { title: "Profile Settings — CivicPulse AI" },
      { name: "description", content: "Manage your CivicPulse profile." },
      { property: "og:title", content: "Profile Settings — CivicPulse AI" },
      { property: "og:description", content: "Manage your CivicPulse profile." },
      { property: "og:type", content: "website" },
      { name: "twitter:card", content: "summary_large_image" },
    ],
  }),
  component: () => <SimplePage type="profile" />,
});
