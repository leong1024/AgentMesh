import ReactMarkdown from "react-markdown";
import rehypeSanitize from "rehype-sanitize";
import remarkGfm from "remark-gfm";

import { extractMarkdownReport } from "../utils/extractMarkdownReport";

type Props = {
  /** Raw stream payload: markdown, or full JSON string with a nested `report` field. */
  markdown: string;
};

export function ReportView({ markdown }: Props) {
  const body = extractMarkdownReport(markdown);
  if (!body) return null;
  return (
    <article className="report-view">
      <ReactMarkdown
        remarkPlugins={[remarkGfm]}
        rehypePlugins={[rehypeSanitize]}
      >
        {body}
      </ReactMarkdown>
    </article>
  );
}
