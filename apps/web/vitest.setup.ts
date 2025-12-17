import "@testing-library/jest-dom/vitest";
import { cleanup } from "@testing-library/react";
import { afterEach, vi } from "vitest";

// Cleanup after each test
afterEach(() => {
    cleanup();
});

// Provide a default mock for next/navigation used across tests
vi.mock("next/navigation", () => {
    const push = vi.fn();
    const replace = vi.fn();
    const back = vi.fn();
    const forward = vi.fn();
    const refresh = vi.fn();
    return {
        useRouter: () => ({ push, replace, back, forward, refresh }),
        usePathname: () => "/",
        useSearchParams: () => new URLSearchParams(""),
    };
});

// Safety: some DOM APIs aren't implemented in jsdom
if (!("scrollIntoView" in HTMLElement.prototype)) {
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    (HTMLElement.prototype as any).scrollIntoView = vi.fn();
}
