import * as path from "path";
import * as fs from "fs";
import * as os from "os";

import { runTests } from "@vscode/test-electron";

function resolveVSCodeExecutablePath(): string | undefined {
    if (process.platform !== "win32") {
        return undefined;
    }

    const candidates = [
        path.join(os.homedir(), "AppData", "Local", "Programs", "Microsoft VS Code", "bin", "code.cmd"),
        path.join(os.homedir(), "AppData", "Local", "Programs", "Microsoft VS Code", "Code.exe"),
        path.join(os.homedir(), "AppData", "Local", "Programs", "Code", "bin", "code.cmd"),
        path.join(os.homedir(), "AppData", "Local", "Programs", "Code", "Code.exe"),
        "C:\\Program Files\\Microsoft VS Code\\Code.exe",
        "C:\\Program Files\\VS Code\\Code.exe",
    ];

    return candidates.find((candidate) => fs.existsSync(candidate));
}

async function main(): Promise<void> {
    try {
        const extensionDevelopmentPath = path.resolve(__dirname, "../..");
        const extensionTestsPath = path.resolve(__dirname, "./suite/index");
        const vscodeExecutablePath = resolveVSCodeExecutablePath();

        await runTests({
            extensionDevelopmentPath,
            extensionTestsPath,
            launchArgs: ["--disable-extensions"],
            ...(vscodeExecutablePath ? { vscodeExecutablePath } : {}),
        });
    } catch (error) {
        console.error("Failed to run extension tests");
        throw error;
    }
}

void main();
