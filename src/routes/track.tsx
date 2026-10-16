import { createFileRoute } from "@tanstack/react-router";
import { TrackPage } from "@/components/civic-auth";

export const Route = createFileRoute("/track")({
  head: () => ({
    meta: [
      { title: "Track Complaint — CivicPulse AI" },
      { name: "description", content: "Track a public grievance by reference number." },
      { property: "og:title", content: "Track Complaint — CivicPulse AI" },
      { property: "og:description", content: "Track a public grievance by reference number." },
      { property: "og:type", content: "website" },
      { name: "twitter:card", content: "summary_large_image" },
    ],
  }),
  component: TrackPage,
});
