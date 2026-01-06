export default async function BotWidgetConfigRouter({
    params,
}: {
    params: { botId: string };
}) {
    const { botId } = params;

    // Fetch groups the user belongs to, to build correct group-scoped route
    let groups: Array<{ id: string; name: string }> = [];
    try {
        const res = await fetch("/api/v1/groups", {
            cache: "no-store",
        });
        if (res.ok) {
            groups = await res.json();
        }
    } catch {
        // ignore; show fallback UI
    }

    // If exactly one group, redirect to its widget settings page
    if (groups.length === 1) {
        const gid = groups[0].id;
        // Use a client-side redirect to preserve app router behavior
        return (
            <meta
                httpEquiv="refresh"
                content={`0;url=/dashboard/groups/${gid}/bots/${botId}/widget`}
            />
        );
    }

    // Otherwise, show a simple selector with links
    return (
        <div className="container max-w-3xl py-8">
            <h1 className="text-2xl font-bold mb-4">
                Select Group for Bot Widget Settings
            </h1>
            {groups.length === 0 ? (
                <p className="text-slate-600">
                    No groups found or you may not be signed in. Please open the
                    widget settings via the group-scoped path.
                </p>
            ) : (
                <ul className="space-y-3">
                    {groups.map((g) => (
                        <li key={g.id}>
                            <a
                                href={`/dashboard/groups/${g.id}/bots/${botId}/widget`}
                                className="text-sky-600 hover:underline"
                            >
                                Open settings for group: {g.name}
                            </a>
                        </li>
                    ))}
                </ul>
            )}
            <div className="mt-6">
                <p className="text-sm text-slate-500">
                    Direct link (requires group id):
                </p>
                <code className="text-xs">
                    /dashboard/groups/&lt;groupId&gt;/bots/{botId}/widget
                </code>
            </div>
        </div>
    );
}
