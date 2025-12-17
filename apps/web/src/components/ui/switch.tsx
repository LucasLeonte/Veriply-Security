import * as React from "react";

interface SwitchProps extends Omit<React.InputHTMLAttributes<HTMLInputElement>, "type"> {
  checked: boolean;
  onCheckedChange?: (checked: boolean) => void;
}

export function Switch({ checked, onCheckedChange, className = "", ...props }: SwitchProps) {
  return (
    <label className={"inline-flex items-center cursor-pointer " + className}>
      <span className="relative">
        <input
          type="checkbox"
          className="sr-only"
          checked={checked}
          onChange={(e) => onCheckedChange?.(e.target.checked)}
          {...props}
        />
        <span
          aria-hidden="true"
          className={
            "block h-5 w-9 rounded-full transition-colors " +
            (checked ? "bg-sky-600" : "bg-slate-300")
          }
        />
        <span
          aria-hidden="true"
          className={
            "dot absolute left-0 top-0 h-5 w-5 rounded-full bg-white shadow transition-transform " +
            (checked ? "translate-x-4" : "")
          }
        />
      </span>
    </label>
  );
}
