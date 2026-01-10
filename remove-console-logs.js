const fs = require("fs");
const path = require("path");

// Patterns to match console statements
const patterns = [
    /console\.log\([^)]*\);?[\s]*/g,
    /console\.error\([^)]*\);?[\s]*/g,
    /console\.warn\([^)]*\);?[\s]*/g,
    /console\.debug\([^)]*\);?[\s]*/g,
    /console\.info\([^)]*\);?[\s]*/g,
];

// Multi-line patterns (more complex)
const multiLinePatterns = [
    /console\.(log|error|warn|debug|info)\s*\([^;]*?\);?/gs,
];

function removeConsoleLogs(filePath) {
    try {
        let content = fs.readFileSync(filePath, "utf8");
        const originalContent = content;

        // Apply multi-line patterns first
        for (const pattern of multiLinePatterns) {
            content = content.replace(pattern, "");
        }

        // Clean up empty lines (more than 2 consecutive)
        content = content.replace(/\n\s*\n\s*\n+/g, "\n\n");

        // Only write if something changed
        if (content !== originalContent) {
            fs.writeFileSync(filePath, content, "utf8");
            console.log(`Cleaned: ${filePath}`);
            return true;
        }
        return false;
    } catch (error) {
        console.error(`Error processing ${filePath}:`, error.message);
        return false;
    }
}

function walkDirectory(dir, extensions = [".ts", ".tsx", ".js", ".jsx"]) {
    const files = fs.readdirSync(dir);
    let processedCount = 0;

    for (const file of files) {
        const filePath = path.join(dir, file);
        const stat = fs.statSync(filePath);

        if (stat.isDirectory()) {
            if (
                file !== "node_modules" &&
                file !== ".next" &&
                file !== "dist" &&
                file !== "build"
            ) {
                processedCount += walkDirectory(filePath, extensions);
            }
        } else if (extensions.some((ext) => file.endsWith(ext))) {
            if (removeConsoleLogs(filePath)) {
                processedCount++;
            }
        }
    }

    return processedCount;
}

// Start from apps/web/src
const targetDir = path.join(__dirname, "apps", "web", "src");
console.log(`Starting cleanup in: ${targetDir}`);
const count = walkDirectory(targetDir);
console.log(`\nDone! Cleaned ${count} files.`);
