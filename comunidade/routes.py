import os
from flask import render_template, request, redirect, url_for, flash, abort
from comunidade import app, database, bcrypt
from comunidade.forms import FormLogin, FormCriarConta, FormEditarPerfil, PostForm
from comunidade.models import Usuario, Post
from flask_login import login_user, logout_user
from flask_login import current_user  # noqa: F401 # uso para verificar se usuário está logado
from flask_login import login_required # uso para permitir acesso a páginas somente se usuário estiver logado
from flask import send_from_directory, current_app
from PIL import Image, ExifTags, ImageOps
from datetime import datetime

def atualizar_cursos(form):
    
    lista_de_cursos = []  # Inicializa uma lista vazia

    for campo in form:
        if "curso_" in campo.name:  # Verifica se o campo é relacionado a cursos
            if campo.data:  # Verifica se o campo está marcado ou preenchido
                # Adiciona o curso à lista de cursos
                lista_de_cursos.append(campo.label.text)

    # Após o loop, cria a string de cursos ou define como "Não informado"
    if lista_de_cursos:
        lista_cursos_string = ";".join(lista_de_cursos)  # Junta os cursos com ";"
    else:
        lista_cursos_string = 'Não informado'  # Define como "Não informado" se vazio

    return lista_cursos_string



@app.route("/")
def home():
    posts = Post.query.order_by(Post.data_criacao.desc()).all()
    for post in posts:
        post.corpo_red = f"{post.corpo[:50]}..." if len(post.corpo) > 50 else post.corpo
    usuarios = {usuario.id: usuario.username for usuario in Usuario.query.all()}
    foto_usuarios = {usuario.id: usuario.foto_perfil for usuario in Usuario.query.all()}
    return render_template('home.html', posts=posts, usuarios=usuarios, foto_usuarios=foto_usuarios)


@app.route("/contatos")
def contatos():
    return render_template('contatos.html')

@app.route('/usuarios')
@login_required
def usuarios():
    # Consultar todos os usuários da tabela Usuario
    lista_usuarios = Usuario.query.all()
    
    # Criar um dicionário com a quantidade de posts de cada usuário
    posts_por_usuario = {
        usuario.id: Post.query.filter_by(id_usuario=usuario.id).count() for usuario in lista_usuarios
    }
    
    return render_template('usuarios.html', lista_usuarios=lista_usuarios, posts_por_usuario=posts_por_usuario)

@app.route('/login', methods=['GET', 'POST'])
def login():
    form_login = FormLogin()
    # Lógica do login
    if form_login.validate_on_submit() and 'botao_submit_login' in request.form:
        usuario = Usuario.query.filter_by(email=form_login.email.data).first()

        if usuario and bcrypt.check_password_hash(usuario.senha, form_login.senha.data):
            # Fazer o login
            login_user(usuario, remember=form_login.lembrar_dados.data)

            flash(f'Login feito com sucesso no e-mail: {form_login.email.data}', 'alert-primary')

            # Redireciona para a próxima página, se existir
            parametro_next = request.args.get('next')
            if parametro_next:
                return redirect(parametro_next)
            else:
                return redirect(url_for('home'))  # Redireciona para a função 'home'

        else:
            flash('Usuário ou senha incorretos', 'alert-danger')

    # Retorna a página de login (para GET e falhas no POST)
    return render_template('login.html', form_login=form_login)

            


@app.route('/criarconta', methods=['GET', 'POST'])
def criarconta():
    form_criar_conta = FormCriarConta()  # Instância do formulário

    if form_criar_conta.validate_on_submit() and 'botao_submit_criar_conta' in request.form:
        # Criar usuário com os dados da instância do formulário
        
        # implantação de senha criptografada
        senha_cryptografada = bcrypt.generate_password_hash(form_criar_conta.senha.data).decode("utf-8")
        usuario = Usuario(
            username=form_criar_conta.username.data,  # Acessando dados da instância
            email=form_criar_conta.email.data,
            senha=senha_cryptografada
        )
    
        # Adicionar o usuário ao banco de dados
        database.session.add(usuario)
        database.session.commit()

        flash(f'Conta criada para o e-mail: {form_criar_conta.email.data}', 'alert-primary')
        return redirect(url_for('home'))

    return render_template('criarconta.html', form_criar_conta=form_criar_conta)

