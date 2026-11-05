/* MedExpert: selección de opciones y avance en los pasos de la consulta. Sin dependencias.
   El servidor vuelve a validar todo; este script solo marca opciones y habilita el avance. */
(function () {
  "use strict";

  function elegida(boton) {
    return boton.getAttribute("aria-pressed") === "true";
  }

  function marcar(boton, valor) {
    boton.setAttribute("aria-pressed", valor ? "true" : "false");
  }

  document.querySelectorAll("form.form-paso").forEach(function (form) {
    var unica = form.dataset.modo === "unica";
    var campo = form.dataset.campo;
    var opciones = Array.prototype.slice.call(form.querySelectorAll(".opcion[data-valor]"));
    var ninguna = form.querySelector("[data-ninguna]");
    var avanzar = form.querySelector(".avanzar");

    function valido() {
      return opciones.some(elegida) || (ninguna !== null && elegida(ninguna));
    }

    function actualizar() {
      var listo = valido();
      avanzar.setAttribute("aria-disabled", listo ? "false" : "true");
      avanzar.setAttribute(
        "aria-label",
        listo ? avanzar.dataset.ariaActivo : avanzar.dataset.ariaInactivo
      );
    }

    function agregarOculto(nombre, valor) {
      var campoOculto = document.createElement("input");
      campoOculto.type = "hidden";
      campoOculto.name = nombre;
      campoOculto.value = valor;
      campoOculto.setAttribute("data-generado", "");
      form.appendChild(campoOculto);
    }

    opciones.forEach(function (boton) {
      boton.addEventListener("click", function () {
        if (unica) {
          opciones.forEach(function (otra) { marcar(otra, otra === boton); });
        } else {
          marcar(boton, !elegida(boton));
        }
        // "Ninguna" es excluyente: al marcar cualquier condición se desmarca.
        if (ninguna !== null && elegida(boton)) {
          marcar(ninguna, false);
        }
        actualizar();
      });
    });

    if (ninguna !== null) {
      ninguna.addEventListener("click", function () {
        var activa = !elegida(ninguna);
        marcar(ninguna, activa);
        if (activa) {
          opciones.forEach(function (otra) { marcar(otra, false); });
        }
        actualizar();
      });
    }

    form.addEventListener("submit", function (evento) {
      if (!valido()) {
        evento.preventDefault();
        (opciones[0] || avanzar).focus();
        return;
      }
      form.querySelectorAll("input[data-generado]").forEach(function (oculto) { oculto.remove(); });
      opciones.filter(elegida).forEach(function (boton) { agregarOculto(campo, boton.dataset.valor); });
      if (ninguna !== null && elegida(ninguna)) {
        agregarOculto("ninguna", "1");
      }
    });

    actualizar();
  });
})();
