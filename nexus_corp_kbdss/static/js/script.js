document.addEventListener("DOMContentLoaded", () => {
    const forms = document.querySelectorAll(".needs-validation");

    forms.forEach((form) => {
        form.addEventListener("submit", (event) => {
            const requiredFields = form.querySelectorAll("[required]");
            let valid = true;

            requiredFields.forEach((field) => {
                if (!field.value.trim()) {
                    field.style.borderColor = "#c2410c";
                    valid = false;
                } else {
                    field.style.borderColor = "#cfd8e6";
                }
            });

            if (!valid) {
                event.preventDefault();
                showNotice("Complete los campos obligatorios antes de continuar.");
            } else {
                showNotice("Procesando informacion del KBDSS...");
            }
        });
    });
});

function showNotice(message) {
    let notice = document.querySelector(".js-notice");
    if (!notice) {
        notice = document.createElement("div");
        notice.className = "message js-notice";
        const content = document.querySelector(".content");
        content.insertBefore(notice, content.children[1] || null);
    }
    notice.textContent = message;
    window.setTimeout(() => notice.remove(), 2500);
}
