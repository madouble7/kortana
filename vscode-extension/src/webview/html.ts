import { randomBytes } from "crypto";

import * as vscode from "vscode";

import { createFrameStyles } from "./styles";

type HtmlDocumentOptions = {
    body: string;
    nonce?: string;
    script?: string;
    title: string;
    webview: vscode.Webview;
    frameSources?: string[];
};

export function createNonce(): string {
    return randomBytes(16).toString("base64");
}

export function renderHtmlDocument(options: HtmlDocumentOptions): string {
    const csp = getWebviewContentSecurityPolicy(
        options.webview,
        options.nonce,
        options.frameSources ?? []
    );
    const scriptTag =
        options.script && options.nonce
            ? `<script nonce="${options.nonce}">${options.script}</script>`
            : "";

    return `<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta http-equiv="Content-Security-Policy" content="${csp}">
    <title>${options.title}</title>
</head>
<body>
    ${options.body}
    ${scriptTag}
</body>
</html>`;
}

export function getFrameWebviewContent(
    webview: vscode.Webview,
    url: string,
    title: string
): string {
    const frameOrigin = new URL(url).origin;

    return renderHtmlDocument({
        body: `
${createFrameStyles()}
<iframe src="${url}" title="${title}" allow="camera *; microphone *; geolocation *; clipboard-write *;"></iframe>
        `,
        frameSources: [frameOrigin],
        title,
        webview,
    });
}

function getWebviewContentSecurityPolicy(
    webview: vscode.Webview,
    nonce?: string,
    frameSources: string[] = []
): string {
    const directives = [
        "default-src 'none'",
        `img-src ${webview.cspSource} https: data:`,
        `style-src ${webview.cspSource} 'unsafe-inline'`,
        `font-src ${webview.cspSource}`,
        nonce ? `script-src 'nonce-${nonce}'` : "script-src 'none'",
    ];

    if (frameSources.length > 0) {
        directives.push(`frame-src ${frameSources.join(" ")}`);
    }

    return directives.join("; ");
}
