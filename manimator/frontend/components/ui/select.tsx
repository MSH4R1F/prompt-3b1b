import * as React from "react";

import { cn } from "@/lib/utils";

interface SelectContextValue {
  value: string;
  onValueChange: (value: string) => void;
}

const SelectContext = React.createContext<SelectContextValue | null>(null);

export function Select({
  value,
  onValueChange,
  children,
}: {
  value: string;
  onValueChange: (value: string) => void;
  children: React.ReactNode;
}) {
  return <SelectContext.Provider value={{ value, onValueChange }}>{children}</SelectContext.Provider>;
}

export function SelectTrigger({ id, children }: { id?: string; children: React.ReactNode }) {
  return (
    <div id={id} className="rounded-md border border-input bg-background px-3 py-2 text-sm">
      {children}
    </div>
  );
}

export function SelectValue() {
  return null;
}

export function SelectContent({ children }: { children: React.ReactNode }) {
  const context = React.useContext(SelectContext);
  if (!context) return null;

  return (
    <select
      className={cn("mt-2 w-full rounded-md border border-input bg-background px-3 py-2 text-sm")}
      value={context.value}
      onChange={(event) => context.onValueChange(event.target.value)}
    >
      {children}
    </select>
  );
}

export function SelectItem({ value, children }: { value: string; children: React.ReactNode }) {
  return <option value={value}>{children}</option>;
}
