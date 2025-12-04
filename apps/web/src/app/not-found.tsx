import Link from 'next/link';

export default function NotFound() {
    return (
        <div className="flex flex-col items-center justify-center min-h-screen bg-slate-100">
            <h2 className="text-2xl font-bold text-slate-900 mb-4">Page Not Found</h2>
            <p className="text-slate-600 mb-6">Could not find requested resource</p>
            <Link
                href="/"
                className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors"
            >
                Return Home
            </Link>
        </div>
    );
}
