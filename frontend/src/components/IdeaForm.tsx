import type { FormEvent } from "react";

type Props = {
  onSubmit: (idea: string) => void;
  disabled: boolean;
};

export function IdeaForm({ onSubmit, disabled }: Props) {
  const handle = (e: FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    const fd = new FormData(e.currentTarget);
    const idea = String(fd.get("idea") ?? "").trim();
    if (!idea) return;
    onSubmit(idea);
  };

  return (
    <form onSubmit={handle} className="idea-form">
      <label htmlFor="idea">Product or startup idea</label>
      <textarea
        id="idea"
        name="idea"
        rows={6}
        required
        disabled={disabled}
        placeholder="Describe your idea in a few sentences."
      />
      <button type="submit" disabled={disabled}>
        {disabled ? "Running…" : "Analyze"}
      </button>
    </form>
  );
}
