[![Python](https://img.shields.io/badge/python-3.10%2B-blue)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Docker](https://img.shields.io/badge/docker-ready-blue)](https://www.docker.com/)

<h2>Pré-requisitos</h2>
<ul>
  <li><strong>Python 3.10+</strong></li>
  <li><strong>Docker</strong> para execução em container (Opcional)</li>
</ul>

<!-- Padronização do início do README para HTML -->
<h2>Instalação e Utilização</h2>

<h3>Rodando Localmente</h3>

<ol>
  <li><strong>Clone o repositório:</strong>
    <pre><code>git clone https://github.com/pedrobellezia/Scrapper-on-demand.git
</code></pre>
  </li>
  <li><strong>Crie um ambiente virtual e ative:</strong>
    <pre><code>python3 -m venv .venv
source .venv/bin/activate
</code></pre>
  </li>
  <li><strong>Instale as dependências:</strong>
    <pre><code>pip install -r requirements.txt
</code></pre>
  </li>
  <li><strong>Instale o Playwright:</strong>
    <pre><code>playwright install chromium
</code></pre>
  </li>
  <li><strong>Execute a aplicação:</strong>
    <pre><code>python app.py
</code></pre>
    O serviço estará disponível no seu IP na porta 5000.
  </li>
</ol>

<hr>

<h3>Rodando com Docker Compose</h3>

<p>Se preferir rodar a aplicação em um container Docker, basta executar o comando abaixo na raiz do projeto:</p>
<pre><code>docker compose up</code></pre>
<p>O serviço estará disponível no seu IP na porta 5000.</p>


<h2>Exemplo de requisição</h2>

Para utilizar o serviço, envie uma requisição POST para o endpoint `/execute_scrap` contendo um JSON com as instruções. Veja abaixo exemplos de como estruturar o JSON:

<h1>Estrutura do JSON</h1>
<p>O script é executado com base em uma série de parâmetros definidos num JSON, sendo ele dividido em duas seções: <code>options</code> e <code>steps</code>.</p>
<h2>Exemplo do JSON</h2>
<pre><code>{
  "options": {
    "headless": false,
    "slow_mo": 1000,
    "args": ["--disable-dev-shm-usage"]
  },
  "steps": [
    {
      "func": "go_to",
      "args": {
        "url": "www.exemplo.com"
      }
    },
    {
      "func": "wait",
      "args": {
        "seconds": 1
      }
    },
    {
      "func": "click",
      "args": {
        "xpath": "//label[span[contains(text(), 'teste')]]"
      }
    },
    {
      "func": "wait",
      "args": {
        "seconds": 20
      }
    }
  ]
}
</code></pre>
<h2><code>options</code></h2>
<p>Contém as configurações gerais do navegador e da funcionalidade do código.</p>
<ul>
<li><strong><code>headless</code></strong>: Define se o navegador será executado sem interface gráfica.
<ul>
<li><code>true</code>: O navegador será executado em segundo plano.</li>
<li><code>false</code>: O navegador será exibido durante a execução.</li>
</ul>
</li>
<li><strong><code>slow_mo</code></strong>: Tempo, em milissegundos, entre as ações executadas.</li>
<li><strong><code>args</code></strong>: Lista de argumentos adicionais para o navegador.
<ul>
<li>Consulte esta <a title="Lista de flags" href="https://peter.sh/experiments/chromium-command-line-switches/" target="_blank" rel="noopener">lista de flags</a> para saber quais argumentos podem ser utilizados.</li>
</ul>
</li>
</ul>
<h3>Exemplo:</h3>
<pre><code>"options": {
  "headless": false,
  "slow_mo": 1000,
  "args": ["--disable-dev-shm-usage"]
}
</code></pre>

<h2><code>steps</code></h2>
<p>Define a sequência de ações executadas pelo script. Cada ação é um objeto que possui 2 item:</p>
<ul>
<li><strong><code>func</code></strong>: Nome da função a ser executada.</li>
<li><strong><code>args</code></strong>: argumentos utilizados na função.</li>
</ul>
<hr>
<h3>Observações</h3>
<h4>Uso de variáveis</h4>
<p>As variáveis previamente salvas durante a execução podem ser utilizadas em qualquer campo.</p>
<p>Existem duas formas de acessar uma variável:</p>
<ul>
<li><strong>Forma direta:</strong> <code>"xpath": "$ref/nome_da_variavel"</code></li>
<li><strong>Interpolação:</strong> <code>"text": "Olá, {$ref/nome_da_variavel}!"</code></li>
</ul>
<p>Essas variáveis devem ter sido definidas anteriormente através de um método.</p>
<p>No retorno da API enviado ao usuário, estarão todas as variáveis salvas com seus respectivos valores.</p>
<h4>Ignorar execução ou erros de passos</h4>
<p>dentro dos argumentos de qualquer método pode ser adicionado os argumentos opcionais:</p>
<ul>
<li><strong><code>ignore_execution</code></strong>: Se <code>true</code>, o passo será completamente ignorado e não será executado. (False por padrão)</li>
<li><strong><code>ignore_error</code></strong>: Se <code>true</code>, o erro gerado durante a execução será ignorado, e a sequência continuará normalmente. (False por padrão)</li>
</ul>
<p><strong>Exemplo:</strong></p>
<pre><code>{
  "func": "click",
  "args": {
    "xpath": "//button[@id='continuar']",
    "ignore_error": true
  }
}
</code></pre>

<h2>Lista de Funções Disponíveis</h2>
<h3><code>go_to</code></h3>
<ul>
<li><strong>Descrição:</strong> Navega até uma URL.</li>
<li><strong>Argumentos:</strong>
<ul>
<li><code>url</code>: URL de destino.</li>
</ul>
</li>
</ul>
<p><strong>Exemplo:</strong></p>
<pre><code>{
  "func": "go_to",
  "args": {
    "url": "www.exemplo.com"
  }
}
</code></pre>
<hr>
<h3><code>wait</code></h3>
<ul>
<li><strong>Descrição:</strong> mantém o código em aguardo por uma quantidade de segundos</li>
<li><strong>Argumentos:</strong>
<ul>
<li><code>seconds</code> (float): Tempo de espera em segundos.</li>
</ul>
</li>
</ul>
<p><strong>Exemplo:</strong></p>
<pre><code>{
  "func": "wait",
  "args": {
    "seconds": 2
  }
}
</code></pre>
<hr>
<h3><code>insert</code></h3>
<ul>
<li><strong>Descrição:</strong> Preenche um campo de texto localizado por XPath.</li>
<li><strong>Argumentos:</strong>
<ul>
<li><code>xpath</code>: XPath do campo de texto.</li>
<li><code>text</code>: Texto a ser inserido.</li>
</ul>
</li>
</ul>
<p><strong>Exemplo</strong></p>
<pre><code>{
  "func": "insert",
  "args": {
    "xpath": "//input[@name='usuario']",
    "text": "admin"
  }
}
</code></pre>
<hr>
<h3><code>click</code></h3>
<ul>
<li><strong>Descrição:</strong> Clica em um elemento da página localizado por XPath.</li>
<li><strong>Argumentos:</strong>
<ul>
<li><code>xpath</code>: XPath do elemento.</li>
</ul>
</li>
</ul>
<p><strong>Exemplo:</strong></p>
<pre><code>{
  "func": "click",
  "args": {
    "xpath": "//button[@type='submit']"
  }
}
</code></pre>
<hr>
<h3><code>select_option</code></h3>
<ul>
<li><strong>Descrição:</strong> Seleciona uma ou mais opções de um <code>&lt;select&gt;</code> usando o <code>label</code> ou <code>value</code> das opções como parâmetro.</li>
<li><strong>Argumentos:</strong>
<ul>
<li><code>xpath</code> : XPath do elemento.</li>
<li><code>options_list</code> (array): Array contendo os valores (<code>label</code> ou <code>value</code>) dos elementos a serem selecionados.</li>
</ul>
</li>
</ul>
<p><strong>Exemplo:</strong></p>
<pre><code>{
  "func": "select_option",
  "args": {
    "xpath": "//select[@id='sexo']",
    "options_list": ["F"]
  }
}
</code></pre>
<hr>
<h3><code>set_timeout</code></h3>
<ul>
<li><strong>Descrição:</strong> Define, em milissegundos, o timeout para todas as ações.</li>
<li><strong>Argumentos:</strong>
<ul>
<li><code>timeout</code> (int): Tempo de timeout em milissegundos.</li>
</ul>
</li>
</ul>
<p><strong>Exemplo:</strong></p>
<pre><code>{
  "func": "set_timeout",
  "args": {
    "timeout": 10000
  }
}
</code></pre>
<hr>
<h3><code>select</code></h3>
<ul>
<li><strong>Descrição:</strong> verifica a existência de um elemento específico.</li>
<li><strong>Argumentos:</strong>
<ul>
<li><code>xpath</code>: XPath do elemento.</li>
</ul>
</li>
</ul>
<p><strong>Exemplo:</strong></p>
<pre><code>{
  "func": "select",
  "args": {
    "xpath": "\\div\\span[3]"
  }
}
</code></pre>
<hr>
<h3><code>captcha_solver</code></h3>
<ul>
<li><strong>Descrição:</strong> Resolve um CAPTCHA simples de imagem usando a API do <a href="https://2captcha.com/pt/" target="_blank" rel="noopener">2Captcha</a>. O código extraído da imagem é preenchido automaticamente no campo de input informado.<br>Caso <code>img_xpath</code> ou <code>input_xpath</code> não sejam fornecidos, o método tentará localizar e resolver automaticamente um CAPTCHA do tipo reCAPTCHA v2 na página.</li>
<li><strong>Observação:</strong> Esse método ainda está em desenvolvimento, portanto, o modo automático <strong>não funciona</strong> corretamente se a página possuir mais de um CAPTCHA do mesmo tipo.</li>
<li><strong>Argumentos:</strong>
<ul>
<li><code>api_key</code>: Chave da API 2Captcha. <strong>Obrigatório.</strong></li>
<li><code>img_xpath</code>: XPath da imagem do CAPTCHA (modo manual).</li>
<li><code>input_xpath</code>: XPath do campo onde o código resolvido será inserido (modo manual).</li>
</ul>
</li>
</ul>
<p><strong>Exemplo (modo manual):</strong></p>
<pre><code>{
  "func": "captcha_solver",
  "args": {
    "api_key": "API_KEY",
    "img_xpath": "//img[@id='captcha']",
    "input_xpath": "//input[@name='captcha_input']"
  }
}
</code></pre>
<p><strong>Exemplo (modo automático):</strong></p>
<pre><code>{
  "func": "captcha_solver",
  "args": {
    "api_key": "API_KEY"
  }
}
</code></pre>
<hr>
<h3><code>save_file</code></h3>
<ul>
<li><strong>Descrição:</strong> Clica em um elemento da página que dispara o download de um arquivo. O arquivo será salvo em um diretório informado com um nome gerado aleatoriamente.</li>
<li><strong>Argumentos:</strong>
<ul>
<li><code>xpath</code>: XPath do botão ou link que dispara o download.</li>
<li><code>path</code>: Caminho do diretório onde o arquivo será salvo.</li>
</ul>
</li>
</ul>
<p><strong>Exemplo:</strong></p>
<pre><code>{
  "func": "save_file",
  "args": {
    "xpath": "//a[@id='download_pdf']",
    "path": "./downloads"
  }
}
</code></pre>
<hr>
<h3><code>page_to_pdf</code></h3>
<ul>
<li><strong>Descrição:</strong> Imprime a pagina atual num PDF, o PDF é salvo no caminho especificado e é dado um nome aleatório para ele.</li>
<li><strong>Argumentos:</strong>
<ul>
<li><code>path</code>: Caminho do diretório onde o PDF será salvo.</li>
</ul>
</li>
</ul>
<p><strong>Exemplo:</strong></p>
<pre><code>{
  "func": "page_to_pdf",
  "args": {
    "path": "./downloads"
  }
}</code></pre>
<hr>
<h3><code>wait_url_change</code></h3>
<ul>
<li><strong>Descrição:</strong> Aguarda a mudança da URL atual.</li>
<li><strong>Argumentos:</strong>
<ul>
<li><code>timeout</code> (int): Tempo máximo de espera em milissegundos.</li>
</ul>
</li>
</ul>
<p><strong>Exemplo:</strong></p>
<pre><code>{
  "func": "wait_url_change",
  "args": {
    "timeout": 10000
  }
}</code></pre>
<hr>
<h3><code>request_pdf</code></h3>
<ul>
<li><strong>Descrição:</strong> Baixa a página como PDF caso a URL aponte diretamente para um PDF. Se o campo <code>url</code> não for informado, utiliza-se a URL atual da página.</li>
<li><strong>Argumentos:</strong>
<ul>
<li><code>url</code> (opcional): URL da página.</li>
<li><code>path</code>: Caminho do diretório onde o arquivo será salvo.</li>
</ul>
</li>
</ul>
<p><strong>Exemplo:</strong></p>
<pre><code>{
  "func": "request_pdf",
  "args": {
    "url": "https://exemplo.com/documento.pdf",
    "path": "./downloads"
  }
}</code></pre>
<hr>
<h3><code>read_inner_text</code></h3>
<ul>
<li><strong>Descrição:</strong> Salva em uma variável o texto interno de um elemento HTML.</li>
<li><strong>Argumentos:</strong>
<ul>
<li><code>xpath</code>: XPath do elemento.</li>
<li><code>name</code>: Nome da variável onde o texto será salvo.</li>
</ul>
</li>
</ul>
<p><strong>Exemplo:</strong></p>
<pre><code>{
  "func": "read_inner_text",
  "args": {
    "xpath": "//span[@id='mensagem']",
    "name": "mensagem_texto"
  }
}</code></pre>
<hr>
<h3><code>read_attribute</code></h3>
<ul>
<li><strong>Descrição:</strong> Salva o valor de um atributo HTML em uma variável.</li>
<li><strong>Argumentos:</strong>
<ul>
<li><code>xpath</code>: XPath do elemento.</li>
<li><code>attribute</code>: Nome do atributo a ser lido.</li>
<li><code>name</code>: Nome da variável onde o valor será salvo.</li>
</ul>
</li>
</ul>
<p><strong>Exemplo:</strong></p>
<pre><code>{
  "func": "read_attribute",
  "args": {
    "xpath": "//img[@id='imagem']",
    "attribute": "src",
    "name": "imagem_base64"
  }
}</code></pre>
<hr>
<h3><code>confirm_popup</code></h3>
<ul>
<li><strong>Descrição:</strong> Aceita automaticamente qualquer popup de confirmação (diálogo) que aparecer na página, durante o tempo especificado pelo usuário. Este método <strong>não interrompe</strong> o fluxo do script, a execução continua normalmente enquanto este método trata os popups em segundo plano.</li>
<li><strong>Argumentos:</strong>
<ul>
<li><code>timeout</code> (int): Tempo total, em milissegundos, durante o qual a escuta ficará ativa para aceitar popups.</li>
</ul>
</li>
</ul>
<p><strong>Exemplo:</strong></p>
<pre><code>{
  "func": "confirm_popup",
  "args": {
    "timeout": 10000
  }
}
</code></pre>
<hr>
<h3><code>backspace</code></h3>
<ul>
<li><strong>Descrição:</strong> Pressiona a tecla <code>Backspace</code> repetidamente.</li>
<li><strong>Argumentos:</strong>
<ul>
<li><code>times</code> (int): Quantidade de vezes que a tecla será pressionada.</li>
</ul>
</li>
</ul>
<p><strong>Exemplo:</strong></p>
<pre><code>{
  "func": "backspace",
  "args": {
    "times": 10
  }
}</code></pre>
<hr>
<h3><code>create_variables</code></h3>
<ul>
<li><strong>Descrição:</strong> Cria inúmeras variáveis .</li>
<li><strong>Argumentos:</strong>
<ul>
<li><code>"nome":"valor"</code>: Qualquer par chave/valor representando o nome da variável e seu conteúdo.</li>
</ul>
</li>
</ul>
<p><strong>Exemplo:</strong></p>
<pre><code>{
  "func": "create_variables",
  "args": {
    "cpf": "12345678901",
    "email": "teste@exemplo.com"
  }
}</code></pre>
<hr>
<h3><code>batch_mode</code></h3>
<ul>
<li><strong>Descrição:</strong> Itera sobre métodos com base em uma lista de valores fornecida.</li>
<li><strong>Argumentos:</strong>
<ul>
<li><code>methods</code>: Lista de métodos a serem executados em cada iteração.</li>
<li><code>"nome":[valores]</code>: Um ou mais pares chave/valor, contendo listas de valores que serão atribuídos a cada variável nas iterações.</li>
</ul>
</li>
</ul>
<p><strong>Funcionamento:</strong></p>
<ul>
<li>Você pode declarar quantas variáveis quiser no formato <code>"nome_da_variavel": [valores]</code>.</li>
<li>Todas as listas de variáveis devem ter o mesmo comprimento. Esse comprimento define o número de iterações.</li>
<li>Os métodos definidos em <code>methods</code> são executados sequencialmente a cada iteração, podendo utilizar os valores atuais das variáveis.</li>
<li>As variáveis podem ser utilizadas de duas formas:
<ul>
<li><strong>Forma direta:</strong> <code>%var/nome_da_variavel</code></li>
<li><strong>Interpolação:</strong> <code>{%var/nome_da_variavel}</code> dentro de strings</li>
</ul>
</li>
<li>Os métodos em <code>methods</code> são escritos exatamente como seriam fora da função <code>batch_mode</code>, com a vantagem de acessar as variáveis definidas na iteração.</li>
</ul>
<p><strong>Exemplo:</strong></p>
<pre><code>{
  "func": "batch_mode",
  "args": {
    "var1": ["value1", "value2", "value3"],
    "var2": ["valueA", "valueB", "valueC"],
    "methods": [
      {
        "func": "go_to",
        "args": {
          "url": "example.com"
        }
      },
      {
        "func": "insert",
        "args": {
          "xpath": "//*[@name='{%var/var2}']",
          "text": "%var/var1"
        }
      }
    ]
  }
}
</code></pre>
