import {
    STATUS_ALIVE_CLASS,
    STATUS_ALIVE_COLOR,
    STATUS_OFFLINE_CLASS,
    STATUS_OFFLINE_COLOR,
} from "./styles";

export function createWebviewFormattingHelpersScript(): string {
    return `
const STATUS_ALIVE_CLASS = "${STATUS_ALIVE_CLASS}";
const STATUS_OFFLINE_CLASS = "${STATUS_OFFLINE_CLASS}";
const STATUS_ALIVE_COLOR = "${STATUS_ALIVE_COLOR}";
const STATUS_OFFLINE_COLOR = "${STATUS_OFFLINE_COLOR}";

function formatStatusText(isOnline, onlineText, offlineText = "Offline", label = "") {
    return label + (isOnline ? onlineText : offlineText);
}

function getStatusClassName(isOnline) {
    return isOnline ? STATUS_ALIVE_CLASS : STATUS_OFFLINE_CLASS;
}

function getStatusIndicatorColor(isOnline) {
    return isOnline ? STATUS_ALIVE_COLOR : STATUS_OFFLINE_COLOR;
}

function applyStatusText(id, isOnline, onlineText, offlineText = "Offline", label = "") {
    setElementText(id, formatStatusText(isOnline, onlineText, offlineText, label));
}

function applyStatusClassName(id, isOnline) {
    setElementClassName(id, getStatusClassName(isOnline));
}

function applyStatusIndicatorColor(id, isOnline) {
    setElementStyle(id, "background", getStatusIndicatorColor(isOnline));
}

function formatTimestamp(value) {
    if (!value) {
        return "";
    }

    const parsed = new Date(value);
    return Number.isNaN(parsed.getTime()) ? String(value) : parsed.toLocaleString();
}

function createAuditActionItem(action) {
    const item = createDomElement("div", {
        className: "audit-item status-" + action.status,
    });

    item.appendChild(
        createDomElement("strong", {
            textContent: action.type + ": " + action.description,
        })
    );
    item.appendChild(document.createElement("br"));
    item.appendChild(
        createDomElement("small", {
            textContent: formatTimestamp(action.timestamp),
        })
    );

    return item;
}

function renderAuditActionList(containerId, actions) {
    if (!actions.length) {
        renderStateBlock(
            containerId,
            "No audit actions available",
            "",
            "audit-item status-pending"
        );
        return;
    }

    replaceElementChildren(containerId);
    const container = getRequiredElement(containerId);

    for (const action of actions) {
        container.appendChild(createAuditActionItem(action));
    }
}
    `;
}
