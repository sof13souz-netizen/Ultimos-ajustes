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