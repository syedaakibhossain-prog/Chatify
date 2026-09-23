interface Props {
  names: string[];
}

export default function TypingIndicator({ names }: Props) {
  if (names.length === 0) return <div className="typing-indicator" />;

  const label =
    names.length === 1
      ? `${names[0]} is typing`
      : `${names.slice(0, 2).join(", ")} are typing`;

  return (
    <div className="typing-indicator">
      <div className="typing-dots">
        <span />
        <span />
        <span />
      </div>
      <span>{label}</span>
    </div>
  );
}
