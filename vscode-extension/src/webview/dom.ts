export function createWebviewDomHelpersScript(): string {
    return `
function getRequiredElement(id) {
    const element = document.getElementById(id);
    if (!element) {
        throw new Error("Missing required element: " + id);
    }

    return element;
}

function setElementText(id, value) {
    getRequiredElement(id).textContent = value;
}

function setElementClassName(id, className) {
    getRequiredElement(id).className = className;
}

function setElementStyle(id, property, value) {
    getRequiredElement(id).style[property] = value;
}

function replaceElementChildren(id, ...children) {
    getRequiredElement(id).replaceChildren(...children);
}

function createDomElement(tagName, options = {}) {
    const element = document.createElement(tagName);

    if (options.className) {
        element.className = options.className;
    }

    if (options.textContent !== undefined) {
        element.textContent = options.textContent;
    }

    return element;
}

function renderStateBlock(containerId, title, detail = "", className = "") {
    const stateBlock = createDomElement("div", { className });
    stateBlock.appendChild(createDomElement("strong", { textContent: title }));

    if (detail) {
        stateBlock.appendChild(document.createElement("br"));
        stateBlock.appendChild(
            createDomElement("small", { textContent: detail })
        );
    }

    replaceElementChildren(containerId, stateBlock);
}
    `;
}
