import { createFileRoute } from "@tanstack/react-router";
import { ComplaintsPage } from "@/components/civic-pages";

export const Route = createFileRoute("/complaints/")({
  component: ComplaintsPage,
});
