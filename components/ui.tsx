import type { ButtonHTMLAttributes, HTMLAttributes } from "react";

function classes(...values: Array<string | false | undefined>) {
  return values.filter(Boolean).join(" ");
}

export function Button({ className, ...props }: ButtonHTMLAttributes<HTMLButtonElement>) {
  return <button className={classes("button", className)} {...props} />;
}

export function Card({ className, ...props }: HTMLAttributes<HTMLDivElement>) {
  return <div className={classes("card", className)} {...props} />;
}

export function Badge({ tone = "neutral", className, ...props }: HTMLAttributes<HTMLSpanElement> & { tone?: "neutral" | "ready" | "review" | "block" }) {
  return <span className={classes("badge", `badge-${tone}`, className)} {...props} />;
}
