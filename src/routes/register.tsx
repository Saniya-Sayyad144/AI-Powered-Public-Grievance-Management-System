import { createFileRoute } from "@tanstack/react-router";
import { RegisterPage } from "@/components/civic-auth";

export const Route = createFileRoute("/register")({
  head: () => ({
    meta: [
      { title: "Register — CivicPulse AI" },
      { name: "description", content: "Create a CivicPulse citizen account." },
      { property: "og:title", content: "Register — CivicPulse AI" },
      { property: "og:description", content: "Create a CivicPulse citizen account." },
      { property: "og:type", content: "website" },
      { name: "twitter:card", content: "summary_large_image" },
    ],
  }),
  component: RegisterPage,
});
