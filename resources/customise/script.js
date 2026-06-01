/**
 * script.js
 * Handles communication between the palette UI and Fusion's python backend.
 * 
 * Message protocol (JSON strings):
 *   Python -> HTML: { action: "load", templates: { details, state, ... } }
 *   HTML -> Python: { action: "save", templates: { ... } }
 *   HTML -> Python: { action: "cancel" }
 */

"use strict";

// ----------------------------------------------------
// Field IDs (must match input elem IDs in index.html)
// and keys in lib/template.py DEFAULTS
// ----------------------------------------------------

const FIELD_IDS = [
    "details",
    "state",
    "large_text",
    "idle_text",
    "privacy_text",
];

const DEFAULTS = {
    "details":      'Designing "{document_name}"',
    "state":        "{component_count} · {workspace}",
    "large_text":   "Autodesk Fusion 360",
    "idle_text":    "Idle",
    "privacy_text": "Working in Fusion 360",
};

// ----------------------------------------------------
//      HELPERS
// ----------------------------------------------------

function getFields() {
    const templates = {};
    for (const id of FIELD_IDS) {
        templates[id] = document.getElementById(id).value;
    }
    return templates;
}

function setFields(templates) {
    for (const id of FIELD_IDS) {
        if (templates[id] !== undefined) {
            document.getElementById(id).value = templates[id];
        }
    }
}

function sendToPython(payload) {
    // adsk.fusionSendData is injected by Fusions palette webview
    if (typeof adsk !== undefined) {
        adsk.sendFusionData("incomingFromHTML", JSON.stringify(payload));
    } else {
        // dev fallback - log to console when opened outside Fusion
        console.log("sendToPython:", payload);
    }
}

// ----------------------------------------------------
//      RECEIVE MESSAGES FROM PYTHON
// ----------------------------------------------------

window.fusionJavaScriptHandler = {
    handleData: function (action, dataStr) {
        try {
            const data = JSON.parse(dataStr);
            if (action === "load" && data.templates) {
                setFields(data.templates);
            }
        } catch (e) {
            console.error("fusionJavaScriptHandler error:", e);
        }
    }
};

// ----------------------------------------------------
//      BUTTON HANDLERS
// ----------------------------------------------------

document.getElementById("btn-save").addEventListener("click", () => {
    sendToPython({ action: "save", templates: getFields() });

    // brief visual confirmation
    const btn = document.getElementById("btn-save");
    btn.textContent = "Saved!";
    btn.classList.add("saved");
    setTimeout(() => {
        btn.textContent = "Save";
        btn.classList.remove("saved");
    }, 1200);
});

document.getElementById("btn-cancel").addEventListener("click", () => {
    sendToPython({ action: "cancel" });
});

document.getElementById("btn-revert").addEventListener("click", () => {
    setFields(DEFAULTS);
});

// --------------------------------------------------
// signal python that the page is ready to receive
// template data (fires after page DOM is loaded)
// --------------------------------------------------

sendToPython({ action: "ready" });
