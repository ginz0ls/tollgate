import { createFileRoute } from "@tanstack/react-router";

import { StatusBadge } from "../components/StatusBadge";

export const Route = createFileRoute("/")({
  component: Home,
});

function Home() {
  return (
    <main>
      <h1>Appunti</h1>
      <StatusBadge state="ok" text="Pronto" />
    </main>
  );
}
