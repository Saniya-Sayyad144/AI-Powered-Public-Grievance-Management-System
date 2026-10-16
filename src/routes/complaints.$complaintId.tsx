import { createFileRoute } from "@tanstack/react-router";
import { ComplaintDetail } from "@/components/civic-pages";
export const Route = createFileRoute("/complaints/$complaintId")({
  head: () => ({
    meta: [
      { title: "Complaint Details — CivicPulse AI" },
      { name: "description", content: "Complaint status, assignment, evidence, and AI review." },
      { property: "og:title", content: "Complaint Details — CivicPulse AI" },
      {
        property: "og:description",
        content: "Complaint status, assignment, evidence, and AI review.",
      },
      { property: "og:type", content: "website" },
      { name: "twitter:card", content: "summary_large_image" },
    ],
  }),
  component: Page,
});
function Page() {
  const { complaintId } = Route.useParams();
  return <ComplaintDetail id={complaintId} />;
}
