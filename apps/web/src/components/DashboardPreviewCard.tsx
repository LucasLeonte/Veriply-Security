import { LucideIcon } from "lucide-react";
import Link from "next/link";
import { ReactNode } from "react";

interface ActionLink {
    href: string;
    label: string;
    variant?: "primary" | "secondary";
    disabled?: boolean;
    disabledHint?: string;
}

interface DashboardPreviewCardProps<T> {
    icon: LucideIcon;
    iconBgColor: string;
    iconTextColor: string;
    title: string;
    description: string;
    totalCount: string;
    actions: ActionLink[];
    items?: T[];
    renderItem: (item: T) => ReactNode;
}

export function DashboardPreviewCard<T>({
    icon: Icon,
    iconBgColor,
    iconTextColor,
    title,
    description,
    totalCount,
    actions,
    items,
    renderItem,
}: DashboardPreviewCardProps<T>) {
    return (
        <div className="bg-white border border-slate-200 rounded-xl p-5 flex flex-col">
            <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                    <div
                        className={`p-2 rounded-md ${iconBgColor} ${iconTextColor}`}
                    >
                        <Icon className="h-5 w-5" />
                    </div>
                    <div>
                        <h3 className="font-medium text-slate-900">{title}</h3>
                        <p className="text-sm text-slate-500">{description}</p>
                    </div>
                </div>
                <span className="text-sm text-slate-500">{totalCount}</span>
            </div>

            <div className="mt-4 flex gap-2">
                {actions.map((action, index) => (
                    <Link
                        key={index}
                        href={action.href}
                        aria-disabled={action.disabled}
                        className={
                            action.variant === "primary"
                                ? action.disabled
                                    ? "px-3 py-2 text-sm rounded-lg bg-slate-100 text-slate-400 cursor-not-allowed"
                                    : `px-3 py-2 text-sm rounded-lg ${iconBgColor.replace(
                                          "100",
                                          "600"
                                      )} text-white hover:${iconBgColor.replace(
                                          "100",
                                          "700"
                                      )}`
                                : action.disabled
                                ? "px-3 py-2 text-sm rounded-lg border border-slate-200 text-slate-400 cursor-not-allowed"
                                : "px-3 py-2 text-sm rounded-lg border border-slate-300 hover:bg-slate-50"
                        }
                        title={
                            action.disabled ? action.disabledHint : undefined
                        }
                    >
                        {action.label}
                    </Link>
                ))}
            </div>

            {items && items.length > 0 && (
                <ul className="mt-4 divide-y divide-slate-100">
                    {items.map((item, index) => (
                        <li key={index}>{renderItem(item)}</li>
                    ))}
                </ul>
            )}
        </div>
    );
}
