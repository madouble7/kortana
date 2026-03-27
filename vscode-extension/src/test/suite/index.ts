import * as assert from "assert";
import * as vscode from "vscode";

const EXPECTED_COMMANDS = [
    "kortana.openAIStudio",
    "kortana.openDeployPage",
    "kortana.unsealRuntime",
    "kortana.checkHealth",
    "kortana.viewMetrics",
    "kortana.autonomy.audit.open",
];

export async function run(): Promise<void> {
    const extension = vscode.extensions.all.find(
        (candidate) => candidate.packageJSON.name === "kortana-vscode"
    );

    assert.ok(extension, "Expected the Kor'tana extension to be available");

    if (!extension.isActive) {
        await extension.activate();
    }

    const registeredCommands = await vscode.commands.getCommands(true);
    const contributedCommands: string[] =
        extension.packageJSON.contributes?.commands?.map(
            (command: { command: string }) => command.command
        ) ?? [];

    for (const command of EXPECTED_COMMANDS) {
        assert.ok(
            registeredCommands.includes(command),
            `Expected command to be registered: ${command}`
        );
        assert.ok(
            contributedCommands.includes(command),
            `Expected command to be contributed: ${command}`
        );
    }
}
