document.addEventListener('DOMContentLoaded', function () {
    var cabecalho = document.querySelector('.cabecalho-padrao');
    if (!cabecalho) return;

    var menu = cabecalho.querySelector('.cabecalho-menu');
    var usuario = cabecalho.querySelector('.cabecalho-usuario');
    if (!menu) return;

    var botao = document.createElement('button');
    botao.type = 'button';
    botao.className = 'botao-menu-mobile';
    botao.setAttribute('aria-label', 'Abrir menu');
    botao.setAttribute('aria-expanded', 'false');
    var imagem = document.createElement('img');
    imagem.src = '/static/uploads/campo_header.png';
    imagem.alt = 'Abrir menu';
    botao.appendChild(imagem);
    cabecalho.appendChild(botao);

    function ajustarMenu() {
        if (window.innerWidth <= 800) {
            if (usuario && usuario.parentElement !== menu) menu.insertBefore(usuario, menu.firstChild);
        } else if (usuario && usuario.parentElement === menu) {
            cabecalho.insertBefore(usuario, botao);
            menu.classList.remove('menu-mobile-aberto');
            botao.setAttribute('aria-expanded', 'false');
        }
    }

    botao.addEventListener('click', function () {
        menu.classList.toggle('menu-mobile-aberto');
        botao.setAttribute('aria-expanded', menu.classList.contains('menu-mobile-aberto') ? 'true' : 'false');
    });

    ajustarMenu();
    window.addEventListener('resize', ajustarMenu);
});
