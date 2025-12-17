import Link from "next/link";
import { AlertCircle } from "lucide-react";
import { Button } from "@/components/ui/button";

export default function NotFound() {
    return (
        <div className="h-screen w-full flex items-center justify-center bg-slate-50">
            <div className="text-center max-w-md px-6">
                <AlertCircle className="h-16 w-16 text-amber-500 mx-auto mb-4" />
                <h1 className="text-2xl font-semibold text-slate-900 mb-2">
                    Bot Not Found
                </h1>
                <p className="text-slate-600 mb-6">
                    The bot you're looking for doesn't exist or is not
                    available for public chat.
                </p>
                <div className="space-x-4">
                    <Button asChild variant="default">
                        <Link href="/">Go Home</Link>
                    </Button>
                    <Button asChild variant="outline">
                        <a href="mailto:support@veriply.com">Contact Support</a>
                    </Button>
                </div>
            </div>
        </div>
    );
}
