// Espera o HTML terminar de carregar antes de rodar o código.
// Sem isso, o JS poderia procurar elementos que ainda não existem na página.
document.addEventListener('DOMContentLoaded', function () {

    // Procura no HTML o cabeçalho (elemento com a classe "cabecalho-padrao").
    var cabecalho = document.querySelector('.cabecalho-padrao');
    // Se a página não tiver cabeçalho (ex.: tela de login), encerra aqui e não faz nada.
    if (!cabecalho) return;

    // Dentro do cabeçalho, pega a lista de links do menu e o bloco com os dados do usuário (foto/nome).
    var menu = cabecalho.querySelector('.cabecalho-menu');
    var usuario = cabecalho.querySelector('.cabecalho-usuario');
    // Sem menu não há o que ajustar, então encerra.
    if (!menu) return;

    // Cria por código o botão que abre/fecha o menu no celular (o "hambúrguer").
    var botao = document.createElement('button');
    botao.type = 'button';                          // evita que o botão envie formulários por engano
    botao.className = 'botao-menu-mobile';          // classe usada pelo CSS para estilizar e esconder no desktop
    botao.setAttribute('aria-label', 'Abrir menu'); // texto lido por leitores de tela (acessibilidade)
    botao.setAttribute('aria-expanded', 'false');   // informa que o menu começa fechado

    // Cria a imagem do ícone e a coloca dentro do botão.
    var imagem = document.createElement('img');
    imagem.src = '/static/uploads/campo_header.png';
    imagem.alt = 'Abrir menu';                      // texto alternativo se a imagem não carregar
    botao.appendChild(imagem);

    // Adiciona o botão pronto no final do cabeçalho.
    cabecalho.appendChild(botao);

    // Reorganiza o cabeçalho conforme a largura da tela.
    function ajustarMenu() {
        if (window.innerWidth <= 800) {
            // Tela pequena: se o bloco do usuário ainda não estiver dentro do menu,
            // move ele para o começo do menu (insertBefore + firstChild = primeira posição).
            if (usuario && usuario.parentElement !== menu) menu.insertBefore(usuario, menu.firstChild);
        } else if (usuario && usuario.parentElement === menu) {
            // Tela grande: se o usuário estiver dentro do menu, devolve ele ao cabeçalho, antes do botão.
            cabecalho.insertBefore(usuario, botao);
            // Fecha o menu mobile e atualiza a informação de acessibilidade.
            menu.classList.remove('menu-mobile-aberto');
            botao.setAttribute('aria-expanded', 'false');
        }
    }

    // Ao clicar no botão, alterna a classe que mostra/esconde o menu.
    botao.addEventListener('click', function () {
        // toggle: adiciona a classe se não tiver, remove se tiver.
        menu.classList.toggle('menu-mobile-aberto');
        // Atualiza o aria-expanded: "true" se o menu ficou aberto, "false" se fechou.
        botao.setAttribute('aria-expanded', menu.classList.contains('menu-mobile-aberto') ? 'true' : 'false');
    });

    // Ajusta uma vez ao abrir a página...
    ajustarMenu();
    // ...e de novo toda vez que a janela mudar de tamanho (girar o celular, redimensionar).
    window.addEventListener('resize', ajustarMenu);
});