
export default function Home() {
    return (
        <DashboardLayout userName="Sarah Anderson" userInitials="SA">
            <div className="space-y-6">
                {/* Welcome Section */}
                <div className="bg-white rounded-lg border border-slate-300 p-6 shadow-sm">
                    <h2 className="text-2xl font-semibold text-slate-950 mb-2">
                        Welcome to Veriply
                    </h2>
                    <p className="text-slate-600">
                        Review and verify AI-generated responses before they're
                        sent to customers.
                    </p>
                </div>

                {/* Stats Grid */}
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                    <div className="bg-white rounded-lg border border-slate-300 p-6 shadow-sm">
                        <div className="text-sm font-medium text-slate-600 mb-1">
                            Pending Review
                        </div>
                        <div className="text-3xl font-bold text-slate-950">
                            3
                        </div>
                        <p className="text-xs text-slate-500 mt-2">
                            Awaiting your approval
                        </p>
                    </div>
                    <div className="bg-white rounded-lg border border-slate-300 p-6 shadow-sm">
                        <div className="text-sm font-medium text-slate-600 mb-1">
                            This Week
                        </div>
                        <div className="text-3xl font-bold text-emerald-600">
                            24
                        </div>
                        <p className="text-xs text-slate-500 mt-2">
                            Responses verified
                        </p>
                    </div>
                    <div className="bg-white rounded-lg border border-slate-300 p-6 shadow-sm">
                        <div className="text-sm font-medium text-slate-600 mb-1">
                            Accuracy
                        </div>
                        <div className="text-3xl font-bold text-slate-950">
                            98%
                        </div>
                        <p className="text-xs text-slate-500 mt-2">
                            All-time approval rate
                        </p>
                    </div>
                </div>

                {/* Recent Activity */}
                <div className="bg-white rounded-lg border border-slate-300 p-6 shadow-sm">
                    <h3 className="text-lg font-semibold text-slate-950 mb-4">
                        Recent Activity
                    </h3>
                    <div className="space-y-3">
                        {[
                            {
                                status: "Approved",
                                time: "2 minutes ago",
                                ticket: "TK-1024",
                            },
                            {
                                status: "Approved",
                                time: "15 minutes ago",
                                ticket: "TK-1023",
                            },
                            {
                                status: "Rejected",
                                time: "1 hour ago",
                                ticket: "TK-1022",
                            },
                        ].map((item) => (
                            <div
                                key={item.ticket}
                                className="flex items-center justify-between py-2 border-t border-slate-200"
                            >
                                <div>
                                    <p className="text-sm font-medium text-slate-950">
                                        {item.ticket}
                                    </p>
                                    <p className="text-xs text-slate-500">
                                        {item.time}
                                    </p>
                                </div>
                                <div
                                    className={`text-xs font-medium px-3 py-1 rounded-full ${
                                        item.status === "Approved"
                                            ? "bg-emerald-100 text-emerald-700"
                                            : "bg-red-100 text-red-700"
                                    }`}
                                >
                                    {item.status}
                                </div>
                            </div>
                        ))}
                    </div>
                </div>
            </div>
        </DashboardLayout>
    );
}
