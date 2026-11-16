# Sites, vídeo e automação · Fabio Rabelo

Um caso de site premium, três páginas para negócios locais, vídeo e automação CSV. São conceitos fictícios, com código, fontes selecionadas e comandos de reprodução. Não há envio de mensagens, pedidos ou reserva de horários.

**[Ver ao vivo →](https://fabiorabeloj.github.io/portfolio-sites/)**

## Alto Lume · caso premium

[Explorar o site](https://fabiorabeloj.github.io/portfolio-sites/examples/premium/site/) · [Fontes, reprodução e direitos](examples/premium/README.md) · [Ficha e limites](examples/premium/FICHA.md)

Conceito de pousada com **25 páginas**, entradas em português, inglês e espanhol e simuladores localizados. Inclui três acomodações, experiências, seis guias em português, perguntas, contato, temas e galerias. As prévias de contato e da estadia ficam na própria página. Reserva confirmada, pagamento, disponibilidade real e administração não estão integrados.

O caso reaproveita a base genérica Alto Lume do serviço Site de experiência, de referência comercial **R$ 8.000**. É uma demonstração própria, sem cliente ou venda realizada. O escopo desta cópia é 25 páginas e três idiomas de entrada; não inclui material escolar.

Para explorar, use o servidor da raiz e abra `/examples/premium/site/`. Para servir o caso separadamente, execute de `examples/premium`: `python -m http.server 8000 --bind 127.0.0.1 --directory site`. Encerre com `Ctrl+C`. Os caminhos relativos funcionam em subpasta.

O site preserva `noindex`. Canonical, compartilhamento e sitemap usam `example.invalid` como referência neutra, descrita no README do pacote. `_headers` depende de suporte da hospedagem; GitHub Pages não aplica esse arquivo como configuração de cabeçalhos. Não há promessa de indexação ou de operação de uma pousada real.

## Três páginas para negócios locais

| [Barbearia Brasa](https://fabiorabeloj.github.io/portfolio-sites/barbearia.html) | [Studio Aurora](https://fabiorabeloj.github.io/portfolio-sites/salao.html) | [Chapa Quente](https://fabiorabeloj.github.io/portfolio-sites/hamburgueria.html) |
|---|---|---|
| ![Barbearia Brasa](previas/barbearia.jpg) | ![Studio Aurora](previas/salao.jpg) | ![Chapa Quente](previas/hamburgueria.jpg) |
| Barbearia: hora marcada, tabela de preços, tema escuro | Salão: serviços por categoria, horários, tema claro | Hamburgueria: cardápio, horário, pedido rápido |

> Negócios fictícios. As fotos foram geradas por IA e os contatos são simulados: os botões mostram um aviso em vez de abrir o WhatsApp ou o mapa.

## Como foram feitos

- HTML, CSS e JavaScript puros, sem framework e sem etapa de build.
- Pensados primeiro para o celular; capturas completas em 390 px e 1440 px na pasta [`capturas/`](capturas/).
- Cada página tem chamada principal visível na primeira tela, preços ou cardápio sem precisar perguntar e, no fim, horário e informações de atendimento.

## Rodar localmente

```sh
python -m http.server 8000 --bind 127.0.0.1
```

Abra http://127.0.0.1:8000. Encerre com `Ctrl+C`. As páginas também abrem diretamente no navegador. Não há build, instalação npm, API, banco ou chave para estes três conceitos.

## Verificar e reproduzir

```sh
python tools/verificar.py
```

Python 3.10+ e biblioteca padrão. O comando confere os hashes de proveniência e os arquivos/âncoras locais dos HTML incluídos. Não substitui testes de interação, revisão visual ou acessibilidade completa. [Dependências](docs/DEPENDENCIAS.md) · [Proveniência e atribuições](docs/PROVENIENCIA.md).

## Vídeo e automação

| Projeto | Abrir | Reproduzir e conferir |
|---|---|---|
| Chapa Quente: motion design de 18 s sobre duas imagens de IA, com áudio original | [MP4](examples/video/chapa-quente-18s.mp4) · [quadros](examples/video/contato-quadros.jpg) | [Fontes, dependências e direitos](examples/video/README.md) |
| Pedidos em ordem: validar, normalizar e deduplicar CSV fictício | [Relatório interativo](https://fabiorabeloj.github.io/portfolio-sites/examples/automation/demo/resultado/relatorio.html) | [Código, fixture, 14 testes e reprodução](examples/automation/README.md) |

Na pasta `examples/automation`, execute `python -X utf8 -B demonstrar.py` para processar a mesma fixture duas vezes e comparar os resultados. Requer Python 3.12+, sem pacotes adicionais. As 12 linhas se dividem em quatro pedidos prontos, três duplicatas e cinco linhas para revisão. Não há envio, ERP, agenda ou conta real.

O vídeo é composição sobre imagens estáticas, com aviso de demonstração persistente. Não representa filmagem, campanha ou resultado comercial. As fontes do Windows e os binários de edição não são distribuídos. A origem declarada das imagens e os limites da evidência estão nos manifestos de cada pacote; não se promete exclusividade.

O verificador da raiz também confere os manifestos SHA-256 dos exemplos incluídos. [Critérios de incorporação](docs/INTEGRACAO.md).

---

**English:** a premium inn concept with 25 pages and Portuguese, English and Spanish entry points; three local-business landing pages; an 18-second motion-design video; and a runnable CSV automation example. Fictional businesses, identified AI images and local contact previews. Code, selected assets, instructions and limitations accompany each project. [Live demo](https://fabiorabeloj.github.io/portfolio-sites/).

Código original sob licença [MIT](LICENSE), com os avisos próprios de cada exemplo. Essa licença não se estende às imagens ou fontes por suposição. Feito por [Fabio Rabelo](https://github.com/fabiorabeloj).
