import { createFileRoute } from "@tanstack/react-router";
import { ReportPage } from "@/components/civic-pages";
export const Route = createFileRoute("/report")({
  head: () => ({
    meta: [
      { title: "Report a Complaint — CivicPulse AI" },
      { name: "description", content: "Submit a civic grievance with location and evidence." },
      { property: "og:title", content: "Report a Complaint — CivicPulse AI" },
      {
        property: "og:description",
        content: "Submit a civic grievance with location and evidence.",
      },
      { property: "og:type", content: "website" },
      { name: "twitter:card", content: "summary_large_image" },
    ],
  }),
  component: ReportPage,
});
