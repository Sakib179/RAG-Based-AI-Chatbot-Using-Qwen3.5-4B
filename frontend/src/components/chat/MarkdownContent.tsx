import type { ReactNode } from "react";

function inlineMarkdown(value: string): ReactNode[] {
  const tokenPattern = /(\*\*.+?\*\*|__.+?__|\*.+?\*|_.+?_|`.+?`)/g;
  const parts = value.split(tokenPattern).filter(Boolean);
  return parts.map((part, index) => {
    if ((part.startsWith("**") && part.endsWith("**")) || (part.startsWith("__") && part.endsWith("__"))) {
      return <strong key={index}>{part.slice(2, -2)}</strong>;
    }
    if ((part.startsWith("*") && part.endsWith("*")) || (part.startsWith("_") && part.endsWith("_"))) {
      return <em key={index}>{part.slice(1, -1)}</em>;
    }
    if (part.startsWith("`") && part.endsWith("`")) {
      return <code key={index} className="rounded bg-slate-200 px-1 py-0.5 text-[0.9em] dark:bg-slate-700">{part.slice(1, -1)}</code>;
    }
    return <span key={index}>{part}</span>;
  });
}

export function MarkdownContent({ content }: { content: string }) {
  const lines = content.split("\n");
  const nodes: ReactNode[] = [];
  let bullets: string[] = [];
  const flushBullets = () => {
    if (!bullets.length) return;
    nodes.push(<ul key={`list-${nodes.length}`} className="my-2 list-disc space-y-1 pl-5">{bullets.map((item, index) => <li key={index}>{inlineMarkdown(item)}</li>)}</ul>);
    bullets = [];
  };

  lines.forEach((line, index) => {
    const heading = /^(#{1,6})\s+(.+)$/.exec(line);
    const bullet = /^\s*[-*]\s+(.+)$/.exec(line);
    if (heading) {
      flushBullets();
      const level = heading[1].length;
      const className = level === 1 ? "mt-3 text-xl font-bold" : level === 2 ? "mt-3 text-lg font-bold" : "mt-2 font-semibold";
      const headingTags = ["h1", "h2", "h3", "h4", "h5", "h6"] as const;
      const Heading = headingTags[Math.min(level, 6) - 1];
      nodes.push(<Heading key={index} className={className}>{inlineMarkdown(heading[2])}</Heading>);
    } else if (bullet) {
      bullets.push(bullet[1]);
    } else if (line.trim()) {
      flushBullets();
      nodes.push(<p key={index} className="my-2">{inlineMarkdown(line)}</p>);
    } else {
      flushBullets();
    }
  });
  flushBullets();
  return <div>{nodes}</div>;
}
