from flask import (Flask, render_template, redirect, request, flash, url_for, session, send_from_directory, send_file,jsonify)
#aplicação web, abrir página do html e envia informações do python pra elas, redirecionar usuário, receber dados, mensagens temporárias, gera endereço de uma rota, armazena info dos usuários,
#envia arquivo de uma pasta específica, envia arquivo ao navegador como o pdf, transf dados do python em resposta formato json
import calendar  # calendario
import fdb  #executar comandos sql
import pygal #gráficos do dashboard
import os #arquivos do sistema
import math #calculos
import random  #valores
from datetime import date, datetime, timedelta  #calcular intervalo de dif entre data
from fpdf import FPDF  #documento pdf
from werkzeug.security import generate_password_hash, check_password_hash  #transf senha em hash para armazenar, verifica se a senha corresponde ao hash
from uuid import uuid4  #evitar nomes repetidos e identificar arquivos

# Flask(__name__) cria o objeto principal do site. O __name__ diz ao Flask onde está este arquivo,
# e é a partir dessa pasta que ele encontra as pastas "templates" (HTML) e "static" (imagens, css, js).
app = Flask(__name__)  # cria a aplicação Flask
app.config["SECRET_KEY"] = "1234"  # chave usada para assinar a sessão (cookie) e as mensagens flash; em produção deve ser longa e secreta

# dados de conexão com o banco Firebird
host = "localhost"  # servidor do banco (a própria máquina)
database = r"C:\Users\Aluno\Downloads\CredMais-pronta\CredMais-4rta-Sprint-FINALIZADA-main\BANCO.FDB"  # caminho do arquivo .FDB
user = "SYSDBA"  # usuário padrão do Firebird
password = "sysdba"  # senha do usuário


def conectar_banco():   #para conactar o banco
    # abre e devolve uma nova conexão com o Firebird; quem chama precisa fechar (close)
    # fdb.connect abre a conexão com o Firebird usando os dados definidos lá em cima
    # (servidor, caminho do arquivo .FDB, usuário e senha). Se o banco estiver desligado ou o caminho
    # estiver errado, essa linha gera um erro - por isso toda rota que chama conectar_banco() usa try/except.
    return fdb.connect(
        host=host,
        database=database,
        user=user,
        password=password
    )


def validar_senha(senha):
    # regra de senha forte: retorna True só se cumprir todos os requisitos
    if len(senha) < 8:  # mínimo de 8 caracteres
        return False
    # any(... for c in senha) percorre a senha caractere por caractere e devolve True assim que
    # encontrar UM caractere que atenda à condição (isupper = maiúscula, islower = minúscula,
    # isdigit = número). A linha do símbolo usa "not c.isalnum()": se não é letra nem número, é símbolo.
    tem_maiuscula = any(c.isupper() for c in senha)  # pelo menos 1 letra maiúscula
    tem_minuscula = any(c.islower() for c in senha)  # pelo menos 1 minúscula
    tem_numero = any(c.isdigit() for c in senha)  # pelo menos 1 número
    tem_especial = any(not c.isalnum() for c in senha)  # pelo menos 1 símbolo (não letra/número)

    return tem_maiuscula and tem_minuscula and tem_numero and tem_especial


# ADMINISTRADOR
TIPO_ADMIN = 2  # valor da coluna TIPO que identifica um administrador (1 = usuário comum)


# Esta função roda automaticamente antes de renderizar QUALQUER template.
# O dicionário que ela devolve vira variável global nos HTMLs, então todo template pode
# usar {{ eh_admin }} sem precisar que cada rota envie essa informação.
@app.context_processor
def dados_do_header():
    # context_processor: injeta a variável "eh_admin" automaticamente em TODOS os templates (ex.: para mostrar menu de admin)
    try:
        eh_admin = int(session.get("usuario_tipo", 0)) == TIPO_ADMIN  #procura na sessão o tipo do usuário conectado. Se não encontrar utiliza 0
        #transforma valor em inteiro e compara o tipo do usuário com a constante que representa no administrador
    except (TypeError, ValueError):  # se o valor da sessão não for numérico
        eh_admin = False
    return {"eh_admin": eh_admin}  #recebe true se for e false se nao for


# ============================================================
# INÍCIO
# ============================================================

# @app.route liga um endereço (URL) a uma função: quando o navegador acessa "/", o Flask executa inicio().
# Sem o parâmetro methods, a rota só aceita GET (abrir a página). Quem recebe formulário usa methods=["GET","POST"].
@app.route("/")
def inicio():
    # página inicial pública
    return render_template("index.html")
@app.route("/logo")
def logo():
    # entrega a imagem da logo guardada em static/uploads
    # app.root_path = pasta onde está o app.py. os.path.join monta o caminho com a barra correta do sistema
    # (\\ no Windows, / no Linux). send_from_directory entrega o arquivo de forma segura ao navegador,
    # impedindo que alguém acesse arquivos fora dessa pasta.
    return send_from_directory(os.path.join(app.root_path, "static", "uploads"),"logo.png")
@app.route("/fundo")
def fundo():
    # entrega a imagem de fundo das páginas
    return send_from_directory(os.path.join(app.root_path, "static", "uploads"),"fundo.png")


# ============================================================
# CADASTRO
# ============================================================

