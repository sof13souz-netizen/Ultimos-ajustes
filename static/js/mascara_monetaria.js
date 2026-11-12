document.querySelectorAll(".campo-dinheiro").forEach(function(campo) {
    campo.addEventListener("input", function() {
        var numeros = campo.value.replace(/\D/g, "");
        if (numeros === "") {
            campo.value = "";
        } else {
            var valor = (Number(numeros) / 100).toFixed(2);
            var partes = valor.split(".");
            partes[0] = partes[0].replace(/\B(?=(\d{3})+(?!\d))/g, ".");
            campo.value = partes[0] + "," + partes[1];
        }
    });
});
