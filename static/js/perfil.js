function mostrarFoto(input) {
    let arquivo = input.files[0];

    if (arquivo) {
        let imagem = document.getElementById("imagem-perfil");
        let textoSemFoto = document.getElementById("texto-sem-foto");

        // Mostra a foto escolhida antes de salvar
        imagem.src = URL.createObjectURL(arquivo);
        imagem.hidden = false;

        // Esconde o texto de adicionar foto
        textoSemFoto.hidden = true;
    }
}

function abrirConfirmacao() {
    document.getElementById("modal-excluir").style.display = "flex";
}

function fecharConfirmacao() {
    document.getElementById("modal-excluir").style.display = "none";
}

function confirmarExclusao() {
    document.getElementById("form-excluir").submit();
}