@app.route("/cadastro", methods=["GET", "POST"])
def cadastro():
    # GET: mostra o formulário | POST: valida os dados e cria o usuário
    if request.method == "POST":
        # request.form guarda os campos enviados pelo formulário HTML (método POST).
        # .get("nome", "") busca o campo pelo atributo name="nome" do input; se ele não existir, devolve "" (vazio)
        # em vez de dar erro. .strip() remove espaços no começo e no fim do texto digitado.
        nome = request.form.get("nome", "").strip()  # strip tira espaços das pontas
        email = request.form.get("email", "").strip().lower()  # e-mail sempre em minúsculo para evitar duplicidade
        senha = request.form.get("senha", "")
        confirmar_senha = request.form.get("confirmar_senha", "")

        # nenhum campo pode ficar vazio
        # "not nome" é True quando o texto está vazio (string vazia conta como falso no Python).
        # O "or" faz o if entrar se QUALQUER um dos campos estiver vazio.
        if not nome or not email or not senha or not confirmar_senha:
            # flash guarda uma mensagem temporária que o template exibe uma vez (usando get_flashed_messages).
            # Sem segundo argumento ela fica sem categoria; com "erro" ou "sucesso" o HTML escolhe a cor.
            flash("Preencha todos os campos.")
            return render_template("cadastro_usuario.html")

        # o nome precisa ter ao menos uma letra (não aceita só números/símbolos)
        if not any(c.isalpha() for c in nome):
            flash("O nome precisa ter pelo menos uma letra.")
            return render_template("cadastro_usuario.html")

        # aplica a regra de senha forte
        if not validar_senha(senha):
            flash("A senha deve ter no mínimo 8 caracteres, "
                 "uma letra maiúscula, uma letra minúscula, "
                 "um número e um caractere especial.")
            return render_template("cadastro_usuario.html")

        if senha != confirmar_senha:    #se a senha for diferente que confirmar senha
            flash("As senhas não são iguais.")
            return render_template("cadastro_usuario.html")

        conexao = None  # começam como None para o finally saber se precisam ser fechados
        cursor = None

        # try/except/finally: o Python tenta executar o bloco do try; se QUALQUER erro acontecer (banco fora do ar,
        # falha de SQL...), pula para o except em vez de derrubar o site com tela de erro. O finally roda sempre.
        try:   #tratamento de erro
            conexao = conectar_banco()
            cursor = conexao.cursor()

            # verifica se o e-mail já existe (? evita SQL injection)
            # O cursor é quem executa comandos SQL. O "?" é um parâmetro: o valor vem separado, na tupla (email,).
            # A vírgula depois de email é obrigatória - sem ela o Python não entende como tupla de 1 item.
            # Isso protege contra SQL Injection (alguém digitar comandos SQL no campo de e-mail).
            cursor.execute( "SELECT ID_USUARIO FROM USUARIO WHERE EMAIL = ?", (email,))

            # fetchone() devolve a PRIMEIRA linha do resultado ou None se a consulta não achou nada.
            # Se achou uma linha (valor "verdadeiro"), o e-mail já existe.
            if cursor.fetchone():  # achou alguém com esse e-mail
                flash("Este e-mail já está cadastrado.")
                return render_template("cadastro_usuario.html")

            # generate_password_hash transforma a senha em um código irreversível (hash com "sal" aleatório).
            # Assim, mesmo que o banco vaze, ninguém lê a senha real. Para conferir no login usa-se check_password_hash.
            senha_criptografada = generate_password_hash(senha)  # nunca guarda a senha pura, só o hash

            # cria o usuário: tipo 1 (comum), ativo, 0 tentativas de login, não bloqueado
            cursor.execute(
                """
                INSERT INTO USUARIO
                (NOME, EMAIL, SENHA, TIPO, ATIVO, TENTATIVAS_LOGIN, BLOQUEADO)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (nome, email, senha_criptografada, 1, True, 0, False)
            )

            # busca o ID recém-criado para ligar ao histórico de senha
            cursor.execute( "SELECT ID_USUARIO FROM USUARIO WHERE EMAIL = ?",(email,))

            usuario = cursor.fetchone()

            if not usuario:
                # raise cria um erro de propósito. Esse caso "não deveria acontecer" (acabamos de inserir o usuário),
                # mas se acontecer o except abaixo desfaz tudo com rollback.
                raise Exception("Usuário não foi encontrado após o cadastro.")

            id_usuario = usuario[0]

            # grava a primeira senha no histórico (usado depois para impedir reutilização)
            cursor.execute(
                """
                INSERT INTO HISTORICO_SENHA (SENHA, ID_USUARIO, DATA_ALTERACAO)
                VALUES (?, ?, CURRENT_TIMESTAMP)
                """,
                (senha_criptografada, id_usuario)
            )

            conexao.commit()  # só confirma se tudo deu certo (transação)

            flash("Cadastro realizado com sucesso!", "sucesso")
            # url_for("login") recebe o NOME DA FUNÇÃO (def login) e devolve a URL dela ("/login").
            # Assim, se a URL mudar um dia, só o @app.route precisa ser alterado. redirect manda o navegador para lá.
            return redirect(url_for("login"))

        except Exception:
            if conexao:
                conexao.rollback()  # desfaz tudo se algo falhou

            # logger.exception grava no terminal o erro completo (com o traceback), útil para o programador depurar,
            # enquanto o usuário vê apenas uma mensagem simples pelo flash.
            app.logger.exception("Erro ao salvar cadastro.")  # registra o erro completo no console
            flash("Erro ao salvar o cadastro.")
            return render_template("cadastro_usuario.html")

        finally:
            # sempre fecha cursor e conexão, com erro ou não
            if cursor:
                cursor.close()
            if conexao:
                conexao.close()

    return render_template("cadastro_usuario.html")  # GET: apenas mostra o formulário


# ============================================================
# LOGIN
# ============================================================

@app.route("/login", methods=["GET", "POST"])
def login():
    # GET: mostra o formulário | POST: autentica, controla tentativas e bloqueio
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        senha = request.form.get("senha", "")

        if not email or not senha:
            flash("Preencha o e-mail e a senha.")
            return render_template("login.html")

        conexao = None
        cursor = None

        try:
            conexao = conectar_banco()
            cursor = conexao.cursor()

            # busca os dados do usuário pelo e-mail
            cursor.execute(
                """
                SELECT ID_USUARIO, NOME, EMAIL, SENHA, TIPO, ATIVO, TENTATIVAS_LOGIN, BLOQUEADO, FOTO_PERFIL
                FROM USUARIO
                WHERE EMAIL = ?
                """,
                (email,)
            )

            usuario = cursor.fetchone()

            if not usuario:
                # mensagem genérica de propósito: não revela se o e-mail existe
                flash("E-mail ou senha incorretos.")
                return render_template("login.html")

            # separa as colunas da linha retornada em variáveis
            id_usuario = usuario[0]
            nome_usuario = usuario[1]
            email_usuario = usuario[2]
            senha_banco = usuario[3]
            tipo_usuario = usuario[4]
            ativo = usuario[5]
            # "usuario[6] or 0": se a coluna vier vazia (None), usa 0. Depois int() garante que seja número inteiro.
            tentativas_login = int(usuario[6] or 0)  # None vira 0
            bloqueado = usuario[7]
            foto_perfil = usuario[8] or ""

            # conta desativada não entra
            # O banco pode devolver o campo booleano como False ou como 0 dependendo do driver;
            # conferimos as duas formas para não deixar passar uma conta inativa.
            if ativo is False or ativo == 0:
                flash("Sua conta está inativa. Não é possível realizar o login.")
                return render_template("login.html")

            # conta bloqueada por excesso de tentativas não entra
            if bloqueado is True or bloqueado == 1:
                flash("Sua conta está bloqueada por excesso de tentativas.")
                return render_template("login.html")

            if not senha_banco:
                flash("Este usuário não possui uma senha cadastrada.")
                return render_template("login.html")

            # senha errada: soma tentativa e bloqueia ao chegar em 3
            # check_password_hash(hash_do_banco, senha_digitada) refaz o cálculo e devolve True se baterem.
            # Aqui o "not" faz o bloco rodar quando a senha está ERRADA.
            if not check_password_hash(senha_banco, senha):
                tentativas_login += 1

                if tentativas_login >= 3:
                    cursor.execute(
                        """
                        UPDATE USUARIO
                        SET TENTATIVAS_LOGIN = ?, BLOQUEADO = ?
                        WHERE ID_USUARIO = ?
                        """,
                        (tentativas_login, True, id_usuario)
                    )
                    conexao.commit()

                    flash("Você atingiu o limite de 3 tentativas. " "Sua conta foi bloqueada.")
                    return render_template("login.html")

                # ainda não chegou em 3: apenas salva o novo número de tentativas
                cursor.execute(
                    """
                    UPDATE USUARIO
                    SET TENTATIVAS_LOGIN = ?
                    WHERE ID_USUARIO = ?
                    """,
                    (tentativas_login, id_usuario)
                )
                conexao.commit()

                restantes = 3 - tentativas_login  #quantas vezes tentou o login

                if restantes == 1:
                    flash("E-mail ou senha incorretos. Você tem ""apenas 1 tentativa restante.")
                else:
                    flash(f"E-mail ou senha incorretos. " f"Você ainda possui {restantes} tentativas.")

                return render_template("login.html")

            # senha correta: zera as tentativas e garante que não está bloqueado
            cursor.execute(
                """
                UPDATE USUARIO
                SET TENTATIVAS_LOGIN = ?, BLOQUEADO = ?
                WHERE ID_USUARIO = ?
                """,
                (0, False, id_usuario)
            )
            conexao.commit()

            # cria a sessão do usuário logado (limpa qualquer sessão antiga antes)
            session.clear()
            # session é um dicionário guardado em um cookie ASSINADO com a SECRET_KEY: o usuário não consegue alterar
            # seus valores sem invalidar a assinatura. É por ele que o sistema sabe quem está logado nas próximas páginas.
            session["usuario_id"] = id_usuario
            session["usuario_nome"] = nome_usuario
            session["usuario_email"] = email_usuario
            session["usuario_tipo"] = tipo_usuario
            session["usuario_foto"] = foto_perfil

            return redirect(url_for("dashboard"))

        except Exception:
            app.logger.exception("Erro no login.")
            flash("Erro ao realizar o login.")
            return render_template("login.html")

        finally:
            if cursor:
                cursor.close()
            if conexao:
                conexao.close()

    return render_template("login.html")


@app.route("/sucesso")
def sucesso():
    # rota de atalho: se não estiver logado volta ao início, senão vai ao dashboard
    if "usuario_id" not in session:
        return redirect(url_for("inicio")) #verifica se o usuário cadastrou

    return redirect(url_for("dashboard"))


@app.route("/sistema")
def sistema():
    # outro atalho com o mesmo comportamento de /sucesso
    if "usuario_id" not in session:
        return redirect(url_for("inicio"))

    return redirect(url_for("dashboard"))


@app.route("/logout")
def logout():
    # encerra a sessão e volta para a página inicial
    session.clear()
    return redirect(url_for("inicio"))   #limpa todos os dados da sessão


@app.route("/sair")
def sair():
    # entrega a imagem "sair.png" usada no botão de logout
    caminho = os.path.join(app.root_path, "static", "uploads")
    return send_from_directory(caminho, "sair.png")


# ============================================================
# PERFIL
# ============================================================

def buscar_usuario(id_usuario):
    # retorna (id, nome, email, senha_hash, foto) do usuário, ou None se não existir
    conexao = conectar_banco()

    try:
        cursor = conexao.cursor()
        try:
            cursor.execute(
                """
                SELECT ID_USUARIO, NOME, EMAIL, SENHA, FOTO_PERFIL
                FROM USUARIO
                WHERE ID_USUARIO = ?
                """,
                (id_usuario,)
            )
            return cursor.fetchone()
        finally:
            cursor.close()  # try/finally aninhados garantem o fechamento mesmo com erro
    finally:
        conexao.close()


def email_ja_existe(email, id_usuario):
    # True se OUTRO usuário (ID diferente do atual) já usa esse e-mail
    conexao = conectar_banco()

    try:
        cursor = conexao.cursor()
        try:
            cursor.execute(
                """
                SELECT ID_USUARIO
                FROM USUARIO
                WHERE EMAIL = ? AND ID_USUARIO <> ?
                """,
                (email, id_usuario)
            )
            return cursor.fetchone() is not None
        finally:
            cursor.close()
    finally:
        conexao.close()


def buscar_ultimas_senhas(id_usuario):
    # devolve a lista com os hashes das 3 últimas senhas do usuário (mais recentes primeiro)
    conexao = conectar_banco()

    try:
        cursor = conexao.cursor()
        try:
            cursor.execute(
                """
                SELECT FIRST 3 SENHA
                FROM HISTORICO_SENHA
                WHERE ID_USUARIO = ?
                ORDER BY DATA_ALTERACAO DESC, ID_HISTORICO_SENHA DESC
                """,
                (id_usuario,)
            )
            return [registro[0] for registro in cursor.fetchall()]  # pega só a coluna SENHA de cada linha
        finally:
            cursor.close()
    finally:
        conexao.close()


@app.route("/perfil", methods=["GET", "POST"])
def perfil():
    # GET: mostra o formulário de edição | POST: atualiza nome, e-mail, senha e foto
    if "usuario_id" not in session:
        flash("Faça login para acessar seu perfil.")

        return redirect(url_for("login"))

    id_usuario = session["usuario_id"]

    if request.method == "GET":
        try:
            usuario = buscar_usuario(id_usuario)

            if usuario is None:
                flash("Usuário não encontrado.", "erro")
                return redirect(url_for("login"))

            # envia os dados atuais para preencher o formulário
            return render_template(
                "editar_perfil.html",
                nome=usuario[1] or "",
                email=usuario[2] or "",
                foto_perfil=usuario[4] or ""
            )

        except Exception:
            app.logger.exception("Erro ao consultar perfil.")
            flash("Não foi possível carregar o perfil.", "erro")
            return redirect(url_for("dashboard"))

    # ---- a partir daqui é POST ----
    nome = request.form.get("nome", "").strip()
    email = request.form.get("email", "").strip().lower()
    senha_atual = request.form.get("senha_atual", "")
    nova_senha = request.form.get("nova_senha", "")

    # Arquivos enviados pelo formulário (input type="file") ficam em request.files, não em request.form.
    foto = request.files.get("foto")  # arquivo enviado (pode vir vazio)
    nome_foto = None  # só recebe valor se uma foto válida for enviada

    if not any(c.isalpha() for c in nome):  #verificar se tem letra ( any ve se pelo menos uma das questoes é true)
        flash("O nome precisa ter pelo menos uma letra.", "erro")
        return redirect(url_for("perfil"))

    # limite de tamanho das colunas do banco
    if len(nome) > 100 or len(email) > 100:
        flash("Nome e e-mail devem ter no máximo 100 caracteres.", "erro")
        return redirect(url_for("perfil"))

    try:
        usuario = buscar_usuario(id_usuario)

        if usuario is None:
            flash("Usuário não encontrado.", "erro")
            return redirect(url_for("perfil"))

        hash_atual = usuario[3] or ""  # hash da senha atual guardada no banco

        # para trocar a senha é obrigatório informar a atual
        if nova_senha and not senha_atual:
            flash("Informe sua senha atual para definir uma nova senha.", "erro")
            return redirect(url_for("perfil"))

        if email_ja_existe(email, id_usuario):
            flash("Este e-mail já está cadastrado.", "erro")
            return redirect(url_for("perfil"))

        novo_hash = None  # continua None se a senha não for alterada

        if nova_senha:
            # confere se a senha atual digitada está correta
            if not check_password_hash(hash_atual, senha_atual):
                flash("A senha atual está incorreta.", "erro")
                return redirect(url_for("perfil"))

            # nova senha precisa ser forte
            if not validar_senha(nova_senha):
                flash("A nova senha precisa ter 8 caracteres ou mais, uma letra maiúscula, uma minúscula, um número e um símbolo.","erro")
                return redirect(url_for("perfil"))

            senhas_anteriores = buscar_ultimas_senhas(id_usuario)  #para nao utilizar as ultimas 3 senhas

            # não pode ser igual à senha atual
            if check_password_hash(hash_atual, nova_senha):
                flash("A nova senha deve ser diferente da senha atual.", "erro")
                return redirect(url_for("perfil"))

            # nem igual a alguma das 3 últimas do histórico
            # Compara a nova senha com cada hash do histórico. Não dá para comparar texto com texto porque
            # o hash é diferente a cada geração; por isso se usa check_password_hash em cada um.
            for senha_antiga in senhas_anteriores:
                if check_password_hash(senha_antiga, nova_senha):
                    flash("Não é permitido reutilizar as três últimas senhas.", "erro")
                    return redirect(url_for("perfil"))

            novo_hash = generate_password_hash(nova_senha)

        if foto and foto.filename:
            extensao = os.path.splitext(foto.filename)[1].lower() #transf tudo em minúscula

            if extensao not in (".jpg", ".jpeg", ".png", ".webp"):  #ver se a extensao é uma dessas, se n for manda
                flash("Escolha uma imagem JPG, JPEG, PNG ou WEBP.", "erro")
                return redirect(url_for("perfil"))

            # f-string: o que está entre {} é substituído pelo valor da variável. uuid4().hex gera um código aleatório
            # único (ex.: 9f1c2a...), então o nome final fica algo como perfil_3_9f1c2a....png e nunca se repete.
            nome_foto = f'perfil_{id_usuario}_{uuid4().hex}{extensao}'  #criar um nome específico para não ter iguais
            pasta_uploads = os.path.join(app.root_path, "static", "uploads")
            os.makedirs(pasta_uploads, exist_ok=True)  #criar pasta caso ela não exista
            caminho_foto = os.path.join(pasta_uploads, nome_foto)
            foto.save(caminho_foto)  # grava o arquivo no disco

        conexao = conectar_banco()

        try:
            cursor = conexao.cursor()

            try:
                # se a senha mudou, guarda a senha ANTIGA no histórico
                if novo_hash is not None:
                    cursor.execute(
                        """
                        INSERT INTO HISTORICO_SENHA (SENHA, ID_USUARIO, DATA_ALTERACAO)
                        VALUES (?, ?, ?)
                        """,
                        (hash_atual, id_usuario, datetime.now())
                    )

                # 4 combinações de UPDATE: com/sem foto nova e com/sem senha nova
                if nome_foto:
                    if novo_hash is not None:
                        cursor.execute(
                            """
                            UPDATE USUARIO
                            SET NOME = ?, EMAIL = ?, SENHA = ?, FOTO_PERFIL = ?
                            WHERE ID_USUARIO = ?
                            """,
                            (nome, email, novo_hash, nome_foto, id_usuario)
                        )
                    else:
                        cursor.execute(
                            """
                            UPDATE USUARIO
                            SET NOME = ?, EMAIL = ?, FOTO_PERFIL = ?
                            WHERE ID_USUARIO = ?
                            """,
                            (nome, email, nome_foto, id_usuario)
                        )
                else:
                    if novo_hash is not None:
                        cursor.execute(
                            """
                            UPDATE USUARIO
                            SET NOME = ?, EMAIL = ?, SENHA = ?
                            WHERE ID_USUARIO = ?
                            """,
                            (nome, email, novo_hash, id_usuario)
                        )
                    else:
                        cursor.execute(
                            """
                            UPDATE USUARIO
                            SET NOME = ?, EMAIL = ?
                            WHERE ID_USUARIO = ?
                            """,
                            (nome, email, id_usuario)
                        )

                conexao.commit()

            except Exception:
                conexao.rollback()
                raise  # repassa o erro para o except externo

            finally:
                cursor.close()

        finally:
            conexao.close()

        # atualiza a sessão para o cabeçalho mostrar os dados novos
        session["usuario_nome"] = nome
        session["usuario_email"] = email

        if nome_foto:
            session["usuario_foto"] = nome_foto

        flash("Perfil atualizado com sucesso!", "sucesso")
        return redirect(url_for("perfil"))

    except Exception:
        app.logger.exception("Erro ao atualizar o perfil.")
        flash("Não foi possível salvar os dados.", "erro")
        return redirect(url_for("perfil"))


@app.route("/perfil/excluir-foto", methods=["POST"])
def excluir_foto_perfil():
    # remove a foto do usuário (banco + arquivo) e volta para a imagem padrão
    if "usuario_id" not in session:
        return redirect(url_for("login"))

    id_usuario = session["usuario_id"]
    conexao = conectar_banco()
    cursor = conexao.cursor()

    try:
        # guarda o nome da foto antiga para apagar o arquivo depois
        cursor.execute("SELECT FOTO_PERFIL FROM USUARIO WHERE ID_USUARIO = ?", (id_usuario,))
        usuario = cursor.fetchone()
        foto_antiga = usuario[0] if usuario else None

        cursor.execute("UPDATE USUARIO SET FOTO_PERFIL = NULL WHERE ID_USUARIO = ?", (id_usuario,))
        conexao.commit()

        session["usuario_foto"] = ""

        if foto_antiga:
            caminho_foto = os.path.join(app.root_path, "static", "uploads", foto_antiga)  #se não mudou a foto
            if os.path.isfile(caminho_foto):
                os.remove(caminho_foto)   #remover a foto

        flash("Foto de perfil removida. A imagem padrão será usada.", "sucesso")

    except Exception:
        conexao.rollback()
        app.logger.exception("Erro ao remover foto de perfil.")
        flash("Não foi possível remover a foto de perfil.", "erro")

    finally:
        cursor.close()
        conexao.close()

    return redirect(url_for("perfil"))


@app.route("/perfil/excluir", methods=["POST"])
def excluir_perfil():
    # exclui a própria conta e todos os dados ligados a ela
    # (se a conta estiver bloqueada, esta rota na verdade DESBLOQUEIA)

    if "usuario_id" not in session:
        return redirect(url_for("login"))

    id_usuario = session["usuario_id"]
    conexao = conectar_banco()
    cursor = conexao.cursor()
    try:
        cursor.execute("SELECT BLOQUEADO FROM USUARIO WHERE ID_USUARIO = ?", (id_usuario,))
        status_usuario = cursor.fetchone()
        if status_usuario and status_usuario[0]:
            # perfil bloqueado: zera tentativas e libera o acesso
            cursor.execute("""
                UPDATE USUARIO
                SET BLOQUEADO = ?, TENTATIVAS_LOGIN = ?
                WHERE ID_USUARIO = ?
            """, (False, 0, id_usuario))
            conexao.commit()
            flash("Perfil desbloqueado com sucesso.", "sucesso")
            return redirect(url_for("gerenciar_usuarios"))

        # exclusão em cascata manual: filhos primeiro (parcelas -> empréstimos -> simulações),
        # senão as chaves estrangeiras do banco impedem a exclusão
        cursor.execute("SELECT ID_SIMULACAO FROM SIMULACAO WHERE ID_USUARIO = ?", (id_usuario,))
        simulacoes = [x[0] for x in cursor.fetchall()]
        for id_simulacao in simulacoes:
            cursor.execute("SELECT ID_EMPRESTIMO FROM EMPRESTIMO WHERE ID_SIMULACAO = ?", (id_simulacao,))
            for emp in cursor.fetchall():
                cursor.execute("DELETE FROM PARCELA WHERE ID_EMPRESTIMO = ?", (emp[0],))
            cursor.execute("DELETE FROM EMPRESTIMO WHERE ID_SIMULACAO = ?", (id_simulacao,))
        cursor.execute("DELETE FROM SIMULACAO WHERE ID_USUARIO = ?", (id_usuario,))
        cursor.execute("DELETE FROM MOV_FINANCEIRA WHERE ID_USUARIO = ?", (id_usuario,))
        cursor.execute("DELETE FROM HISTORICO_SENHA WHERE ID_USUARIO = ?", (id_usuario,))
        cursor.execute("DELETE FROM USUARIO WHERE ID_USUARIO = ?", (id_usuario,))
        conexao.commit()
        session.clear()  # desloga, pois a conta não existe mais

        flash("Perfil excluído com sucesso.", "sucesso")
        return redirect(url_for("inicio"))

    except Exception:
        conexao.rollback()
        app.logger.exception("Erro ao excluir perfil.")
        flash("Não foi possível excluir o perfil.", "erro")
        return redirect(url_for("perfil"))
    finally:
        cursor.close()
        conexao.close()


# ============================================================
# MOVIMENTAÇÕES
# ============================================================

TIPO_RECEITA = 1   #ja definidos os valores aqui e no banco
TIPO_DESPESA = 0

PERIODOS = {"ultimos": "Últimos 3 Meses","proximos": "Próximos 3 Meses","todos": "Todo o Tempo",}
#parte definida das movimentações (chave = valor da URL, valor = texto exibido)


def conectar():
    # apelido de conectar_banco(), usado nas funções de movimentação
    return conectar_banco()


def id_usuario_movimentacao():
    # devolve o ID do usuário logado (ou None); filtra todas as consultas por dono
    return session.get("usuario_id")


def formatar_reais(valor):   #formatar os valores de dinheiro
    # Formato ":,.2f" = separador de milhar (,) + 2 casas decimais (.2f). float() garante que seja número.
    # O resultado vem no padrão americano (1,234.50); as 3 linhas seguintes trocam para o brasileiro.
    texto = f"{float(valor):,.2f}"   # 1234.5 -> "1,234.50" (padrão americano)
    texto = texto.replace(",", "X")  # troca a vírgula por marcador temporário
    texto = texto.replace(".", ",")  # ponto decimal vira vírgula
    return texto.replace("X", ".")   # marcador vira ponto de milhar -> "1.234,50"


def datas_do_periodo(periodo):
    # converte o nome do período em (data_inicio, data_fim)
    hoje = date.today()

    if periodo == "ultimos":   #parte das movimentações
        inicio = hoje - timedelta(days=90)  # 90 dias para trás
        fim = hoje
    elif periodo == "proximos":
        inicio = hoje
        fim = hoje + timedelta(days=90)  # 90 dias para frente
    else:
        # "todos": intervalo bem largo
        inicio = date(2000, 1, 1)
        fim = date(2100, 1, 1)

    return inicio, fim


def montar_movimentacao(linha):
    # transforma uma linha do banco em um dicionário pronto para o template
    # linha: 0=id, 1=data, 2=descrição, 3=tipo, 4=valor, 5=classificação
    if linha[3] == TIPO_RECEITA:
        categoria = "Receita"
        classe = "receita"   # classe CSS (cor verde)
        sinal = "+"
    else:
        categoria = "Despesa"
        classe = "despesa"   # classe CSS (cor vermelha)
        sinal = "-"

    classificacao = "Fixa" if linha[5] == 1 else "Variável"  # 1 = fixa (repete todo mês)
    descricao = linha[2] or ""
    valor = float(linha[4])

    return {
        "id": linha[0],
        # strftime formata a data como texto: %d = dia, %m = mês, %Y = ano com 4 dígitos.
        # "data" mostra só dia/mês na lista; "data_completa" mostra dia/mês/ano.
        "data": linha[1].strftime("%d/%m"),
        "data_completa": linha[1].strftime("%d/%m/%Y"),
        "descricao": descricao,
        "categoria": categoria,
        "classe": classe,
        "sinal": sinal,
        "classificacao": classificacao,
        "valor": valor,
        "valor_texto": formatar_reais(valor)
    }


def buscar_movimentacoes(data_inicio, data_fim):
    # lista as movimentações do usuário no intervalo (mais recentes primeiro)
    con = conectar()

    try:
        cursor = con.cursor()
        try:
            # NOT LIKE ignora as "Parcela de empréstimo ..." (parcelas ainda não pagas não contam como despesa)
            cursor.execute(
                """
                SELECT
                    ID_MOV_FINANCEIRA, DATA_LANCAMENTO, DESCRICAO,
                    TIPO, VALOR, CLASSIFICACAO
                FROM MOV_FINANCEIRA
                WHERE ID_USUARIO = ?
                  AND DATA_LANCAMENTO >= ?
                  AND DATA_LANCAMENTO <= ?
                  AND DESCRICAO NOT LIKE 'Parcela de empréstimo %'
                ORDER BY DATA_LANCAMENTO DESC, ID_MOV_FINANCEIRA DESC
                """,
                (id_usuario_movimentacao(), data_inicio, data_fim)
            )

            # List comprehension: cria uma lista nova aplicando montar_movimentacao a cada linha do resultado.
            # É o mesmo que fazer um for com append, só que em uma linha.
            return [montar_movimentacao(linha)for linha in cursor.fetchall()]
        finally:
            cursor.close()
    finally:
        con.close()


def buscar_movimentacao(id_mov):
    # busca UMA movimentação; o filtro por ID_USUARIO impede ver dados de outras pessoas
    con = conectar()

    try:
        cursor = con.cursor()
        try:
            cursor.execute(
                """
                SELECT ID_MOV_FINANCEIRA, DATA_LANCAMENTO, DESCRICAO, TIPO, VALOR, CLASSIFICACAO
                FROM MOV_FINANCEIRA
                WHERE ID_MOV_FINANCEIRA = ? AND ID_USUARIO = ?
                  AND DESCRICAO NOT LIKE 'Parcela de empréstimo %'
                """,
                (id_mov, id_usuario_movimentacao())
            )

            linha = cursor.fetchone()
            return montar_movimentacao(linha) if linha else None

        finally:
            cursor.close()
    finally:
        con.close()


def somar(tipo, data_inicio=date(2000, 1, 1)):
    # soma todos os valores de um tipo (receita ou despesa) a partir de uma data
    con = conectar()

    try:
        cursor = con.cursor()
        try:
            cursor.execute(
                """
                SELECT VALOR
                FROM MOV_FINANCEIRA
                WHERE ID_USUARIO = ?
                  AND TIPO = ?
                  AND DATA_LANCAMENTO >= ?
                  AND DESCRICAO NOT LIKE 'Parcela de empréstimo %'
                """,
                (id_usuario_movimentacao(), tipo, data_inicio)
            )

            # fetchall() devolve todas as linhas. Para cada linha pega a coluna 0 (VALOR), converte em float e
            # sum() soma tudo. Se não houver linhas, a soma é 0.
            return sum(float(linha[0]) for linha in cursor.fetchall())

        finally:
            cursor.close()
    finally:
        con.close()


def somar_mes(tipo):   #calcular o período do mês atual
    hoje = date.today()   #obtem a data do pc e armazena na variável hoje
    # replace(day=1) cria uma cópia da data de hoje trocando só o dia para 1 (primeiro dia do mês atual).
    inicio = hoje.replace(day=1)   #identificar o começo do período que será consultado

    if hoje.month == 12:
        fim = date(hoje.year + 1, 1, 1)  #verifica se é dezembro e define o final do período como dia 1 de janeiro
    else:
        fim = date(hoje.year, hoje.month + 1, 1)  #se nao for define o primeiro dia do mes seguinte

    con = conectar()

    try:
        cursor = con.cursor()
        try:
            # fim é exclusivo (<): pega do dia 1 do mês atual até antes do dia 1 do próximo
            cursor.execute(
                """
                SELECT VALOR
                FROM MOV_FINANCEIRA
                WHERE ID_USUARIO = ?
                  AND TIPO = ?
                  AND DATA_LANCAMENTO >= ?
                  AND DATA_LANCAMENTO < ?
                  AND DESCRICAO NOT LIKE 'Parcela de empréstimo %'
                """,
                (id_usuario_movimentacao(), tipo, inicio, fim)
            )

            # fetchall() devolve todas as linhas. Para cada linha pega a coluna 0 (VALOR), converte em float e
            # sum() soma tudo. Se não houver linhas, a soma é 0.
            return sum(float(linha[0]) for linha in cursor.fetchall())

        finally:
            cursor.close()
    finally:
        con.close()


@app.route("/movimentacoes")
def movimentacoes():
    # tela principal de movimentações: lista + saldo + resumo dos últimos 30 dias
    if "usuario_id" not in session:
        flash("Faça login para acessar esta página.", "erro")
        return redirect(url_for("login"))

    periodo = request.args.get("periodo", "ultimos")  # lê ?periodo=... da URL

    if periodo not in PERIODOS:  # valor inválido volta ao padrão
        periodo = "ultimos"

    data_inicio, data_fim = datas_do_periodo(periodo)
    dados = buscar_movimentacoes(data_inicio, data_fim)

    # Saldo = tudo que entrou - tudo que saiu (desde o ano 2000, ou seja, todo o histórico).
    saldo = somar(TIPO_RECEITA) - somar(TIPO_DESPESA)  #calcular o saldo disponível

    inicio_30_dias = date.today() - timedelta(days=30)
    receitas = somar(TIPO_RECEITA, inicio_30_dias)  #soma de receitas e embaixo soma de despesas
    despesas = somar(TIPO_DESPESA, inicio_30_dias)

    return render_template(
        "movimentacoes.html",
        dados=dados,
        saldo_texto=formatar_reais(saldo),
        receitas_texto=formatar_reais(receitas),
        despesas_texto=formatar_reais(despesas),
        periodo=periodo
    )


@app.route("/nova-movimentacao", methods=["GET", "POST"])
def nova_movimentacao():
    # cria uma receita/despesa; se for "fixa", repete o lançamento pelos próximos N meses
    if "usuario_id" not in session:
        flash("Faça login para acessar esta página.", "erro")
        return redirect(url_for("login"))

    if request.method == "POST":   #receber as informações
        tipo = request.form.get("tipo", "").strip()  # aqui "tipo" é a descrição digitada (ex.: Salário)
        categoria = request.form.get("categoria", "").strip()  # Receita ou Despesa
        valor = request.form.get("valor", "").strip()
        classificacao = request.form.get("classificacao", "2")  # "1" = fixa, "2" = variável
        meses = request.form.get("meses", "1")  # quantos meses repetir (só vale para fixa)

        if not tipo:
            flash("Informe o tipo de movimentação.", "erro")
            return redirect(url_for("nova_movimentacao"))

        if categoria not in ("Receita", "Despesa"):
            flash("Selecione Receita ou Despesa.", "erro")
            return redirect(url_for("nova_movimentacao"))

        try:
            # Se o texto não for um número (ex.: "abc"), converter_valor lança ValueError; o except coloca 0,
            # e logo abaixo o "valor_numerico <= 0" rejeita com mensagem amigável.
            valor_numerico = converter_valor(valor)  # "1.234,56" -> 1234.56
        except (ValueError, AttributeError):
            valor_numerico = 0

        if valor_numerico <= 0:
            flash("Insira um valor válido.", "erro")
            return redirect(url_for("nova_movimentacao"))

        if classificacao == "1":
            classificacao_numero = 1

            try:
                quantidade = int(meses)
            except ValueError:
                quantidade = 0

            if quantidade < 1 or quantidade > 120:  # limite de 10 anos
                flash("Informe de 1 a 120 meses.", "erro")
                return redirect(url_for("nova_movimentacao"))
        else:
            classificacao_numero = 2
            quantidade = 1  # variável: um único lançamento

        # Expressão condicional (if em uma linha): valor_se_verdadeiro if condição else valor_se_falso.
        # Converte o texto "Receita"/"Despesa" para o número 1/0 que o banco guarda.
        tipo_numero = ( TIPO_RECEITA if categoria == "Receita" else TIPO_DESPESA)  #classificação de 1 e 2

        con = conectar()

        try:
            cursor = con.cursor()

            try:
                hoje = date.today()

                # cria um lançamento por mês
                for i in range(quantidade):
                    total_meses = hoje.month - 1 + i          # meses contados a partir de janeiro do ano atual
                    ano = hoje.year + total_meses // 12       # a cada 12 meses avança 1 ano
                    mes = total_meses % 12 + 1                # mês de 1 a 12
                    ultimo_dia = calendar.monthrange(ano, mes)[1]  # último dia do mês (28..31)
                    dia = min(hoje.day, ultimo_dia)           # dia 31 em fevereiro vira 28/29
                    data_mov = date(ano, mes, dia)

                    cursor.execute(
                        """
                        INSERT INTO MOV_FINANCEIRA
                        (TIPO, VALOR, DATA_LANCAMENTO, DESCRICAO, ID_USUARIO, CLASSIFICACAO)
                        VALUES (?, ?, ?, ?, ?, ?)
                        """,
                        (
                            tipo_numero,
                            valor_numerico,
                            data_mov,
                            tipo,
                            id_usuario_movimentacao(),
                            classificacao_numero
                        )
                    )

                con.commit()  # confirma todos os meses de uma vez

            except Exception:
                con.rollback()
                raise

        finally:
            con.close()

        # guarda os dados na sessão para a tela de confirmação
        # Guardamos na sessão porque o redirect abaixo cria uma NOVA requisição, que não enxerga as variáveis desta.
        # (padrão Post/Redirect/Get: evita duplicar o lançamento se o usuário apertar F5.)
        session["ultima_movimentacao"] = {
            "valor_texto": formatar_reais(valor_numerico),
            "categoria": categoria,
            "descricao": tipo,
            "classe": "receita" if categoria == "Receita" else "despesa"
        }

        return redirect(url_for("movimentacao_registrada"))

    return render_template("nova_movimentacao.html")


@app.route("/movimentacao-registrada")
def movimentacao_registrada():
    # tela "movimentação registrada"; pop lê e apaga da sessão, então só aparece uma vez
    dados = session.pop("ultima_movimentacao", None)

    if dados is None:  # acessou direto sem ter criado nada
        return redirect(url_for("movimentacoes"))

    return render_template("movimentacao_registrada.html", dados=dados)


# <int:id_mov> é uma parte variável da URL: /movimentacao/15 chama a função com id_mov = 15.
# O "int:" garante que só números sejam aceitos (qualquer outra coisa gera erro 404 automaticamente).
@app.route("/movimentacao/<int:id_mov>")
def visualizar_movimentacao(id_mov):
    # mostra os detalhes de uma movimentação (<int:id_mov> vem da URL)
    mov = buscar_movimentacao(id_mov)

    if "usuario_id" not in session:
        flash("Faça login para acessar esta página.", "erro")
        return redirect(url_for("login"))

    if mov is None:
        flash("Movimentação não encontrada.", "erro")
        return redirect(url_for("movimentacoes"))

    return render_template("visualizar_movimentacao.html", mov=mov)


@app.route("/movimentacao/<int:id_mov>/editar", methods=["GET", "POST"])
def editar_movimentacao(id_mov):
    # só permite editar a DESCRIÇÃO da movimentação
    mov = buscar_movimentacao(id_mov)

    if mov is None:
        flash("Movimentação não encontrada.", "erro")
        return redirect(url_for("movimentacoes"))

    if request.method == "POST":
        descricao = request.form.get("descricao", "").strip()

        if not descricao:
            flash("Informe a descrição da movimentação.", "erro")
            return redirect(url_for("editar_movimentacao", id_mov=id_mov))

        if len(descricao) > 100:
            flash("A descrição pode ter no máximo 100 caracteres.", "erro")
            return redirect(url_for("editar_movimentacao", id_mov=id_mov))

        con = conectar()

        try:
            cursor = con.cursor()
            try:
                cursor.execute(
                    """
                    UPDATE MOV_FINANCEIRA
                    SET DESCRICAO = ?
                    WHERE ID_MOV_FINANCEIRA = ? AND ID_USUARIO = ?
                    """,
                    (descricao, id_mov, id_usuario_movimentacao())
                )
                con.commit()
            except Exception:
                con.rollback()
                raise
        finally:
            con.close()

        flash("Descrição atualizada com sucesso!", "sucesso")
        return redirect(
            url_for("visualizar_movimentacao", id_mov=id_mov)
        )

    return render_template("editar_movimentacao.html", mov=mov)


@app.route("/movimentacao/<int:id_mov>/excluir", methods=["POST"])
def excluir_movimentacao(id_mov):
    # exclui a movimentação; se for FIXA, apaga também as repetições iguais (mesma descrição, tipo e valor)
    mov = buscar_movimentacao(id_mov)

    if mov is None:
        flash("Movimentação não encontrada.", "erro")
        return redirect(url_for("movimentacoes"))

    con = conectar()
    id_usuario = id_usuario_movimentacao()

    try:
        cursor = con.cursor()

        try:
            if mov["classificacao"] == "Fixa":
                tipo_numero = (
                    TIPO_RECEITA
                    if mov["categoria"] == "Receita"
                    else TIPO_DESPESA
                )

                # busca todas as fixas com mesma descrição e tipo
                cursor.execute(
                    """
                    SELECT ID_MOV_FINANCEIRA, VALOR
                    FROM MOV_FINANCEIRA
                    WHERE ID_USUARIO = ?
                      AND CLASSIFICACAO = 1
                      AND TIPO = ?
                      AND DESCRICAO = ?
                    """,
                    (id_usuario, tipo_numero, mov["descricao"])
                )

                candidatas = cursor.fetchall()
                quantidade = 0

                # apaga só as que também têm o mesmo valor
                for candidata in candidatas:
                    # Compara o valor no Python (e não no SQL) para evitar problema de tipo/arredondamento do banco.
                    # Só apaga as fixas com valor idêntico, preservando outra fixa de mesmo nome mas valor diferente.
                    if float(candidata[1]) == mov["valor"]:
                        cursor.execute(
                            """
                            DELETE FROM MOV_FINANCEIRA
                            WHERE ID_MOV_FINANCEIRA = ? AND ID_USUARIO = ?
                            """,
                            (candidata[0], id_usuario)
                        )
                        quantidade += 1

                if quantidade == 1:
                    mensagem = "Movimentação excluída com sucesso!"
                else:
                    mensagem = (
                        f"{quantidade} movimentações fixas iguais "
                        "foram excluídas com sucesso!"
                    )
            else:
                # variável: apaga apenas esta
                cursor.execute(
                    """
                    DELETE FROM MOV_FINANCEIRA
                    WHERE ID_MOV_FINANCEIRA = ? AND ID_USUARIO = ?
                    """,
                    (id_mov, id_usuario)
                )
                mensagem = "Movimentação excluída com sucesso!"

            con.commit()

        except Exception:
            con.rollback()
            raise

    finally:
        con.close()

    flash(mensagem, "sucesso")
    return redirect(url_for("movimentacoes"))


# ============================================================
# RELATÓRIO PDF
# ============================================================

def texto_pdf(texto):
    # a fonte padrão do FPDF só aceita latin-1; caracteres fora dele viram "?" em vez de dar erro
    texto = str(texto).encode("latin-1", "replace")
    return texto.decode("latin-1")


@app.route("/emprestimos/<int:id_emprestimo>/pdf")
def pdf_emprestimo(id_emprestimo):
    # relatório em PDF de UM empréstimo: dados do empréstimo + todas as parcelas
    if "usuario_id" not in session:
        return redirect(url_for("login"))

    conexao = conectar_banco()
    cursor = conexao.cursor()
    try:
        # busca o empréstimo; o filtro por ID_USUARIO impede baixar o de outra pessoa
        cursor.execute("""
            SELECT e.ID_EMPRESTIMO, e.DATA, e.STATUS, s.VALOR_EMPRESTIMO,
                   s.NUM_PARCELAS, s.VALOR_TOTAL, s.RISCO
            FROM EMPRESTIMO e JOIN SIMULACAO s ON e.ID_SIMULACAO = s.ID_SIMULACAO
            WHERE e.ID_EMPRESTIMO = ? AND s.ID_USUARIO = ?
        """, (id_emprestimo, session["usuario_id"]))
        emp = cursor.fetchone()
        if not emp:
            flash("Empréstimo não encontrado.", "erro")
            return redirect(url_for("historico_emprestimos"))

        # reajusta as parcelas pendentes pela taxa do ano, igual à tela de detalhes,
        # para o PDF mostrar os mesmos valores que o usuário vê
        taxa_atual = buscar_taxa_por_ano(date.today().year)
        if taxa_atual:
            atualizar_parcelas_pendentes(cursor, id_emprestimo, session["usuario_id"], taxa_atual["juros"])
            conexao.commit()

        cursor.execute("""
            SELECT NUM_PARCELAS, DATA_VENCIMENTO, VALOR, STATUS
            FROM PARCELA WHERE ID_EMPRESTIMO = ? ORDER BY NUM_PARCELAS
        """, (id_emprestimo,))
        parcelas = cursor.fetchall()
    finally:
        cursor.close()
        conexao.close()

    data_emprestimo = emp[1].strftime("%d/%m/%Y") if isinstance(emp[1], (date, datetime)) else str(emp[1])

    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()

    # título e subtítulo (mesmo estilo dos outros relatórios)
    pdf.set_font("Arial", "B", 16)
    pdf.cell(190, 12, texto_pdf("Detalhes do Empréstimo - CredMais"), ln=True, align="C")
    pdf.set_font("Arial", size=10)
    pdf.cell(190, 8, texto_pdf("Empréstimo nº " + str(emp[0]) + " | Gerado em " +
                               datetime.now().strftime("%d/%m/%Y %H:%M")), ln=True, align="C")
    pdf.ln(5)
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.ln(5)

    # bloco com os dados do empréstimo: rótulo à esquerda e valor à direita, cada linha com borda
    pdf.set_font("Arial", "B", 11)
    pdf.cell(190, 8, texto_pdf("Dados do empréstimo"), ln=True)
    pdf.set_font("Arial", size=10)
    dados = [
        ("Data", data_emprestimo),
        ("Valor emprestado", "R$ " + formatar_reais(float(emp[3] or 0))),
        ("Número de parcelas", str(emp[4])),
        ("Total a pagar", "R$ " + formatar_reais(float(emp[5] or 0))),
        ("Risco", str(emp[6] or "-")),
        ("Status", str(emp[2] or "Em andamento")),
    ]
    for rotulo, valor in dados:
        pdf.cell(60, 8, texto_pdf(rotulo), border=1)
        pdf.cell(130, 8, texto_pdf(valor), border=1, ln=True)
    pdf.ln(8)

    # tabela de parcelas
    def cabecalho_tabela():
        pdf.set_font("Arial", "B", 10)
        pdf.cell(25, 10, "Parcela", border=1)
        pdf.cell(55, 10, "Vencimento", border=1)
        pdf.cell(60, 10, "Valor", border=1)
        pdf.cell(50, 10, "Status", border=1, ln=True)
        pdf.set_font("Arial", size=9)

    pdf.set_font("Arial", "B", 11)
    pdf.cell(190, 8, texto_pdf("Parcelas"), ln=True)
    cabecalho_tabela()

    total_pago = 0
    total_pendente = 0
    for p in parcelas:
        if pdf.get_y() > 265:          # perto do fim da página: nova página e repete o cabeçalho
            pdf.add_page()
            cabecalho_tabela()
        valor = float(p[2] or 0)
        status = p[3] or "Pendente"
        if status == "Pago":
            total_pago += valor
        else:
            total_pendente += valor
        vencimento = p[1].strftime("%d/%m/%Y") if isinstance(p[1], (date, datetime)) else str(p[1])
        pdf.cell(25, 10, str(p[0]), border=1)
        pdf.cell(55, 10, vencimento, border=1)
        pdf.cell(60, 10, texto_pdf("R$ " + formatar_reais(valor)), border=1)
        pdf.cell(50, 10, texto_pdf(status), border=1, ln=True)

    # resumo final centralizado, como no relatório de movimentações
    pdf.ln(8)
    pdf.set_font("Arial", "B", 11)
    pdf.cell(190, 10, texto_pdf("Total pago: R$ " + formatar_reais(total_pago)), ln=True, align="C")
    pdf.cell(190, 10, texto_pdf("Total pendente: R$ " + formatar_reais(total_pendente)), ln=True, align="C")

    caminho = os.path.join(app.root_path, "emprestimo_" + str(id_emprestimo) + ".pdf")
    pdf.output(caminho)
    return send_file(caminho, as_attachment=True, mimetype="application/pdf",
                     download_name="emprestimo_" + str(id_emprestimo) + ".pdf")

# ============================================================
# TAXAS DE JUROS
# ============================================================

def converter_taxa(linha):
    # transforma a linha do banco em dicionário (mantém nomes duplicados "id"/"id_taxa_juros", "juros"/"taxa_mensal" para compatibilidade com os templates)
    data_referencia = linha[1]

    # O banco pode devolver data com hora (datetime). .date() descarta a hora para ficar só com a data.
    # isinstance(x, tipo) confere se o valor é daquele tipo.
    if isinstance(data_referencia, datetime):
        data_referencia = data_referencia.date()

    return {
        "id": linha[0],
        "id_taxa_juros": linha[0],
        "data_referencia": data_referencia,
        "ano": data_referencia.year,
        "juros": float(linha[2]),
        "taxa_mensal": float(linha[2])
    }


def buscar_taxas_banco():
    # lista todas as taxas cadastradas, da mais recente para a mais antiga
    conexao = conectar_banco()

    try:
        cursor = conexao.cursor()

        try:
            cursor.execute(
                """
                SELECT ID_TAXA_JUROS, DATA_REFERENCIA, TAXA_MENSAL
                FROM TAXA_JUROS
                ORDER BY DATA_REFERENCIA DESC, ID_TAXA_JUROS DESC
                """
            )

            return [
                converter_taxa(linha)
                for linha in cursor.fetchall()
            ]

        finally:
            cursor.close()

    finally:
        conexao.close()


def buscar_taxa_por_ano(ano):
    # retorna a taxa do ano informado (a mais recente, se houver mais de uma) ou None
    conexao = conectar_banco()

    try:
        cursor = conexao.cursor()

        try:
            cursor.execute(
                """
                SELECT FIRST 1
                    ID_TAXA_JUROS, DATA_REFERENCIA, TAXA_MENSAL
                FROM TAXA_JUROS
                WHERE EXTRACT(YEAR FROM DATA_REFERENCIA) = ?
                ORDER BY ID_TAXA_JUROS DESC
                """,
                (ano,)
            )

            linha = cursor.fetchone()

            if linha is None:
                return None

            return converter_taxa(linha)

        finally:
            cursor.close()

    finally:
        conexao.close()


def buscar_taxa_por_id(id_taxa):
    # retorna a taxa pelo ID ou None
    conexao = conectar_banco()

    try:
        cursor = conexao.cursor()

        try:
            cursor.execute(
                """
                SELECT ID_TAXA_JUROS, DATA_REFERENCIA, TAXA_MENSAL
                FROM TAXA_JUROS
                WHERE ID_TAXA_JUROS = ?
                """,
                (id_taxa,)
            )

            linha = cursor.fetchone()

            if linha is None:
                return None

            return converter_taxa(linha)

        finally:
            cursor.close()

    finally:
        conexao.close()


def validar_dados_taxa(ano_texto, juros_texto):
    # converte os textos do formulário em (ano, juros); lança ValueError com mensagem amigável se algo estiver errado
    try:
        ano = int(ano_texto)
        juros = float(juros_texto.strip().replace(",", "."))  # aceita vírgula decimal

    except (ValueError, TypeError, AttributeError):
        # Converte o erro técnico (ex.: "invalid literal for int") em uma mensagem amigável.
        # Quem chama esta função captura com "except ValueError as erro" e mostra str(erro) ao usuário.
        raise ValueError("Informe um ano e uma taxa válidos.")

    if ano < 1900 or ano > 9999:
        raise ValueError("Informe um ano válido.")

    if juros < 0:
        raise ValueError("A taxa de juros não pode ser negativa.")

    return ano, juros


@app.route("/taxas/editar", methods=["GET", "POST"])
def editar_taxa():
    # GET: mostra a taxa de um ano (ou a mais recente) | POST: altera o valor da taxa de um ano já cadastrado
    if "usuario_id" not in session:
        flash("Faça login para acessar esta página.", "erro")
        return redirect(url_for("login"))

    if request.method == "POST":
        ano_texto = request.form.get("ano", "").strip()
        juros_texto = request.form.get("juros", "").strip()

        try:
            ano, juros = validar_dados_taxa(ano_texto, juros_texto)
            taxa_existente = buscar_taxa_por_ano(ano)

            if taxa_existente is None:
                flash("Não existe uma taxa cadastrada para esse ano.", "erro")
                return redirect(url_for("editar_taxa"))

            conexao = conectar_banco()

            try:
                cursor = conexao.cursor()
                cursor.execute(
                    """
                    UPDATE TAXA_JUROS
                    SET TAXA_MENSAL = ?
                    WHERE ID_TAXA_JUROS = ?
                    """,
                    (juros, taxa_existente["id"])
                )
                conexao.commit()
                cursor.close()
            finally:
                conexao.close()

            flash("Taxa atualizada com sucesso!", "sucesso")
            return redirect(url_for("editar_taxa", ano=ano))

        # "as erro" guarda o objeto do erro; str(erro) devolve o texto que foi escrito no raise ValueError("...").
        except ValueError as erro:
            flash(str(erro), "erro")  # mensagem vinda de validar_dados_taxa
            return redirect(url_for("editar_taxa"))

        except Exception:
            app.logger.exception("Erro ao editar taxa.")
            flash("Não foi possível salvar as alterações.", "erro")
            return redirect(url_for("editar_taxa"))

    # ---- GET ----
    ano_texto = request.args.get("ano", "").strip()

    try:
        if ano_texto:
            taxa = buscar_taxa_por_ano(int(ano_texto))
        else:
            taxas = buscar_taxas_banco()
            taxa = taxas[0] if taxas else {"ano": "", "juros": ""}  # sem taxas: formulário vazio

    except ValueError:
        taxa = {"ano": "", "juros": ""}
        flash("O ano informado é inválido.", "erro")

    except Exception:
        app.logger.exception("Erro ao carregar taxa para edição.")
        taxa = {"ano": "", "juros": ""}
        flash("Não foi possível carregar as taxas do banco.", "erro")

    if taxa is None:
        taxa = {"ano": "", "juros": ""}
        flash("Não foi encontrada uma taxa para esse ano.", "erro")

    return render_template("editar_taxas.html", taxa=taxa)


@app.route("/taxas/cadastrar", methods=["GET", "POST"])
def cadastrar_taxa():
    # cadastra uma taxa nova (uma por ano; a data de referência é sempre 01/01 do ano)
    taxa = {"ano": "", "juros": ""}
    if "usuario_id" not in session:
        flash("Faça login para acessar esta página.", "erro")
        return redirect(url_for("login"))

    if request.method == "POST":
        ano_texto = request.form.get("ano", "").strip()
        juros_texto = request.form.get("juros", "").strip()

        # guarda o que foi digitado para reexibir no formulário em caso de erro
        taxa = {
            "ano": ano_texto,
            "juros": juros_texto
        }

        try:
            ano, juros = validar_dados_taxa(ano_texto, juros_texto)
            taxa_existente = buscar_taxa_por_ano(ano)

            if taxa_existente is not None:
                flash(f"Já existe uma taxa cadastrada para o ano {ano}.", "erro")
                return render_template("cadastrar_taxas.html", taxa=taxa)

            # O banco guarda uma data completa, então cada taxa anual usa 1º de janeiro do ano como referência.
            data_referencia = date(ano, 1, 1)
            conexao = conectar_banco()

            try:
                cursor = conexao.cursor()

                try:
                    cursor.execute(
                        """
                        INSERT INTO TAXA_JUROS
                            (DATA_REFERENCIA, TAXA_MENSAL)
                        VALUES (?, ?)
                        """,
                        (data_referencia, juros)
                    )
                    conexao.commit()
                except Exception:
                    conexao.rollback()
                    raise
                finally:
                    cursor.close()
            finally:
                conexao.close()

            flash("Taxa cadastrada com sucesso!", "sucesso")
            return redirect(url_for("cadastrar_taxa"))

        except ValueError as erro:
            flash(str(erro), "erro")
            return render_template("cadastrar_taxas.html", taxa=taxa)

        except Exception:
            app.logger.exception("Erro ao cadastrar taxa.")
            flash("Não foi possível cadastrar a taxa no banco de dados.", "erro")
            return render_template("cadastrar_taxas.html", taxa=taxa)

    return render_template("cadastrar_taxas.html", taxa=taxa)


@app.route("/taxas")
def listar_taxas():
    # página que lista todas as taxas
    try:
        taxas = buscar_taxas_banco()
    except Exception:
        app.logger.exception("Erro ao listar taxas.")
        flash("Não foi possível consultar as taxas no banco.", "erro")
        taxas = []

    return render_template("listar_taxas.html", taxas=taxas)


@app.route("/taxas/administrar")
def administrar_taxas():
    # painel de administração de taxas (com opções de cadastrar/editar)
    try:
        taxas = buscar_taxas_banco()
    except Exception:
        app.logger.exception("Erro ao carregar administração de taxas.")
        flash("Não foi possível consultar as taxas no banco.", "erro")
        taxas = []

    return render_template("administrar_taxas.html", taxas=taxas)


@app.route("/logo_taxas")
def logo_taxas():
    # imagem usada nas telas de taxas
    caminho = os.path.join(app.root_path, "static", "uploads")
    return send_from_directory(caminho, "logo_taxas.png")


@app.route("/icone_taxas")
def icone_taxas():
    # ícone usado nas telas de taxas
    caminho = os.path.join(app.root_path, "static", "uploads")
    return send_from_directory(caminho, "icone_taxas.png")


# ============================================================
# DASHBOARD
# ============================================================

def gerar_grafico_dashboard(id_usuario):
    # gera um gráfico de barras (SVG) com receitas x despesas dos últimos 6 meses e devolve a URL do arquivo
    hoje = date.today()
    primeiro_mes = hoje.year * 12 + hoje.month - 1 - 5   # número absoluto do mês de 5 meses atrás (ano*12+mês)
    ano_inicio = primeiro_mes // 12
    mes_inicio = primeiro_mes % 12 + 1
    data_inicio = date(ano_inicio, mes_inicio, 1)        # dia 1 do primeiro mês do gráfico

    conexao = conectar_banco()
    cursor = conexao.cursor()
    try:
        # busca todas as movimentações do período (sem as parcelas de empréstimo não pagas)
        cursor.execute("""
            SELECT DATA_LANCAMENTO, TIPO, VALOR
            FROM MOV_FINANCEIRA
            WHERE ID_USUARIO = ? AND DATA_LANCAMENTO >= ? AND DATA_LANCAMENTO <= ?
              AND DESCRICAO NOT LIKE 'Parcela de empréstimo %'
            ORDER BY DATA_LANCAMENTO
        """, (id_usuario, data_inicio, hoje))
        registros = cursor.fetchall()
    finally:
        cursor.close()
        conexao.close()

    # monta a lista com os 6 meses, todos começando com receitas/despesas = 0
    meses = []
    for i in range(6):
        total_meses = primeiro_mes + i
        ano = total_meses // 12
        mes = total_meses % 12 + 1   #
        meses.append({"ano": ano, "mes": mes, "nome": f"{mes:02d}/{ano}","receitas": 0.0, "despesas": 0.0})

    # dicionário (ano, mês) -> mês, para achar rápido onde somar cada registro
    # Dicionário por compreensão: a chave é a tupla (ano, mês) e o valor é o próprio dicionário do mês.
    # Serve para achar o mês de cada registro rapidamente: meses_por_chave[(2026, 11)].
    meses_por_chave = {(item["ano"], item["mes"]): item for item in meses}
    for registro in registros:
        data_mov = registro[0]
        if isinstance(data_mov, datetime):
            data_mov = data_mov.date()
        chave = (data_mov.year, data_mov.month)
        if chave in meses_por_chave:
            # "or 0" protege caso o VALOR venha vazio (None), evitando erro ao converter.
            valor = float(registro[2] or 0)
            if registro[1] == TIPO_RECEITA:
                meses_por_chave[chave]["receitas"] += valor
            else:
                meses_por_chave[chave]["despesas"] += valor

    # configura o gráfico pygal (tamanho, grades, cores)
    # pygal.Bar cria um gráfico de barras. Os parâmetros ajustam altura, linhas de grade e legenda;
    # o Style define cores (hex), fundo e animação. Cada .add() abaixo é uma série (um grupo de barras).
    grafico = pygal.Bar(
        height=330,
        x_label_rotation=0,
        show_y_guides=True,
        show_x_guides=False,
        show_legend=False,
        style=pygal.style.Style(
            background="white",
            plot_background="white",
            foreground="#59677D",
            foreground_strong="#153779",
            foreground_subtle="#E8EDF5",
            colors=("#16A879", "#F44A4D"),  # azul = receitas, verde = despesas
            opacity=0.95,
            opacity_hover=1,
            transition="400ms"
        )
    )
    grafico.title = ""
    grafico.x_labels = [item["nome"] for item in meses]  # rótulos "MM/AAAA"
    grafico.add("Receitas", [round(item["receitas"], 2) for item in meses])
    grafico.add("Despesas", [round(item["despesas"], 2) for item in meses])

    # salva o SVG em static/graficos e devolve a URL pública
    pasta_graficos = os.path.join(app.root_path, "static", "graficos")
    os.makedirs(pasta_graficos, exist_ok=True)
    caminho_svg = os.path.join(pasta_graficos, "grafico_dashboard.svg")
    grafico.render_to_file(caminho_svg)
    return url_for("static", filename="graficos/grafico_dashboard.svg")


@app.route("/dashboard")
def dashboard():
    # tela principal após o login: resumo financeiro, parcelas futuras e gráfico
    if "usuario_id" not in session:
        return redirect(url_for("login"))

    hoje = date.today()
    data_atual = hoje.strftime("%d/%m/%Y")
    id_usuario = session["usuario_id"]
    parcelas_futuras = []
    comprometimento_anual = 0  # soma das parcelas que vencem nos próximos 365 dias

    conexao = conectar_banco()
    cursor = conexao.cursor()
    try:
        # parcelas não pagas e ainda não vencidas, ligando PARCELA -> EMPRESTIMO -> SIMULACAO (onde está o usuário)
        cursor.execute("""
            SELECT p.VALOR, p.DATA_VENCIMENTO
            FROM PARCELA p
            JOIN EMPRESTIMO e ON p.ID_EMPRESTIMO = e.ID_EMPRESTIMO
            JOIN SIMULACAO s ON e.ID_SIMULACAO = s.ID_SIMULACAO
            WHERE s.ID_USUARIO = ? AND p.STATUS <> 'Pago'
              AND p.DATA_VENCIMENTO >= ?
            ORDER BY p.DATA_VENCIMENTO
        """, (id_usuario, hoje))
        for linha in cursor.fetchall():
            valor = float(linha[0] or 0)
            vencimento = linha[1]
            parcelas_futuras.append({"valor": valor, "data_objeto": vencimento})

        # soma só as parcelas que vencem em até 1 ano
        # timedelta representa um intervalo de tempo; somar 365 dias à data de hoje dá o limite de 1 ano à frente.
        limite_anual = hoje + timedelta(days=365)
        for parcela in parcelas_futuras:
            if parcela["data_objeto"] <= limite_anual:
                comprometimento_anual += parcela["valor"]
    except Exception:
        app.logger.exception("Erro ao carregar parcelas do dashboard.")
    finally:
        cursor.close()
        conexao.close()

    total_parcelas_futuras = sum(p["valor"] for p in parcelas_futuras)
    quantidade_parcelas_futuras = len(parcelas_futuras)

    # a lista está ordenada por vencimento, então a primeira é a próxima parcela
    if parcelas_futuras:
        proxima = parcelas_futuras[0]
        proxima_parcela_valor = formatar_reais(proxima["valor"])
        proxima_parcela_data = proxima["data_objeto"].strftime("%d/%m/%Y")
    else:
        proxima_parcela_valor = "-"
        proxima_parcela_data = "Nenhuma parcela cadastrada"

    # estima a renda anual = (receitas - despesas do mês) x 12 e calcula quanto % dela está comprometido
    # Estimativa simples: renda líquida do mês atual multiplicada por 12.
    # O "if renda_anual_estimada > 0" abaixo evita divisão por zero ou percentual negativo.
    renda_anual_estimada = (somar_mes(TIPO_RECEITA) - somar_mes(TIPO_DESPESA)) * 12
    if renda_anual_estimada > 0:
        percentual_comprometimento_anual = formatar_reais(
            (comprometimento_anual / renda_anual_estimada) * 100
        )
    else:
        percentual_comprometimento_anual = "-"

    svg = gerar_grafico_dashboard(id_usuario)

    return render_template(
        "dashboard.html",
        svg=svg,
        data_atual=data_atual,
        renda_mensal_liquida=formatar_reais(somar_mes(TIPO_RECEITA) - somar_mes(TIPO_DESPESA)),
        receita_total=formatar_reais(somar(TIPO_RECEITA)),
        despesa_total=formatar_reais(somar(TIPO_DESPESA)),
        comprometimento_anual=formatar_reais(comprometimento_anual),
        percentual_comprometimento_anual=percentual_comprometimento_anual,
        parcelas_futuras=formatar_reais(total_parcelas_futuras),
        quantidade_parcelas_futuras=quantidade_parcelas_futuras,
        proxima_parcela_valor=proxima_parcela_valor,
        proxima_parcela_data=proxima_parcela_data
    )


# as rotas abaixo só entregam imagens da pasta static/uploads usadas no layout
@app.route("/logo_dashboard")
def logo_dashboard():
    caminho = os.path.join(app.root_path, "static", "uploads")
    return send_from_directory(caminho, "logo_dashboard.png")


@app.route("/dinheiro")
def dinheiro():
    caminho = os.path.join(app.root_path, "static", "uploads")
    return send_from_directory(caminho, "dinheiro.png")


@app.route("/check")
def check():
    caminho = os.path.join(app.root_path, "static", "uploads")
    return send_from_directory(caminho, "check.png")


@app.route("/quadrado")
def quadrado():
    caminho = os.path.join(app.root_path, "static", "uploads")
    return send_from_directory(caminho, "quadrado.png")


@app.route("/calculadora")
def calculadora():
    caminho = os.path.join(app.root_path, "static", "uploads")
    return send_from_directory(caminho, "calculadora.png")


@app.route("/escudo")
def escudo():
    caminho = os.path.join(app.root_path, "static", "uploads")
    return send_from_directory(caminho, "escudo.png")


@app.route("/predio")
def predio():
    caminho = os.path.join(app.root_path, "static", "uploads")
    return send_from_directory(caminho, "predio.png")


# ============================================================
# EMPRÉSTIMOS
# ============================================================

def converter_valor(valor):
    # converte texto de dinheiro em float: "R$ 1.234,56" -> 1234.56
    # Limpa o texto: tira espaços das pontas e remove "R$" e espaços internos, sobrando só números e separadores.
    valor = valor.strip().replace("R$", "").replace(" ", "")

    if "," in valor:
        # formato brasileiro: tira o ponto de milhar e troca a vírgula por ponto
        valor = valor.replace(".", "").replace(",", ".")

    return float(valor)


def gerar_parcelas(emprestimo):
    # cria a lista de parcelas mensais (número, vencimento, valor, status) a partir dos dados do empréstimo
    parcelas = []
    # strptime faz o inverso do strftime: converte TEXTO ("13/11/2026") em objeto de data,
    # seguindo o formato indicado (%d/%m/%Y).
    data = datetime.strptime(emprestimo["data"], "%d/%m/%Y")  # texto -> data

    quantidade = emprestimo["quantidade_parcelas"]
    valor_parcela = emprestimo["valor_parcela"]

    for numero in range(1, quantidade + 1):
        # Soma "numero" meses ao mês da contratação. Como pode passar de 12, as duas linhas seguintes
        # usam divisão inteira (//) para descobrir quantos anos avançar e resto (%) para o mês de 1 a 12.
        # O "- 1" / "+ 1" existe porque os meses começam em 1, mas o resto da divisão começa em 0.
        mes_total = data.month + numero                 # primeira parcela vence 1 mês após a contratação
        ano = data.year + (mes_total - 1) // 12         # avança o ano quando passa de dezembro
        mes = (mes_total - 1) % 12 + 1

        dia = min(data.day, calendar.monthrange(ano, mes)[1])  # ajusta dia 31 para meses menores
        vencimento = datetime(ano, mes, dia)

        parcelas.append({
            "numero": numero,
            "vencimento": vencimento.strftime("%d/%m/%Y"),
            "valor": valor_parcela,
            "valor_formatado": "R$ " + formatar_reais(valor_parcela),
            # Parcelas com número até "parcelas_pagas" nascem como Pago; as demais como Pendente.
            # Em novos empréstimos parcelas_pagas é 0, então todas começam Pendentes.
            "status": (
                "Pago"
                if numero <= emprestimo.get("parcelas_pagas", 0)
                else "Pendente"
            )
        })

    return parcelas


def atualizar_parcelas_pendentes(cursor, id_emprestimo, id_usuario, taxa_valor):
    # recalcula as parcelas ainda não pagas usando a taxa do ano atual (juros variáveis)
    # recebe o cursor de fora para participar da mesma transação de quem chamou

    # busca valor emprestado e taxa original do empréstimo
    cursor.execute("""
        SELECT s.VALOR_EMPRESTIMO, t.TAXA_MENSAL
        FROM EMPRESTIMO e
        JOIN SIMULACAO s ON e.ID_SIMULACAO = s.ID_SIMULACAO
        JOIN TAXA_JUROS t ON s.ID_TAXA_JUROS = t.ID_TAXA_JUROS
        WHERE e.ID_EMPRESTIMO = ?
    """, (id_emprestimo,))
    linha = cursor.fetchone()
    if not linha:
        return

    # Se a taxa do empréstimo estiver vazia, usa a taxa atual para não dar erro nas contas.
    taxa_original = float(linha[1] or taxa_valor)
    saldo = float(linha[0] or 0)  # saldo devedor começa com o valor total emprestado
    cursor.execute("""
        SELECT NUM_PARCELAS, VALOR, STATUS, TAXA_APLICADA
        FROM PARCELA WHERE ID_EMPRESTIMO = ? ORDER BY NUM_PARCELAS
    """, (id_emprestimo,))
    parcelas = cursor.fetchall()

    # reduz o saldo devedor com cada parcela já paga: amortização = parcela - juros do período
    for parcela in parcelas:
        if parcela[2] == "Pago":
            taxa_antiga = float(parcela[3]) if parcela[3] is not None else taxa_original
            juros = saldo * (taxa_antiga / 100)
            # max(0, ...) impede que o saldo fique negativo por diferença de arredondamento.
            saldo = max(0, saldo - (float(parcela[1]) - juros))

    # Filtra só as parcelas que ainda não foram pagas (coluna 2 = STATUS).
    pendentes = [p for p in parcelas if p[2] != "Pago"]
    quantidade = len(pendentes)
    mensal = taxa_valor / 100
    if quantidade == 0:
        return  # nada a recalcular
    # fórmula da Tabela Price: PMT = saldo * i / (1 - (1+i)^-n)
    # Taxa zero (sem juros): a fórmula da Price daria divisão por zero (0/0), então usa divisão simples.
    # Caso contrário aplica a Tabela Price: parcela = V * i / (1 - (1+i)^-n), onde V = valor emprestado,
    # i = taxa mensal em decimal e n = número de parcelas. O "** (-n)" é potência negativa, igual a 1/(1+i)^n.
    if mensal == 0:
        valor_novo = round(saldo / quantidade, 2)
    else:
        valor_novo = round(saldo * mensal / (1 - (1 + mensal) ** (-quantidade)), 2)

    # grava o novo valor e a taxa em cada parcela pendente e na movimentação ligada a ela
    for parcela in pendentes:
        cursor.execute("""
            UPDATE PARCELA SET VALOR = ?, TAXA_APLICADA = ?
            WHERE ID_EMPRESTIMO = ? AND NUM_PARCELAS = ?
        """, (valor_novo, taxa_valor, id_emprestimo, parcela[0]))
        cursor.execute("""
            UPDATE MOV_FINANCEIRA SET VALOR = ?
            WHERE ID_USUARIO = ? AND DESCRICAO = ?
        """, (valor_novo, id_usuario,
              "Parcela de empréstimo " + str(id_emprestimo) + "-" + str(parcela[0])))


@app.route("/emprestimos")
def historico_emprestimos():
    # lista os empréstimos do usuário filtrando por período
    if "usuario_id" not in session:
        flash("Faça login para acessar esta página.", "erro")
        return redirect(url_for("login"))

    periodo = request.args.get("periodo", "ultimos")
    if periodo not in PERIODOS:
        periodo = "ultimos"

    # mesma lógica de datas_do_periodo, escrita aqui diretamente
    hoje = date.today()
    if periodo == "ultimos":
        data_inicio = hoje - timedelta(days=90)
        data_fim = hoje
    elif periodo == "proximos":
        data_inicio = hoje
        data_fim = hoje + timedelta(days=90)
    else:
        data_inicio = date(2000, 1, 1)
        data_fim = date(2100, 12, 31)

    conexao = conectar_banco()
    cursor = conexao.cursor()
    # JOIN liga tabelas: EMPRESTIMO (e) -> SIMULACAO (s) pelo ID_SIMULACAO, porque o dono do empréstimo (ID_USUARIO)
    # e o valor/risco ficam na simulação. BETWEEN ? AND ? filtra datas dentro do intervalo (inclusive as pontas).
    # "e" e "s" são apelidos (alias) das tabelas, para escrever menos.
    dados = []
    try:
        cursor.execute("""
            SELECT e.ID_EMPRESTIMO, e.DATA, s.VALOR_EMPRESTIMO,
                   s.NUM_PARCELAS, s.RISCO, e.STATUS
            FROM EMPRESTIMO e
            JOIN SIMULACAO s ON e.ID_SIMULACAO = s.ID_SIMULACAO
            WHERE s.ID_USUARIO = ? AND e.DATA BETWEEN ? AND ?
            ORDER BY e.DATA DESC, e.ID_EMPRESTIMO DESC
        """, (session["usuario_id"], data_inicio, data_fim))
        for linha in cursor.fetchall():
            # Se for data de verdade formata dd/mm/aaaa; se vier como outro tipo, converte para texto com str()
            # para a página nunca quebrar.
            data = linha[1].strftime("%d/%m/%Y") if isinstance(linha[1], (date, datetime)) else str(linha[1])
            dados.append({
                "id": linha[0],
                "data": data,
                "descricao": "Empréstimo",
                "classificacao": "Risco " + str(linha[4] or "Baixo"),
                "categoria": str(linha[3]) + " parcelas",
                "valor_texto": formatar_reais(float(linha[2] or 0)),
                "status": linha[5] or "Em andamento"
            })
    except Exception:
        app.logger.exception("Erro ao buscar histórico de empréstimos.")
        flash("Não foi possível carregar o histórico.", "erro")
    finally:
        cursor.close()
        conexao.close()

    return render_template("historico_emprestimos.html", dados=dados, periodo=periodo)


@app.route("/emprestimos/relatorio")
def relatorio_emprestimos():
    # gera o PDF do histórico de empréstimos (mesma ideia do /relatorio de movimentações)
    if "usuario_id" not in session:
        return redirect(url_for("login"))

    periodo = request.args.get("periodo", "ultimos")
    if periodo not in PERIODOS:
        periodo = "ultimos"
    hoje = date.today()
    if periodo == "ultimos":
        inicio, fim = hoje - timedelta(days=90), hoje
    elif periodo == "proximos":
        inicio, fim = hoje, hoje + timedelta(days=90)
    else:
        inicio, fim = date(2000, 1, 1), date(2100, 12, 31)

    conexao = conectar_banco()
    cursor = conexao.cursor()
    cursor.execute("""
        SELECT e.ID_EMPRESTIMO, e.DATA, s.VALOR_EMPRESTIMO,
               s.NUM_PARCELAS, s.RISCO, e.STATUS
        FROM EMPRESTIMO e JOIN SIMULACAO s ON e.ID_SIMULACAO = s.ID_SIMULACAO
        WHERE s.ID_USUARIO = ? AND e.DATA BETWEEN ? AND ?
        ORDER BY e.DATA DESC
    """, (session["usuario_id"], inicio, fim))
    linhas = cursor.fetchall()
    cursor.close()
    conexao.close()

    # cabeçalho do PDF
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    pdf.set_font("Arial", "B", 16)
    pdf.cell(190, 12, texto_pdf("Histórico de Empréstimos - CredMais"), ln=True, align="C")
    pdf.set_font("Arial", size=10)
    pdf.cell(190, 8, texto_pdf("Período: " + PERIODOS[periodo]), ln=True, align="C")
    pdf.ln(5)
    # títulos das colunas
    pdf.set_font("Arial", "B", 10)
    pdf.cell(35, 10, "Data", border=1)
    pdf.cell(65, 10, texto_pdf("Valor"), border=1)
    pdf.cell(35, 10, "Parcelas", border=1)
    pdf.cell(55, 10, "Risco / Status", border=1, ln=True)
    pdf.set_font("Arial", size=9)
    # uma linha por empréstimo
    for item in linhas:
        data = item[1].strftime("%d/%m/%Y") if isinstance(item[1], (date, datetime)) else str(item[1])
        pdf.cell(35, 10, data, border=1)
        pdf.cell(65, 10, texto_pdf("R$ " + formatar_reais(float(item[2] or 0))), border=1)
        pdf.cell(35, 10, str(item[3]) + "x", border=1)
        pdf.cell(55, 10, texto_pdf(str(item[4]) + " / " + str(item[5])), border=1, ln=True)
    caminho = os.path.join(app.root_path, "relatorio_emprestimos.pdf")
    pdf.output(caminho)
    return send_file(caminho, as_attachment=True, mimetype="application/pdf")


@app.route("/emprestimos/<int:id_emprestimo>")
def visualizar_emprestimo(id_emprestimo):
    # detalhes de um empréstimo salvo no banco, com a lista de parcelas
    if "usuario_id" not in session:
        return redirect(url_for("login"))

    conexao = conectar_banco()
    cursor = conexao.cursor()
    try:
        # confirma que o empréstimo pertence ao usuário logado
        cursor.execute("""
            SELECT e.ID_EMPRESTIMO, e.DATA, e.STATUS, s.VALOR_EMPRESTIMO,
                   s.NUM_PARCELAS, s.VALOR_PARCELA, s.VALOR_TOTAL, s.RISCO
            FROM EMPRESTIMO e JOIN SIMULACAO s ON e.ID_SIMULACAO = s.ID_SIMULACAO
            WHERE e.ID_EMPRESTIMO = ? AND s.ID_USUARIO = ?
        """, (id_emprestimo, session["usuario_id"]))
        linha = cursor.fetchone()
        if not linha:
            flash("Empréstimo não encontrado.", "erro")
            return redirect(url_for("historico_emprestimos"))
        # ao abrir, reajusta as parcelas pendentes para a taxa vigente do ano atual
        taxa_atual = buscar_taxa_por_ano(date.today().year)
        if taxa_atual:
            atualizar_parcelas_pendentes(cursor, id_emprestimo, session["usuario_id"], taxa_atual["juros"])
            conexao.commit()
        # lê as parcelas já atualizadas
        cursor.execute("""
            SELECT ID_PARCELA, NUM_PARCELAS, VALOR, DATA_VENCIMENTO, STATUS, TAXA_APLICADA
            FROM PARCELA WHERE ID_EMPRESTIMO = ? ORDER BY NUM_PARCELAS
        """, (id_emprestimo,))
        parcelas = cursor.fetchall()
        lista = []
        for p in parcelas:
            venc = p[3].strftime("%d/%m/%Y") if isinstance(p[3], (date, datetime)) else str(p[3])
            lista.append({
                "id": p[0], "numero": p[1], "valor": float(p[2] or 0),
                "vencimento": venc, "status": p[4] or "Pendente",
                "taxa": float(p[5]) if p[5] is not None else None,
                "valor_formatado": "R$ " + formatar_reais(float(p[2] or 0))
            })
        # Se for data de verdade formata dd/mm/aaaa; se vier como outro tipo, converte para texto com str()
        # para a página nunca quebrar.
        data = linha[1].strftime("%d/%m/%Y") if isinstance(linha[1], (date, datetime)) else str(linha[1])
        # dicionário final com os mesmos nomes de chave usados em detalhes_emprestimos.html
        emprestimo = {
            "id": linha[0], "data": data, "status": linha[2],
            "valor": float(linha[3] or 0), "quantidade_parcelas": int(linha[4] or 0),
            "valor_parcela": float(linha[5] or 0), "total": float(linha[6] or 0),
            "risco": linha[7], "parcelas": int(linha[4] or 0), "lista_parcelas": lista,
            "valor_formatado": "R$ " + formatar_reais(float(linha[3] or 0)),
            "total_formatado": "R$ " + formatar_reais(float(linha[6] or 0)),
            "parcela_formatada": "R$ " + formatar_reais(float(linha[5] or 0))
        }
        taxa_atual = buscar_taxa_por_ano(date.today().year)
        return render_template("detalhes_emprestimos.html", emprestimo=emprestimo,
                               taxa_atual=taxa_atual["juros"] if taxa_atual else 0)
    finally:
        cursor.close()
        conexao.close()


@app.route("/emprestimos/<int:id_emprestimo>/excluir", methods=["POST"])
def excluir_emprestimo(id_emprestimo):
    # exclui um empréstimo do usuário (parcelas primeiro, depois o empréstimo)
    if "usuario_id" not in session:
        return redirect(url_for("login"))

    conexao = conectar_banco()
    cursor = conexao.cursor()
    try:
        # verifica se é do usuário logado
        cursor.execute("""
            SELECT e.ID_EMPRESTIMO
            FROM EMPRESTIMO e JOIN SIMULACAO s ON e.ID_SIMULACAO = s.ID_SIMULACAO
            WHERE e.ID_EMPRESTIMO = ? AND s.ID_USUARIO = ?
        """, (id_emprestimo, session["usuario_id"]))
        if not cursor.fetchone():
            flash("Empréstimo não encontrado.", "erro")
            return redirect(url_for("historico_emprestimos"))
        cursor.execute("DELETE FROM PARCELA WHERE ID_EMPRESTIMO = ?", (id_emprestimo,))
        cursor.execute("DELETE FROM EMPRESTIMO WHERE ID_EMPRESTIMO = ?", (id_emprestimo,))
        conexao.commit()
        flash("Empréstimo excluído com sucesso.", "sucesso")
    except Exception:
        conexao.rollback()
        app.logger.exception("Erro ao excluir empréstimo.")
        flash("Não foi possível excluir o empréstimo.", "erro")
    finally:
        cursor.close()
        conexao.close()
    return redirect(url_for("historico_emprestimos"))


@app.route("/parcela/<int:id_parcela>/pagar", methods=["POST"])
def pagar_parcela(id_parcela):
    # paga uma parcela: registra a despesa, marca como paga, recalcula as pendentes e conclui o empréstimo se acabaram
    if "usuario_id" not in session:
        return redirect(url_for("login"))

    conexao = conectar_banco()
    cursor = conexao.cursor()
    try:
        # busca a parcela e o dono (via EMPRESTIMO -> SIMULACAO)
        cursor.execute("""
            SELECT p.ID_EMPRESTIMO, p.NUM_PARCELAS, p.VALOR, p.STATUS,
                   s.ID_USUARIO
            FROM PARCELA p
            JOIN EMPRESTIMO e ON p.ID_EMPRESTIMO = e.ID_EMPRESTIMO
            JOIN SIMULACAO s ON e.ID_SIMULACAO = s.ID_SIMULACAO
            WHERE p.ID_PARCELA = ?
        """, (id_parcela,))
        parcela = cursor.fetchone()
        # não existe ou pertence a outro usuário
        if not parcela or parcela[4] != session["usuario_id"]:
            flash("Parcela não encontrada.", "erro")
            return redirect(url_for("historico_emprestimos"))
        if parcela[3] == "Pago":
            flash("Esta parcela já foi paga.", "erro")
            return redirect(url_for("visualizar_emprestimo", id_emprestimo=parcela[0]))

        taxa_atual = buscar_taxa_por_ano(date.today().year)
        taxa_valor = taxa_atual["juros"] if taxa_atual else 0

        # Registra a despesa somente quando a parcela é paga.
        descricao_antiga = "Parcela de empréstimo " + str(parcela[0]) + "-" + str(parcela[1])  # nome "oculto" (filtrado das listas)
        descricao_paga = "Parcela paga " + str(parcela[0]) + "-" + str(parcela[1])             # nome novo, passa a aparecer
        cursor.execute("""
            SELECT ID_MOV_FINANCEIRA
            FROM MOV_FINANCEIRA
            WHERE ID_USUARIO = ? AND DESCRICAO = ?
        """, (session["usuario_id"], descricao_antiga))
        despesa_antiga = cursor.fetchone()
        if despesa_antiga:
            # já existia a movimentação da parcela: só renomeia e coloca a data de hoje
            cursor.execute("""
                UPDATE MOV_FINANCEIRA
                SET DATA_LANCAMENTO = ?, DESCRICAO = ?
                WHERE ID_MOV_FINANCEIRA = ?
            """, (date.today(), descricao_paga, despesa_antiga[0]))
        else:
            # não existia: cria uma despesa nova
            cursor.execute("""
                INSERT INTO MOV_FINANCEIRA
                    (TIPO, VALOR, DATA_LANCAMENTO, DESCRICAO, ID_USUARIO, CLASSIFICACAO)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (TIPO_DESPESA, parcela[2], date.today(), descricao_paga,
                  session["usuario_id"], 1))

        # marca a parcela como paga guardando a taxa vigente no momento
        cursor.execute("""
            UPDATE PARCELA SET STATUS = 'Pago', TAXA_APLICADA = ?
            WHERE ID_PARCELA = ?
        """, (taxa_valor, id_parcela))

        # Atualiza os valores e a taxa somente das parcelas que ainda faltam.
        atualizar_parcelas_pendentes(cursor, parcela[0], session["usuario_id"], taxa_valor)

        # NOT EXISTS (SELECT 1 ...) é verdadeiro quando NÃO há nenhuma parcela com status diferente de 'Pago'.
        # O "SELECT 1" só testa existência (não importa qual coluna). Ou seja: todas pagas -> empréstimo Concluído.
        # se não sobrou nenhuma parcela não paga, o empréstimo vira "Concluído"
        cursor.execute("""
            UPDATE EMPRESTIMO SET STATUS = 'Concluído'
            WHERE ID_EMPRESTIMO = ?
              AND NOT EXISTS (SELECT 1 FROM PARCELA WHERE ID_EMPRESTIMO = ? AND STATUS <> 'Pago')
        """, (parcela[0], parcela[0]))
        conexao.commit()
        # dados para a tela de confirmação
        session["parcela_paga"] = {
            "numero": parcela[1], "valor": formatar_reais(float(parcela[2])),
            "data": date.today().strftime("%d/%m/%Y"), "taxa": taxa_valor
        }
        return redirect(url_for("parcela_paga"))
    except Exception:
        conexao.rollback()
        app.logger.exception("Erro ao pagar parcela.")
        flash("Não foi possível pagar a parcela.", "erro")
        return redirect(url_for("historico_emprestimos"))
    finally:
        cursor.close()
        conexao.close()