@app.route('/sair')
@login_required
def sair():
    logout_user()
    flash('Logout success!', 'alert-success')
    return redirect(url_for('home'))

# Opção 1: Função separada para processamento de imagem
from PIL import Image, ImageOps
import os
from flask import current_app

def process_profile_photo(photo_file, user_id, max_size=(155, 155)):
    """
    Processa e salva uma foto de perfil com tratamento adequado de orientação.
    
    Args:
        photo_file: Arquivo de imagem do formulário
        user_id: ID do usuário para o nome do arquivo
        max_size: Tupla de (largura, altura) para tamanho máximo da imagem
    
    Returns:
        str: Nome do arquivo salvo
    """
    try:
        # Obter extensão do arquivo
        extensao_arquivo = os.path.splitext(photo_file.filename)[1].lower()
        
        # Criar nome do arquivo
        nome_arquivo = f'foto_perfil_{user_id}{extensao_arquivo}'
        
        # Criar caminho completo
        caminho_arquivo = os.path.join(current_app.root_path, 'static/fotos_perfil', nome_arquivo)
        
        # Abrir e processar imagem
        with Image.open(photo_file) as img:
            # Aplicar correção de orientação
            img = ImageOps.exif_transpose(img)
            
            # Converter para RGB se necessário (tratamento para PNGs com transparência)
            if img.mode in ('RGBA', 'LA'):
                background = Image.new('RGB', img.size, 'white')
                background.paste(img, mask=img.split()[-1])
                img = background
            elif img.mode != 'RGB':
                img = img.convert('RGB')
            
            # Redimensionar mantendo proporção
            img.thumbnail(max_size, Image.Resampling.LANCZOS)
            
            # Salvar com qualidade otimizada
            img.save(caminho_arquivo, 'JPEG', quality=85)
            
        return nome_arquivo
        
    except Exception as e:
        print(f"Erro ao processar imagem: {e}")
        raise

# Opção 2: Rota com processamento integrado
@app.route('/perfil', methods=['GET', 'POST'])
@login_required
def editaperfil():
    
    foto_perfil = url_for('static', filename=f"fotos_perfil/{current_user.foto_perfil}")
    form = FormEditarPerfil()

    # Contar a quantidade de posts do usuário logado
    quantidade_posts = Post.query.filter_by(id_usuario=current_user.id).count()
    
    if form.validate_on_submit():  # Validação dos campos do formulário
        current_user.username = form.username.data  # Atualiza o nome de usuário
        current_user.email = form.email.data  # Atualiza o e-mail

        # Atualizar a foto de perfil, se enviada
        if form.foto_perfil.data:
            foto = form.foto_perfil.data
            extensao_arquivo = os.path.splitext(foto.filename)[1].lower()
            formatos_permitidos = {'.jpg', '.jpeg', '.png', '.gif'}

            if extensao_arquivo not in formatos_permitidos:
                flash('Formato de imagem não suportado. Por favor, envie uma imagem nos formatos JPG, PNG ou GIF.', 'alert-danger')
            else:
                try:
                    # Opção 1: Usar a função separada
                    novo_nome_arquivo = process_profile_photo(foto, current_user.id)
                    current_user.foto_perfil = novo_nome_arquivo
                    
                    # Opção 2: Usar o processamento integrado
                    """
                    # Nome do arquivo com ID do usuário
                    nome_arquivo = f'foto_perfil_{current_user.id}{extensao_arquivo}'
                    caminho_arquivo = os.path.join(app.root_path, 'static/fotos_perfil', nome_arquivo)

                    # Reduzir o tamanho da foto
                    tamanho_imagem = (155,155)
                    
                    with Image.open(foto) as foto_reduzida:
                        foto_reduzida = ImageOps.exif_transpose(foto_reduzida)
                        
                        if foto_reduzida.mode in ('RGBA', 'LA'):
                            background = Image.new('RGB', foto_reduzida.size, 'white')
                            background.paste(foto_reduzida, mask=foto_reduzida.split()[-1])
                            foto_reduzida = background
                        elif foto_reduzida.mode != 'RGB':
                            foto_reduzida = foto_reduzida.convert('RGB')
                        
                        foto_reduzida.thumbnail(tamanho_imagem, Image.Resampling.LANCZOS)
                        foto_reduzida.save(caminho_arquivo, 'JPEG', quality=85)
                        
                    current_user.foto_perfil = nome_arquivo
                    """

                except Exception as e:
                    print(f"Erro ao processar a imagem: {e}")
                    flash('Erro ao processar a imagem. Por favor, tente novamente.', 'alert-danger')

        # Atualizar o campo de cursos
        current_user.cursos = atualizar_cursos(form)

        # Salvar alterações no banco de dados
        database.session.commit()
        flash('Perfil atualizado com sucesso!', 'alert-success')
        return redirect(url_for('editaperfil'))

    elif form.errors:  # Exibe mensagens de erro, caso existam
        for campo, mensagens in form.errors.items():
            for mensagem in mensagens:
                flash(f'Erro no campo {campo}: {mensagem}', 'alert-danger')

    return render_template('perfil.html', form=form, foto_perfil=foto_perfil,quantidade_posts=quantidade_posts)

