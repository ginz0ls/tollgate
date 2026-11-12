type StatusBadgeProps = {
  state: "ok" | "errore";
  text: string;
};

export function StatusBadge({ state, text }: StatusBadgeProps) {
  return (
    <span className={`badge badge-${state}`} role="status">
      {text}
    </span>
  );
}