@app.route("/parcela-paga")
def parcela_paga():
    # tela de confirmação de pagamento (aparece uma única vez, pois usa session.pop)
    if "usuario_id" not in session:
        return redirect(url_for("login"))
    parcela = session.pop("parcela_paga", None)
    if not parcela:
        return redirect(url_for("historico_emprestimos"))
    # reaproveita o template de "movimentação registrada"
    return render_template("movimentacao_registrada.html", dados={
        "descricao": "Parcela paga - número " + str(parcela["numero"]),
        "valor_texto": parcela["valor"], "data": parcela["data"],
        "categoria": "Despesa", "classe": "despesa",
        "taxa": parcela["taxa"]
    })


@app.route("/emprestimos/detalhes")
def detalhes_emprestimos():
    # mostra o empréstimo recém-contratado guardado na sessão (antes de abrir pelo histórico)
    if "usuario_id" not in session:
        flash("Faça login para acessar esta página.", "erro")
        return redirect(url_for("login"))

    emprestimo = session.get("emprestimo")

    if emprestimo:
        emprestimo = dict(emprestimo)  # cópia, para não alterar a sessão
        emprestimo["lista_parcelas"] = gerar_parcelas(emprestimo)
        emprestimo["parcelas"] = emprestimo["quantidade_parcelas"]
        emprestimo["valor_formatado"] = "R$ " + formatar_reais(emprestimo["valor"])
        emprestimo["total_formatado"] = "R$ " + formatar_reais(emprestimo["total"])
        emprestimo["parcela_formatada"] = "R$ " + formatar_reais(emprestimo["valor_parcela"])

    return render_template(
        "detalhes_emprestimos.html",
        emprestimo=emprestimo
    )


