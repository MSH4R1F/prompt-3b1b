import * as React from "react";

import { cn } from "@/lib/utils";

type ButtonVariant = "default" | "outline";

interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: ButtonVariant;
}

export function Button({ className, variant = "default", ...props }: ButtonProps) {
  const variantClass =
    variant === "outline"
      ? "border border-border bg-background text-foreground hover:bg-muted"
      : "bg-primary text-primary-foreground hover:opacity-90";

  return (
    <button
      className={cn(
        "inline-flex h-10 items-center justify-center rounded-md px-4 py-2 text-sm font-medium disabled:pointer-events-none disabled:opacity-50",
        variantClass,
        className,
      )}
      {...props}
    />
  );
}
