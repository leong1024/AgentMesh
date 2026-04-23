import { useState } from "react";

type Props = {
  disabled: boolean;
  onSend: (message: string) => Promise<void> | void;
};

export function ChatComposer({ disabled, onSend }: Props) {
  const [value, setValue] = useState("");

  const submit = async () => {
    const text = value.trim();
    if (!text || disabled) return;
    setValue("");
    await onSend(text);
  };

  return (
    <div className="chat-composer">
      <label className="chat-composer__field">
        <span>Message</span>
        <textarea
          aria-label="Chat message"
          placeholder="Send a message to the orchestrator..."
          value={value}
          onChange={(e) => setValue(e.target.value)}
          disabled={disabled}
          rows={3}
          onKeyDown={(e) => {
            if (e.key === "Enter" && !e.shiftKey) {
              e.preventDefault();
              void submit();
            }
          }}
        />
      </label>
      <button type="button" disabled={disabled || !value.trim()} onClick={() => void submit()}>
        {disabled ? "Sending..." : "Send to Orchestrator"}
      </button>
    </div>
  );
}