@app.route("/emprestimo/realizado", methods=["POST"])
def emprestimo_realizado():
    # confirma a contratação: recalcula tudo no servidor e grava SIMULACAO, EMPRESTIMO, PARCELAs e a receita do valor recebido
    if "usuario_id" not in session:
        flash("Faça login para acessar esta página.", "erro")
        return redirect(url_for("login"))

    cliente = request.form.get("cliente", "").strip()
    valor_texto = request.form.get("valor", "").strip()
    parcelas_texto = request.form.get("parcelas", "12").strip()
    data = request.form.get("data", "").strip()
    id_taxa_texto = request.form.get("id_taxa_juros", "").strip()

    # validação dos dados vindos do formulário
    try:
        valor = converter_valor(valor_texto)
        quantidade = int(parcelas_texto)

        if not cliente or valor <= 0 or quantidade < 1:
            raise ValueError

        if quantidade > 60:  # máximo de 60 parcelas
            raise ValueError

        # O input type="date" do HTML envia o formato AAAA-MM-DD, por isso o strptime usa "%Y-%m-%d".
        # Se o campo vier vazio, usa a data de hoje.
        if data:
            data_objeto = datetime.strptime(data, "%Y-%m-%d")  # formato do input type="date"
            data_str = data_objeto.strftime("%d/%m/%Y")
            data_sql = data_objeto.date()
        else:
            data_objeto = datetime.today()  # sem data: usa hoje
            data_str = data_objeto.strftime("%d/%m/%Y")
            data_sql = data_objeto.date()

        id_taxa_juros = int(id_taxa_texto)
        if id_taxa_juros <= 0:
            raise ValueError

    # ValueError: texto que não vira número/data | TypeError: valor None ou tipo errado
    # OverflowError: número grande demais para a conta. Qualquer um dos três cai aqui.
    except (ValueError, TypeError, OverflowError):
        return "Dados inválidos. Confira os valores, a data e as parcelas.", 400

    id_usuario = session["usuario_id"]
    conexao = conectar_banco()
    cursor = conexao.cursor()

    try:
        # Usa a taxa cadastrada pelo administrador para o ano atual.
        # (ignora o id enviado pelo formulário, por segurança)
        cursor.execute("""
            SELECT FIRST 1 ID_TAXA_JUROS, TAXA_MENSAL
            FROM TAXA_JUROS
            WHERE EXTRACT(YEAR FROM DATA_REFERENCIA) = ?
            ORDER BY DATA_REFERENCIA DESC, ID_TAXA_JUROS DESC
        """, (date.today().year,))
        taxa_row = cursor.fetchone()
        if taxa_row is None:
            raise ValueError("Não existe taxa cadastrada para o ano atual.")

        id_taxa_juros = taxa_row[0]
        mensal = float(taxa_row[1]) / 100  # taxa em decimal (2% -> 0.02)
        # Proteção da taxa antes de usar na fórmula:
        #  - "mensal < 0": juros negativo não faz sentido.
        #  - "math.isfinite(mensal)": False quando o número é NaN (não é número) ou infinito (inf).
        #    Esses valores quebrariam a fórmula e gerariam resultado sem sentido, então "not isfinite" barra.
        # Se qualquer condição for verdadeira, a taxa é considerada inválida e o cálculo não acontece.
        if mensal < 0 or not math.isfinite(mensal):
            raise ValueError("Taxa inválida.")
        # parcela pela Tabela Price (sem juros: divisão simples)
        # Taxa zero (sem juros): a fórmula da Price daria divisão por zero (0/0), então usa divisão simples.
        # Caso contrário aplica a Tabela Price: parcela = V * i / (1 - (1+i)^-n), onde V = valor emprestado,
        # i = taxa mensal em decimal e n = número de parcelas. O "** (-n)" é potência negativa, igual a 1/(1+i)^n.
        if mensal == 0:
            valor_parcela = round(valor / quantidade, 2)
        else:
            valor_parcela = round(valor * mensal / (1 - (1 + mensal) ** (-quantidade)), 2)

        # renda líquida do mês = receitas - despesas
        renda = somar_mes(TIPO_RECEITA)
        despesas = somar_mes(TIPO_DESPESA)
        renda_liquida = renda - despesas
        # Sem renda líquida positiva não há como calcular o comprometimento (evita divisão por zero/negativo).
        if renda_liquida <= 0:
            raise ValueError("A renda líquida precisa ser positiva.")

        # % da renda comprometida pela parcela define o risco: até 20% Baixo, até 35% Médio, acima Alto
        comprometimento = (valor_parcela / renda_liquida) * 100
        # Classificação de risco pela parcela: até 20% da renda líquida = Baixo, até 35% = Médio, acima = Alto.
        # Exemplo: parcela 300 e renda líquida 2000 -> 15% -> Baixo.
        if comprometimento <= 20:
            risco = "Baixo"
        elif comprometimento <= 35:
            risco = "Médio"
        else:
            risco = "Alto"
        if risco == "Alto":
            raise ValueError("Empréstimos de alto risco não podem ser realizados.")

        valor_total = round(valor_parcela * quantidade, 2)

        # 1. Salvar na tabela SIMULACAO
        cursor.execute(
            """
            INSERT INTO SIMULACAO (
                ID_USUARIO, ID_TAXA_JUROS, VALOR_EMPRESTIMO, NUM_PARCELAS, 
                VALOR_PARCELA, VALOR_TOTAL, PERCENTUAL_COMPROMETIDO, RISCO, DATA_SIMULACAO
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (id_usuario, id_taxa_juros, valor, quantidade, valor_parcela, valor_total, comprometimento, risco, data_sql)
        )

        # Buscar o ID da simulação gravada
        # Como o INSERT não devolve o ID gerado, pegamos o MAIOR ID do usuário (o último inserido).
        # Funciona porque o ID cresce a cada inserção; o MAX(ID_EMPRESTIMO) mais abaixo não filtra por usuário,
        # então teoricamente poderia pegar o de outra pessoa se dois empréstimos fossem criados ao mesmo tempo.
        cursor.execute("SELECT MAX(ID_SIMULACAO) FROM SIMULACAO WHERE ID_USUARIO = ?", (id_usuario,))
        id_simulacao = cursor.fetchone()[0]

        # 2. Salvar na tabela EMPRESTIMO
        cursor.execute(
            """
            INSERT INTO EMPRESTIMO (ID_SIMULACAO, DATA, STATUS)
            VALUES (?, ?, ?)
            """,
            (id_simulacao, data_sql, 'Em andamento')
        )

        # Buscar o ID do empréstimo gravado
        cursor.execute("SELECT MAX(ID_EMPRESTIMO) FROM EMPRESTIMO")
        id_emprestimo = cursor.fetchone()[0]

        # 3. Gerar e salvar as parcelas na tabela PARCELA
        temp_emprestimo = {
            "data": data_str,
            "quantidade_parcelas": quantidade,
            "valor_parcela": valor_parcela,
            "parcelas_pagas": 0
        }
        lista_parcelas = gerar_parcelas(temp_emprestimo)

        for p in lista_parcelas:
            data_venc = datetime.strptime(p["vencimento"], "%d/%m/%Y").date()
            cursor.execute(
                """
                INSERT INTO PARCELA
                    (ID_EMPRESTIMO, NUM_PARCELAS, VALOR, DATA_VENCIMENTO, STATUS, TAXA_APLICADA)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (id_emprestimo, p["numero"], p["valor"], data_venc, p["status"], float(taxa_row[1]))
            )

        # Registrar o valor recebido e as parcelas nas movimentações financeiras
        # (o dinheiro do empréstimo entra como receita variável)
        cursor.execute(
            """
            INSERT INTO MOV_FINANCEIRA
            (TIPO, VALOR, DATA_LANCAMENTO, DESCRICAO, ID_USUARIO, CLASSIFICACAO)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (TIPO_RECEITA, valor, data_sql, "Empréstimo recebido", id_usuario, 2)
        )

        conexao.commit()  # só confirma se todas as etapas deram certo

    except ValueError as erro_validacao:
        conexao.rollback()
        return str(erro_validacao), 400
    except Exception:
        conexao.rollback()
        app.logger.exception("Erro ao salvar empréstimo no banco.")
        return "Erro ao salvar empréstimo no banco de dados.", 500
    finally:
        cursor.close()
        conexao.close()

    # guarda um resumo na sessão para a tela de detalhes
    session["emprestimo"] = {
        "cliente": cliente,
        "valor": round(valor, 2),
        "data": data_str,
        "quantidade_parcelas": quantidade,
        "valor_parcela": round(valor_parcela, 2),
        "total": valor_total,
        "status": "Em andamento",
        "parcelas_pagas": 0
    }

    # O Flask só salva a sessão quando detecta mudança. Marcar modified = True garante que o dicionário
    # "emprestimo" (aninhado) seja gravado no cookie.
    session.modified = True  # força o Flask a salvar a sessão alterada

    return redirect(url_for("detalhes_emprestimos"))


@app.route("/emprestimo/limpar", methods=["POST"])
def limpar_emprestimo():
    # remove da sessão o empréstimo exibido e volta para a tela de detalhes
    session.pop("emprestimo", None)
    return redirect(url_for("detalhes_emprestimos"))


# ============================================================
# SIMULAÇÃO DE EMPRÉSTIMO
# ============================================================

@app.route("/simulacao", methods=["GET", "POST"])
def simulacao():
    # simula um empréstimo (não grava nada): calcula parcela, total e risco conforme a renda do mês
    if "usuario_id" not in session:
        flash("Faça login para simular um empréstimo.", "erro")
        return redirect(url_for("login"))

    # Padrão usado nesta rota: as variáveis começam como None e vão sendo preenchidas.
    # Cada bloco abaixo só executa se "erro is None", ou seja, se nada deu errado até aqui (efeito cascata).
    erro = None       # mensagem de erro a exibir
    resultado = None  # dicionário com o resultado da simulação
    taxa = None

    try:
        renda = somar_mes(TIPO_RECEITA)
        despesas = somar_mes(TIPO_DESPESA)
    except Exception:
        app.logger.exception("Erro ao consultar as movimentações financeiras.")
        renda = 0
        despesas = 0
        erro = "Não foi possível consultar suas receitas e despesas cadastradas."

    renda_liquida = renda - despesas

    # valida os dados enviados
    # Só processa quando o formulário foi enviado (POST) e nenhum erro anterior foi registrado.
    if request.method == "POST" and erro is None:
        try:
            valor_texto = request.form.get("valor", "").strip()
            parcelas_texto = request.form.get("parcelas", "").strip()

            valor = converter_valor(valor_texto)
            quantidade = int(parcelas_texto)

            if (not math.isfinite(valor) or valor <= 0 or
                    quantidade < 1 or quantidade > 60):
                raise ValueError

            if renda <= 0:
                erro = "Cadastre suas receitas deste mês em Movimentações antes de simular."
            elif renda_liquida <= 0:
                erro = "Suas despesas cadastradas são iguais ou maiores que suas receitas deste mês."

        # ValueError: texto que não vira número/data | TypeError: valor None ou tipo errado
        # OverflowError: número grande demais para a conta. Qualquer um dos três cai aqui.
        except (ValueError, TypeError, OverflowError):
            erro = "Informe um valor de empréstimo e uma quantidade de parcelas válidos."

    # busca a taxa do ano atual (também no GET, para mostrar na tela)
    if erro is None:
        try:
            taxa = buscar_taxa_por_ano(date.today().year)
        except Exception:
            app.logger.exception("Erro ao consultar as taxas.")
            erro = "Não foi possível consultar as taxas no banco de dados."

    # calcula o resultado
    # Só processa quando o formulário foi enviado (POST) e nenhum erro anterior foi registrado.
    if request.method == "POST" and erro is None:
        if taxa is None:
            erro = "Nenhuma taxa foi cadastrada no banco de dados."
        else:
            juros = taxa["juros"]
            mensal = juros / 100
            # Proteção da taxa antes de usar na fórmula:
            #  - "mensal < 0": juros negativo não faz sentido.
            #  - "math.isfinite(mensal)": False quando o número é NaN (não é número) ou infinito (inf).
            #    Esses valores quebrariam a fórmula e gerariam resultado sem sentido, então "not isfinite" barra.
            # Se qualquer condição for verdadeira, a taxa é considerada inválida e o cálculo não acontece.
            if mensal < 0 or not math.isfinite(mensal):
                erro = "A taxa cadastrada é inválida."
            else:
                # Taxa zero (sem juros): a fórmula da Price daria divisão por zero (0/0), então usa divisão simples.
                # Caso contrário aplica a Tabela Price: parcela = V * i / (1 - (1+i)^-n), onde V = valor emprestado,
                # i = taxa mensal em decimal e n = número de parcelas. O "** (-n)" é potência negativa, igual a 1/(1+i)^n.
                if mensal == 0:
                    parcela = valor / quantidade
                else:
                    parcela = valor * mensal / (1 - (1 + mensal) ** (-quantidade))  # Tabela

                total = parcela * quantidade
                comprometimento = (parcela / renda_liquida) * 100  # % da renda líquida usada pela parcela

                # Classificação de risco pela parcela: até 20% da renda líquida = Baixo, até 35% = Médio, acima = Alto.
                # Exemplo: parcela 300 e renda líquida 2000 -> 15% -> Baixo.
                if comprometimento <= 20:
                    risco = "Baixo"
                elif comprometimento <= 35:
                    risco = "Médio"
                else:
                    risco = "Alto"

                # Expressão que já devolve True/False: compara risco com "Alto" e guarda o resultado na variável.
                alto_risco = risco == "Alto"
                resultado = {
                    "valor": formatar_reais(valor),
                    "valor_original": round(valor, 2),
                    "parcelas": quantidade,
                    # Mostra a taxa com 2 casas e vírgula decimal (2.5 -> "2,50") para o padrão brasileiro.
                    "juros": format(float(juros), ".2f").replace(".", ","),
                    "valor_parcela": formatar_reais(parcela),
                    "valor_parcela_original": round(parcela, 2),
                    "total": formatar_reais(total),
                    "comprometimento": formatar_reais(comprometimento),
                    "alto_risco": alto_risco,
                    "risco": risco
                }

                if alto_risco:
                    resultado[
                        "mensagem_risco"] = "A parcela compromete mais de 35% da sua renda mensal líquida. Não é possível realizar este empréstimo."

    # se calculou, mostra a tela de resultado
    if resultado is not None:
        return render_template("resultado_simulacao.html", resultado=resultado, taxa=taxa, erro=None)

    # senão, mostra o formulário (com erro, se houver) e o resumo da renda do mês
    return render_template(
        "simulacao.html",
        resultado=None,
        taxa=taxa,
        erro=erro,
        renda_mes=formatar_reais(renda),
        despesas_mes=formatar_reais(despesas),
        renda_liquida_mes=formatar_reais(renda_liquida)
    )


# ============================================================
# ADMINISTRAÇÃO DE USUÁRIOS
# ============================================================

@app.route("/admin/usuarios")
def gerenciar_usuarios():
    # lista todos os usuários com contadores (total, ativos, bloqueados) - só administrador
    # Proteção de acesso: se o tipo do usuário logado não for o de administrador, a rota é bloqueada.
    # Sem sessão, .get devolve 0 (usuário comum), então visitantes também são barrados.
    if int(session.get("usuario_tipo", 0)) != TIPO_ADMIN:
        flash("Acesso permitido apenas para administradores.", "erro")
        return redirect(url_for("dashboard"))
    conexao = conectar_banco()
    cursor = conexao.cursor()
    try:
        cursor.execute("""
            SELECT ID_USUARIO, NOME, EMAIL, TIPO, ATIVO, BLOQUEADO
            FROM USUARIO ORDER BY NOME
        """)
        usuarios = cursor.fetchall()
        total_usuarios = len(usuarios)
        # sum(1 for ...) conta quantos itens atendem à condição (soma 1 para cada usuário que passa no filtro).
        # usuario[4] = ATIVO e usuario[5] = BLOQUEADO.
        perfis_ativos = sum(1 for usuario in usuarios if usuario[4] and not usuario[5])  # ativo e não bloqueado
        perfis_bloqueados = sum(1 for usuario in usuarios if usuario[5])
    finally:
        cursor.close()
        conexao.close()
    return render_template(
        "gerenciar_usuarios.html", usuarios=usuarios,
        total_usuarios=total_usuarios, perfis_ativos=perfis_ativos,
        perfis_bloqueados=perfis_bloqueados
    )

@app.route("/admin/usuarios/<int:id_usuario>", methods=["GET", "POST"])
def editar_usuario_admin(id_usuario):
    # o administrador edita nome, e-mail, tipo, senha e foto de qualquer usuário
    # Proteção de acesso: se o tipo do usuário logado não for o de administrador, a rota é bloqueada.
    # Sem sessão, .get devolve 0 (usuário comum), então visitantes também são barrados.
    if int(session.get("usuario_tipo", 0)) != TIPO_ADMIN:
        return redirect(url_for("dashboard"))

    conexao = conectar_banco()
    cursor = conexao.cursor()
    try:
        cursor.execute("SELECT NOME, EMAIL, SENHA, FOTO_PERFIL, TIPO, ATIVO, BLOQUEADO FROM USUARIO WHERE ID_USUARIO = ?", (id_usuario,))
        usuario = cursor.fetchone()
        if not usuario:
            return redirect(url_for("gerenciar_usuarios"))

        if request.method == "POST":
            nome = request.form.get("nome", "").strip()
            email = request.form.get("email", "").strip().lower()
            tipo = request.form.get("tipo", "1")  # "1" comum, "2" admin
            nova_senha = request.form.get("nova_senha", "")
            foto = request.files.get("foto")
            foto_nome = usuario[3]  # mantém a foto atual se nenhuma nova for enviada

            # tipo vem do formulário como TEXTO; só aceitamos "1" (comum) ou "2" (admin) para impedir valores inventados.
            if not any(c.isalpha() for c in nome) or tipo not in ("1", "2"):
                flash("Confira o nome e o tipo do usuário.", "erro")
            else:
                # e-mail não pode pertencer a outro usuário
                cursor.execute("SELECT ID_USUARIO FROM USUARIO WHERE EMAIL = ? AND ID_USUARIO <> ?", (email, id_usuario))
                # fetchone() devolve a PRIMEIRA linha do resultado ou None se a consulta não achou nada.
                # Se achou uma linha (valor "verdadeiro"), o e-mail já existe.
                if cursor.fetchone():
                    flash("Este e-mail já está cadastrado.", "erro")
                else:
                    if foto and foto.filename:
                        extensao = os.path.splitext(foto.filename)[1].lower()
                        if extensao not in (".jpg", ".jpeg", ".png", ".webp"):
                            flash("Escolha uma imagem JPG, JPEG, PNG ou WEBP.", "erro")
                            return render_template("editar_usuario_admin.html", nome=usuario[0], email=usuario[1], foto_perfil=usuario[3] or "", tipo=usuario[4], id_usuario=id_usuario, bloqueado=bool(usuario[6]), ativo=bool(usuario[5]))
                        foto_nome = "perfil_" + str(id_usuario) + "_" + uuid4().hex + extensao  # nome único
                        pasta = os.path.join(app.root_path, "static", "uploads")
                        os.makedirs(pasta, exist_ok=True)
                        foto.save(os.path.join(pasta, foto_nome))

                    if nova_senha:
                        # guarda a senha antiga no histórico e grava o hash da nova
                        senha_hash = generate_password_hash(nova_senha)
                        cursor.execute("""
                            INSERT INTO HISTORICO_SENHA (SENHA, ID_USUARIO, DATA_ALTERACAO)
                            VALUES (?, ?, ?)
                        """, (usuario[2], id_usuario, datetime.now()))
                        cursor.execute("""
                            UPDATE USUARIO SET NOME = ?, EMAIL = ?, TIPO = ?, SENHA = ?, FOTO_PERFIL = ?
                            WHERE ID_USUARIO = ?
                        """, (nome, email, int(tipo), senha_hash, foto_nome, id_usuario))
                    else:
                        cursor.execute("""
                            UPDATE USUARIO SET NOME = ?, EMAIL = ?, TIPO = ?, FOTO_PERFIL = ?
                            WHERE ID_USUARIO = ?
                        """, (nome, email, int(tipo), foto_nome, id_usuario))
                    conexao.commit()
                    # se o admin editou a si mesmo, atualiza a sessão
                    # Compara o usuário editado/excluído com o logado: o admin não pode se excluir (evita ficar sem acesso)
                    # e, ao editar a si mesmo, a sessão precisa ser atualizada para refletir os novos dados.
                    if id_usuario == session.get("usuario_id"):
                        session["usuario_nome"] = nome
                        session["usuario_email"] = email
                        session["usuario_tipo"] = int(tipo)
                    flash("Usuário atualizado.", "sucesso")
                    return redirect(url_for("gerenciar_usuarios"))

        # GET (ou POST com erro): mostra o formulário com os dados atuais
        return render_template("editar_usuario_admin.html",
                               nome=usuario[0], email=usuario[1],
                               foto_perfil=usuario[3] or "",
                               tipo=usuario[4], id_usuario=id_usuario, bloqueado=bool(usuario[6]), ativo=bool(usuario[5]))
    finally:
        cursor.close()
        conexao.close()


@app.route("/admin/usuarios/<int:id_usuario>/excluir", methods=["POST"])
def excluir_usuario_admin(id_usuario):
    # admin: se o usuário estiver bloqueado, DESBLOQUEIA; se não, exclui o usuário e seus dados
    # Proteção de acesso: se o tipo do usuário logado não for o de administrador, a rota é bloqueada.
    # Sem sessão, .get devolve 0 (usuário comum), então visitantes também são barrados.
    if int(session.get("usuario_tipo", 0)) != TIPO_ADMIN:
        return redirect(url_for("dashboard"))
    # Compara o usuário editado/excluído com o logado: o admin não pode se excluir (evita ficar sem acesso)
    # e, ao editar a si mesmo, a sessão precisa ser atualizada para refletir os novos dados.
    if id_usuario == session.get("usuario_id"):
        flash("Não é possível excluir sua própria conta por esta tela.", "erro")
        return redirect(url_for("gerenciar_usuarios"))
    conexao = conectar_banco()
    cursor = conexao.cursor()
    try:
        cursor.execute("SELECT BLOQUEADO FROM USUARIO WHERE ID_USUARIO = ?", (id_usuario,))
        status_usuario = cursor.fetchone()
        if status_usuario and status_usuario[0]:
            cursor.execute("""
                UPDATE USUARIO
                SET BLOQUEADO = ?, TENTATIVAS_LOGIN = ?
                WHERE ID_USUARIO = ?
            """, (False, 0, id_usuario))
            conexao.commit()
            flash("Perfil desbloqueado com sucesso.", "sucesso")
            return redirect(url_for("gerenciar_usuarios"))

        # exclusão em cascata manual (mesma lógica de excluir_perfil)
        cursor.execute("SELECT ID_SIMULACAO FROM SIMULACAO WHERE ID_USUARIO = ?", (id_usuario,))
        simulacoes = [x[0] for x in cursor.fetchall()]
        for id_simulacao in simulacoes:
            cursor.execute("SELECT ID_EMPRESTIMO FROM EMPRESTIMO WHERE ID_SIMULACAO = ?", (id_simulacao,))
            emprestimos = [x[0] for x in cursor.fetchall()]
            for id_emp in emprestimos:
                cursor.execute("DELETE FROM PARCELA WHERE ID_EMPRESTIMO = ?", (id_emp,))
            cursor.execute("DELETE FROM EMPRESTIMO WHERE ID_SIMULACAO = ?", (id_simulacao,))
        cursor.execute("DELETE FROM SIMULACAO WHERE ID_USUARIO = ?", (id_usuario,))
        cursor.execute("DELETE FROM MOV_FINANCEIRA WHERE ID_USUARIO = ?", (id_usuario,))
        cursor.execute("DELETE FROM HISTORICO_SENHA WHERE ID_USUARIO = ?", (id_usuario,))
        cursor.execute("DELETE FROM USUARIO WHERE ID_USUARIO = ?", (id_usuario,))
        conexao.commit()
        flash("Usuário excluído.", "sucesso")
    except Exception:
        conexao.rollback()
        app.logger.exception("Erro ao excluir usuário.")
        flash("Não foi possível excluir o usuário.", "erro")
    finally:
        cursor.close()
        conexao.close()
    return redirect(url_for("gerenciar_usuarios"))


# ============================================================
# EXECUÇÃO
# ============================================================

# __name__ vale "__main__" só quando o arquivo é executado direto (python app.py).
# Se o arquivo for importado por outro, o servidor não sobe. debug=True reinicia ao salvar e mostra erros
# detalhados no navegador - use só em desenvolvimento, nunca em produção.
if __name__ == "__main__":
    # só roda o servidor se o arquivo for executado diretamente; debug=True recarrega sozinho e mostra erros detalhados
    app.run(debug=True)
