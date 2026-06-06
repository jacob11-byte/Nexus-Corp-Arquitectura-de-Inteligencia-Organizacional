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
                showNotice("Procesando información del sistema...");
            }
        });
    });

    if (window.datosGraficas) {
        dibujarBarras("graficaAreas", window.datosGraficas.areas, ["#1f78c8", "#0f9f6e", "#b7791f", "#c2410c"]);
        dibujarBarras("graficaPrioridades", window.datosGraficas.prioridades, ["#c2410c", "#b7791f", "#0f9f6e", "#667085"]);
        dibujarLinea("graficaFechas", window.datosGraficas.fechas);
    }
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

function prepararLienzo(canvas) {
    const contexto = canvas.getContext("2d");
    const escala = window.devicePixelRatio || 1;
    const ancho = canvas.clientWidth || canvas.parentElement.clientWidth;
    const alto = Number(canvas.getAttribute("height")) || 220;
    canvas.width = ancho * escala;
    canvas.height = alto * escala;
    contexto.scale(escala, escala);
    contexto.clearRect(0, 0, ancho, alto);
    return { contexto, ancho, alto };
}

function dibujarMensajeVacio(contexto, ancho, alto) {
    contexto.fillStyle = "#667085";
    contexto.font = "14px Arial";
    contexto.textAlign = "center";
    contexto.fillText("No hay información para el rango seleccionado.", ancho / 2, alto / 2);
}

function dibujarBarras(idLienzo, datos, colores) {
    const canvas = document.getElementById(idLienzo);
    if (!canvas || !datos) return;

    const { contexto, ancho, alto } = prepararLienzo(canvas);
    const etiquetas = datos.etiquetas || [];
    const valores = datos.valores || [];
    const maximo = Math.max(...valores, 0);

    if (!maximo) {
        dibujarMensajeVacio(contexto, ancho, alto);
        return;
    }

    const margen = 34;
    const espacio = (ancho - margen * 2) / valores.length;
    const anchoBarra = Math.min(58, espacio * 0.55);

    contexto.strokeStyle = "#e9eef6";
    contexto.beginPath();
    contexto.moveTo(margen, alto - margen);
    contexto.lineTo(ancho - margen / 2, alto - margen);
    contexto.stroke();

    valores.forEach((valor, indice) => {
        const alturaBarra = ((alto - margen * 2) * valor) / maximo;
        const x = margen + indice * espacio + (espacio - anchoBarra) / 2;
        const y = alto - margen - alturaBarra;

        contexto.fillStyle = colores[indice % colores.length];
        contexto.fillRect(x, y, anchoBarra, alturaBarra);

        contexto.fillStyle = "#10243f";
        contexto.font = "700 13px Arial";
        contexto.textAlign = "center";
        contexto.fillText(String(valor), x + anchoBarra / 2, y - 8);

        contexto.fillStyle = "#667085";
        contexto.font = "12px Arial";
        contexto.fillText(etiquetas[indice], x + anchoBarra / 2, alto - 10);
    });
}

function dibujarLinea(idLienzo, datos) {
    const canvas = document.getElementById(idLienzo);
    if (!canvas || !datos) return;

    const { contexto, ancho, alto } = prepararLienzo(canvas);
    const etiquetas = datos.etiquetas || [];
    const valores = datos.valores || [];
    const maximo = Math.max(...valores, 0);

    if (!maximo) {
        dibujarMensajeVacio(contexto, ancho, alto);
        return;
    }

    const margen = 38;
    const paso = valores.length > 1 ? (ancho - margen * 2) / (valores.length - 1) : 0;

    contexto.strokeStyle = "#e9eef6";
    contexto.beginPath();
    contexto.moveTo(margen, alto - margen);
    contexto.lineTo(ancho - margen / 2, alto - margen);
    contexto.stroke();

    contexto.strokeStyle = "#1f78c8";
    contexto.lineWidth = 3;
    contexto.beginPath();

    valores.forEach((valor, indice) => {
        const x = valores.length > 1 ? margen + indice * paso : ancho / 2;
        const y = alto - margen - ((alto - margen * 2) * valor) / maximo;
        if (indice === 0) contexto.moveTo(x, y);
        else contexto.lineTo(x, y);
    });
    contexto.stroke();

    valores.forEach((valor, indice) => {
        const x = valores.length > 1 ? margen + indice * paso : ancho / 2;
        const y = alto - margen - ((alto - margen * 2) * valor) / maximo;
        contexto.fillStyle = "#ffffff";
        contexto.beginPath();
        contexto.arc(x, y, 5, 0, Math.PI * 2);
        contexto.fill();
        contexto.strokeStyle = "#1f78c8";
        contexto.lineWidth = 2;
        contexto.stroke();

        contexto.fillStyle = "#10243f";
        contexto.font = "700 12px Arial";
        contexto.textAlign = "center";
        contexto.fillText(String(valor), x, y - 10);

        contexto.fillStyle = "#667085";
        contexto.font = "12px Arial";
        contexto.fillText(etiquetas[indice], x, alto - 10);
    });
}
