(function () {
    try {
        var script = document.currentScript;
        if (!script) return;
        var botId = script.getAttribute("data-bot-id");
        if (!botId) return;
        var position = script.getAttribute("data-position") || "bottom-right";
        var primaryColor =
            script.getAttribute("data-primary-color") || "#3B82F6";
        var welcomeMessage = script.getAttribute("data-welcome-message") || "";
        var autoOpen =
            (script.getAttribute("data-auto-open") || "false") === "true";

        var container = document.createElement("div");
        container.id = "veriply-widget";
        container.style.position = "fixed";
        container.style.zIndex = "2147483647";
        container.style.width = "360px";
        container.style.height = "560px";
        container.style.borderRadius = "12px";
        container.style.overflow = "hidden";
        container.style.boxShadow = "0 8px 24px rgba(0,0,0,0.2)";
        container.style.background = "#fff";
        container.style.display = autoOpen ? "block" : "none";

        var margin = "20px";
        switch (position) {
            case "bottom-left":
                container.style.left = margin;
                container.style.bottom = margin;
                break;
            case "top-right":
                container.style.right = margin;
                container.style.top = margin;
                break;
            case "top-left":
                container.style.left = margin;
                container.style.top = margin;
                break;
            default:
                container.style.right = margin;
                container.style.bottom = margin;
        }

        var button = document.createElement("button");
        button.type = "button";
        button.setAttribute("aria-label", "Open chat");
        button.style.position = "fixed";
        button.style.zIndex = "2147483647";
        button.style.width = "56px";
        button.style.height = "56px";
        button.style.borderRadius = "50%";
        button.style.border = "none";
        button.style.cursor = "pointer";
        button.style.boxShadow = "0 6px 16px rgba(0,0,0,0.25)";
        button.style.background = primaryColor;
        button.style.color = "#fff";

        // position button near widget
        switch (position) {
            case "bottom-left":
                button.style.left = margin;
                button.style.bottom = margin;
                break;
            case "top-right":
                button.style.right = margin;
                button.style.top = margin;
                break;
            case "top-left":
                button.style.left = margin;
                button.style.top = margin;
                break;
            default:
                button.style.right = margin;
                button.style.bottom = margin;
        }

        button.innerHTML =
            '<svg width="26" height="26" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg"><path d="M4 4H20V16H5.17L4 17.17V4Z" stroke="white" stroke-width="2"/><path d="M8 9H16" stroke="white" stroke-width="2"/><path d="M8 13H12" stroke="white" stroke-width="2"/></svg>';

        button.addEventListener("click", function () {
            container.style.display =
                container.style.display === "none" ? "block" : "none";
        });

        // Listen for close message from iframe
        window.addEventListener("message", function (event) {
            if (event.data.type === "veriply-widget-close") {
                container.style.display = "none";
            }
        });

        var iframe = document.createElement("iframe");
        var origin =
            script.getAttribute("data-origin") || location.origin || "";
        var base = origin.replace(/\/$/, "");
        var iframeSrc =
            base +
            "/public/chat/" +
            encodeURIComponent(botId) +
            "?embedded=true";
        iframe.src = iframeSrc;
        iframe.setAttribute(
            "sandbox",
            "allow-same-origin allow-forms allow-popups allow-scripts"
        );
        iframe.style.width = "100%";
        iframe.style.height = "100%";
        iframe.style.border = "0";

        container.appendChild(iframe);
        document.body.appendChild(container);
        document.body.appendChild(button);

        if (welcomeMessage) {
            try {
                sessionStorage.setItem("veriply_welcome", welcomeMessage);
            } catch (e) {}
        }
    } catch (e) {
        // Graceful failure
    }
})();