@app.route('/postagens/criar_post', methods=['GET', 'POST'])
@login_required
def criar_post():
    form = PostForm()
    if form.validate_on_submit():
        novo_post = Post(
            titulo=form.titulo.data,
            corpo=form.corpo.data,
            data_criacao=datetime.now(),
            id_usuario=current_user.id)
        database.session.add(novo_post)
        database.session.commit()
        flash('Post criado com sucesso!', 'alert-success')
        return redirect(url_for('home'))  # Assumindo que exista uma rota para listar postagens
        # provisoriamente estou usando home
    return render_template('criar_post.html', form=form)




@app.route('/postagens/<int:post_id>', methods=['GET', 'POST'])
@login_required
def exibir_post(post_id):
    # Consulta o post pelo ID
    post = Post.query.get_or_404(post_id)
    usuario = Usuario.query.get(post.id_usuario)
    foto_usuario = usuario.foto_perfil if usuario else 'default.jpg'

    # Inicializa o formulário para edição
    form = PostForm(obj=post)

    if form.validate_on_submit():
        # Verifica se o usuário logado é o autor do post
        if post.id_usuario != current_user.id:
            flash('Você não tem permissão para editar este post.', 'alert-danger')
            return redirect(url_for('exibir_post', post_id=post_id))

        # Atualiza os dados do post
        post.titulo = form.titulo.data
        post.corpo = form.corpo.data
        post.data_criacao = datetime.now()  # Atualiza a data para a edição
        database.session.commit()
        flash('Post atualizado com sucesso!', 'alert-success')

        # Redireciona para a mesma página atualizada
        return redirect(url_for('exibir_post', post_id=post.id))

    return render_template('post.html', post=post, usuario=usuario, foto_usuario=foto_usuario, form=form)


@app.route('/postagens/<int:post_id>/excluir', methods=['POST'])
@login_required
def excluir_post(post_id):
    post = Post.query.get_or_404(post_id)
    
    if post.id_usuario != current_user.id:
        abort(403)
    
    database.session.delete(post)
    database.session.commit()
    flash('Post excluído com sucesso!', 'alert-success')
    return redirect(url_for('home'))

@app.route('/postagens/<int:post_id>/editar', methods=['GET', 'POST'])
@login_required
def editar_post(post_id):  # Renomeado de `exibir_post` para `editar_post`
    post = Post.query.get_or_404(post_id)
    usuario = Usuario.query.get(post.id_usuario)
    foto_usuario = usuario.foto_perfil if usuario else 'default.jpg'

    # Inicializa o formulário para edição do post
    form = PostForm(obj=post)

    # Lógica de edição
    if form.validate_on_submit():
        if post.id_usuario != current_user.id:
            flash('Você não tem permissão para editar este post.', 'danger')
            return redirect(url_for('exibir_post', post_id=post_id))

        # Atualiza os dados do post
        post.titulo = form.titulo.data
        post.corpo = form.corpo.data
        post.data_criacao = datetime.now()  # Atualiza a data para a edição
        database.session.commit()
        flash('Post atualizado com sucesso!', 'success')

        # Redireciona para a mesma página do post atualizado
        return redirect(url_for('exibir_post', post_id=post.id))

    return render_template('editar_post.html', post=post, usuario=usuario, foto_usuario=foto_usuario, form=form)

@app.route('/favicon.ico')
def favicon():
    return send_from_directory(
        os.path.join(app.root_path, 'static'),
        'favicon.ico', mimetype='image/vnd.microsoft.icon'
    )



if __name__ == "__main__":
    app.run()

