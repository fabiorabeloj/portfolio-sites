# Alto Lume · caso de site premium da Facility

Pousada fictícia apresentada em 25 páginas HTML, com entradas em português, inglês e espanhol. O caso reaproveita a base Alto Lume v2 do serviço Site de experiência, de referência comercial R$ 8.000. O material demonstra escopo e implementação do site por meio de um conceito próprio.

## Explorar

Abra a pasta `site/` com um servidor HTTP estático. Com Python já disponível, execute a partir desta pasta.

```text
python -m http.server 8000 --bind 127.0.0.1 --directory site
```

Abra `http://127.0.0.1:8000/`. Os recursos visuais, scripts e fontes acompanham o site. Os links relativos permitem hospedar a pasta na raiz ou em uma subpasta. As referências editoriais externas são links opcionais.

Percorra a página inicial, as três categorias de acomodação, experiências, seis guias, perguntas, contato e o simulador em `reservar/`. As entradas `en/` e `es/` apresentam conteúdo próprio nesses idiomas. Os guias extensos permanecem em português.

## Funções demonstradas

- Navegação entre páginas, menu móvel, tema claro/escuro e preferência de movimento reduzido.
- Cenas da manhã, entardecer e noite, com seleção por abas e pausa.
- Três acomodações com fotos responsivas e galeria ampliada.
- Simulador de estadia com categoria, capacidade, datas, mínimo de noites e desconto ilustrativo.
- Prévia local da mensagem da estadia e do formulário de contato.
- Perguntas organizadas, guias com índice, metadados e conteúdo em três idiomas.

As cenas, valores, políticas da pousada e regras de estadia são fictícios. O banner identifica o conceito e as imagens de IA. A prévia da mensagem permanece na página. Operação hoteleira, disponibilidade de quartos, reserva confirmada, pagamento, atendimento e cadastro administrativo requerem sistemas e configuração próprios.

## Estrutura e reprodução

O HTML, CSS e JavaScript de `site/` são os fontes editáveis desta cópia estática e podem ser servidos diretamente. `capturas/` contém provas visuais selecionadas da mesma versão. `FICHA.md` registra o escopo do ensaio e suas limitações.

Para gerar um pacote e o manifesto SHA-256 com a biblioteca padrão do Python, use uma saída nova fora desta pasta.

```text
python empacotar.py --saida ../alto-lume-premium.zip
```

O empacotador usa ordem de arquivos e datas ZIP fixas para permitir comparação de hashes. O manifesto cobre o site, o código e as capturas incluídas. Regenerar após uma edição produz um manifesto da versão nova. O arquivo ZIP deve ser revisado antes da integração no repositório de destino.

O arquivo `site/_headers` conserva os cabeçalhos da base para servidores compatíveis. A aplicação desses cabeçalhos depende da hospedagem. `robots.txt` e as marcações `noindex` identificam a demonstração. Canonical, compartilhamento e sitemap usam o domínio reservado `example.invalid` como referência neutra a ajustar pelo integrador ao destino aprovado.

## Imagens e fontes

As imagens são sintéticas, geradas anteriormente para o conceito Alto Lume. Duas cenas que continham mãos ou caminhantes foram substituídas por paisagens e ambientes já existentes. A relação dos recursos e os direitos estão em `DIREITOS.md` e `licencas/`.
