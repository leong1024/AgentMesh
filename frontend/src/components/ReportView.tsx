import ReactMarkdown from "react-markdown";
import rehypeSanitize from "rehype-sanitize";

type Props = {
  markdown: string;
};

export function ReportView({ markdown }: Props) {
  return (
    <article className="report-view">
      <ReactMarkdown rehypePlugins={[rehypeSanitize]}>{markdown}</ReactMarkdown>
    </article>
  );
}
