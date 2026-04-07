import {
    type HostResponseEnvelope,
    type WebviewCommandMessage,
    type WebviewRequestMessage,
} from "./messages";

type RuntimeCommandBinding = {
    elementId: string;
    message: WebviewCommandMessage;
};

type RuntimeResponseBinding = {
    type: HostResponseEnvelope["type"];
    handlerName: string;
};

type RuntimeRequestPoller = {
    functionName: string;
    message: WebviewRequestMessage;
    intervalMs?: number;
    invokeImmediately?: boolean;
};

type WebviewRuntimeScriptOptions = {
    commandBindings?: RuntimeCommandBinding[];
    responseBindings?: RuntimeResponseBinding[];
    requestPollers?: RuntimeRequestPoller[];
};

export function createWebviewRuntimeScript(
    options: WebviewRuntimeScriptOptions
): string {
    const sections: string[] = [
        "const vscodeApi = acquireVsCodeApi();",
        "",
        "function postHostMessage(message) {",
        "    vscodeApi.postMessage(message);",
        "}",
    ];

    for (const requestPoller of options.requestPollers ?? []) {
        sections.push(
            "",
            `function ${requestPoller.functionName}() {`,
            `    postHostMessage(${JSON.stringify(requestPoller.message)});`,
            "}"
        );
    }

    if ((options.responseBindings ?? []).length > 0) {
        sections.push(
            "",
            'window.addEventListener("message", (event) => {',
            "    const message = event.data;",
            "    switch (message.type) {"
        );

        for (const responseBinding of options.responseBindings ?? []) {
            sections.push(
                `        case ${JSON.stringify(responseBinding.type)}:`,
                `            ${responseBinding.handlerName}(message.payload);`,
                "            break;"
            );
        }

        sections.push(
            "        default:",
            "            break;",
            "    }",
            "});"
        );
    }

    for (const commandBinding of options.commandBindings ?? []) {
        sections.push(
            "",
            `document.getElementById(${JSON.stringify(commandBinding.elementId)}).addEventListener("click", () => postHostMessage(${JSON.stringify(commandBinding.message)}));`
        );
    }

    for (const requestPoller of options.requestPollers ?? []) {
        if (requestPoller.invokeImmediately) {
            sections.push("", `${requestPoller.functionName}();`);
        }

        if (requestPoller.intervalMs !== undefined) {
            sections.push(
                `setInterval(${requestPoller.functionName}, ${requestPoller.intervalMs});`
            );
        }
    }

    return sections.join("\n");
}
