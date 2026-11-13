// Pega todos os campos HTML com a classe "campo-dinheiro" e aplica o mesmo comportamento a cada um.
document.querySelectorAll(".campo-dinheiro").forEach(function(campo) {

    // "input" dispara a cada tecla digitada, colada ou apagada.
    campo.addEventListener("input", function() {

        // Remove tudo que não for dígito. \D significa "não-número" e o g aplica em todo o texto.
        // Assim, letras, pontos, vírgulas e "R$" digitados são descartados.
        var numeros = campo.value.replace(/\D/g, "");

        if (numeros === "") {
            // Se não sobrou nenhum número, deixa o campo vazio.
            campo.value = "";
        } else {
            // Divide por 100 para os dois últimos dígitos virarem centavos (150000 -> 1500)
            // e toFixed(2) força 2 casas decimais ("1500.00").
            var valor = (Number(numeros) / 100).toFixed(2);

            // Separa a parte inteira da decimal: ["1500", "00"].
            var partes = valor.split(".");

            // Coloca o ponto de milhar na parte inteira. A expressão regular insere um "." antes de
            // cada grupo de 3 dígitos contados do final: "1500" -> "1.500".
            partes[0] = partes[0].replace(/\B(?=(\d{3})+(?!\d))/g, ".");

            // Junta com vírgula decimal (padrão brasileiro): "1.500,00".
            campo.value = partes[0] + "," + partes[1];
        }
    });
});