import { createFileRoute } from "@tanstack/react-router";
import { LoginPage } from "@/components/civic-auth";

export const Route = createFileRoute("/login")({
  head: () => ({
    meta: [
      { title: "Sign in — CivicPulse AI" },
      { name: "description", content: "Access your CivicPulse AI account." },
      { property: "og:title", content: "Sign in — CivicPulse AI" },
      { property: "og:description", content: "Access your CivicPulse AI account." },
      { property: "og:type", content: "website" },
      { name: "twitter:card", content: "summary_large_image" },
    ],
  }),
  component: LoginPage,
});
