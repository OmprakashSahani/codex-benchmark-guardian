import { Github, ShieldCheck } from "lucide-react";
import { Badge } from "./ui";
import { ThemeToggle } from "./theme-toggle";

export function Header() {
  return (
    <header className="site-header">
      <a className="brand" href="#top" aria-label="Codex Benchmark Guardian home">
        <span className="mark"><ShieldCheck size={20} /></span>
        <span>Codex Benchmark Guardian</span>
      </a>
      <nav className="header-actions" aria-label="Primary navigation">
        <Badge>OpenAI Build Week</Badge>
        <a className="icon-button" href="https://github.com/OmprakashSahani/codex-benchmark-guardian" target="_blank" rel="noreferrer" aria-label="GitHub repository">
          <Github size={18} />
        </a>
        <ThemeToggle />
      </nav>
    </header>
  );
}
