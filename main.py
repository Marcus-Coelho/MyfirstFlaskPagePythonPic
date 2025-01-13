from comunidade import app
import os

if __name__ == '__main__':
    # Obter a porta da variável de ambiente "PORT" ou usar 5000 como padrão
    port = int(os.environ.get("PORT", 5000))
    
    # Configurar o host para "0.0.0.0" para que o Railway consiga acessar o servidor
    app.run(host="0.0.0.0", port=port, debug=False)

