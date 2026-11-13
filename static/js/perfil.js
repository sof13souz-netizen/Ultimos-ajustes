// Mostra a prévia da foto escolhida, antes de salvar.
// "input" é o campo <input type="file"> que chamou a função (onchange="mostrarFoto(this)").
function mostrarFoto(input) {
    // input.files é a lista de arquivos escolhidos; [0] é o primeiro (e único).
    let arquivo = input.files[0];

    // Só continua se o usuário realmente escolheu um arquivo (ele pode ter cancelado).
    if (arquivo) {
        // Pega a tag <img> da foto e o texto "adicionar foto" pelos seus ids.
        let imagem = document.getElementById("imagem-perfil");
        let textoSemFoto = document.getElementById("texto-sem-foto");

        // Mostra a foto escolhida antes de salvar.
        // URL.createObjectURL cria um endereço temporário do arquivo na memória do navegador,
        // sem enviá-lo ao servidor.
        imagem.src = URL.createObjectURL(arquivo);
        imagem.hidden = false;      // torna a imagem visível

        // Esconde o texto de adicionar foto.
        textoSemFoto.hidden = true;
    }
}

// Abre a janela de confirmação de exclusão.
// display "flex" faz o modal aparecer (no CSS ele começa com display none).
function abrirConfirmacao() {
    document.getElementById("modal-excluir").style.display = "flex";
}

// Fecha a janela de confirmação (botão "Cancelar").
function fecharConfirmacao() {
    document.getElementById("modal-excluir").style.display = "none";
}

// Botão "Sim, excluir": envia o formulário escondido que faz POST em /perfil/excluir no Flask.
// O envio é feito por JavaScript para só acontecer depois da confirmação do usuário.
function confirmarExclusao() {
    document.getElementById("form-excluir").submit();
}