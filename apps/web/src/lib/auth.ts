/**
 * Get the access token from either localStorage or sessionStorage
 */
export function getAccessToken(): string | null {
    if (typeof window === "undefined") return null;

    // Check localStorage first (remember me = true)
    const localToken = localStorage.getItem("access_token");
    if (localToken) return localToken;

    // Fall back to sessionStorage (remember me = false)
    const sessionToken = sessionStorage.getItem("access_token");
    return sessionToken;
}

/**
 * Clear the access token from both storages
 */
export function clearAccessToken(): void {
    if (typeof window === "undefined") return;

    localStorage.removeItem("access_token");
    sessionStorage.removeItem("access_token");
}
