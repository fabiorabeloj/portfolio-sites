# Chapa Quente

Peça promocional demonstrativa de **18 segundos**, vertical **1080 × 1920**, com tipografia animada, reenquadramento suave, cortes na batida e trilha instrumental original. Marca fictícia do portfólio. O vídeo identifica **conceito demonstrativo e imagens de IA** durante toda a duração.

É motion design sobre duas imagens estáticas existentes. Não é filmagem de um restaurante, cliente contratado, depoimento, campanha executada ou prova de resultado comercial. A pessoa na imagem de preparo também é sintética; o recorte prioriza a chapa e o produto. Não houve geração de nova pessoa, animação facial ou troca de rosto.

## Assistir e revisar

- `chapa-quente-18s.mp4`: master H.264/yuv420p, 30 fps, AAC estéreo/48 kHz, pronto para reprodução.
- `capa.png`: capa gráfica vertical.
- `contato-quadros.jpg`: 36 amostras, uma a cada meio segundo, cobrindo o vídeo inteiro.
- `contato-cortes.jpg`: quadro anterior e posterior a cada um dos quatro cortes.
- `verificacao-publica.json`: medidas e resultado dos checks do master final.

## Edição

| Tempo | Intenção | Texto principal |
|---|---|---|
| 0–2,4 s | Gancho com produto em destaque | Bateu a fome? |
| 2,4–6 s | Preparo e mudança de enquadramento | Começa na chapa. |
| 6–9,6 s | Detalhe de textura e ingredientes | Cheddar. Bacon. E pronto. |
| 9,6–13,2 s | Retorno ao produto inteiro | Capricho em cada camada. |
| 13,2–18 s | Assinatura e chamada final | Chapa Quente. Qual é o seu pedido? |

O desenho mantém a paleta do conceito existente: carvão, creme e laranja. Textos importantes ficam entre x=96 e x=910, y=160 e y=1560. Essas margens são uma referência conservadora para celular; interfaces e legendas adicionadas pela plataforma precisam de nova conferência no destino. As letras entram com deslocamento suave. O movimento não transforma as imagens em cenas filmadas.

O áudio é criado por senoides, ruído e envelopes, com semente fixa: percussão, baixo e notas dedilhadas a 100 BPM. Não usa samples, música de terceiros, voz ou modelo de áudio. O fechamento termina com a marca visível e redução gradual do som.

## Gerar novamente

Requer Python com **Pillow e NumPy**, FFmpeg e ffprobe lado a lado. Ambiente usado: Python 3.13.14, Pillow 12.2.0, NumPy 2.5.0 e FFmpeg 9.0.2. Nada é instalado, baixado ou enviado à rede pelos scripts. O render usa CPU, encoder libx264 com duas threads e filtros com uma thread. Não importa bibliotecas de modelos de IA.

Execute dentro desta pasta, com o Python do ambiente que já contém as bibliotecas:

```powershell
python render.py --ffmpeg ffmpeg
python verificar.py --ffmpeg ffmpeg
```

Se o FFmpeg não estiver no PATH, substitua `ffmpeg` pelo caminho do executável instalado. A variável `FFMPEG_BIN` também é aceita. `ffprobe` deve estar na mesma pasta. O projeto editável é `projeto.json`; as duas imagens necessárias estão em `assets/`. `render.py` gera também `audio-original.wav`, sem dependência de áudio externo.

O render usa **Impact** e **Segoe UI Semibold** instaladas no Windows. Para outro ambiente, configure `VIDEO_FONT_TITLE` e `VIDEO_FONT_BODY` com fontes devidamente licenciadas e repita a conferência de layout. Os arquivos de fonte não acompanham o pacote. Alterar fontes, bibliotecas ou encoder pode mudar pixels e hash; a reprodução bit a bit não é prometida entre ambientes.

## Direitos e procedência

As imagens vieram do conceito próprio Chapa Quente do portfólio existente, com reaproveitamento autorizado para esta demonstração e integração após revisão. O LEIA-ME e o HTML de origem as identificam como imagens de IA. O provedor/modelo gerador e a licença dos pesos **não estão comprovados nas fontes disponibilizadas**. Não atribuir uma licença aberta genérica às imagens nem prometer exclusividade. `manifesto-publico.json` registra essa limitação e os hashes das duas cópias.

A licença MIT em `LICENSE` cobre somente os scripts e a composição/síntese originais desta entrega. Não cobre imagens, marcas nem fontes. A [orientação da Microsoft](https://learn.microsoft.com/en-us/typography/fonts/font-faq) distingue texto rasterizado em gráficos/vídeo da redistribuição dos arquivos de fonte. O pacote contém apenas o texto renderizado; nenhuma TTF é embutida ou distribuída.

FFmpeg/ffprobe e bibliotecas também não são distribuídos. O build FFmpeg usado declara GPL versão 3 ou posterior; Pillow e NumPy mantêm suas próprias licenças nas instalações respectivas. Não houve aquisição de licença, serviço ou pacote pago.

## Verificação e limites

O master final foi decodificado integralmente, incluindo áudio. Foram contados 540 quadros, conferidos codecs, resolução, duração, sincronismo, ausência de quadro preto acidental e níveis de áudio. O contato temporal, os pares de cortes e quadros em resolução completa foram inspecionados. A entrada dos títulos e o aviso persistente têm caixas medidas; uma sobreposição na entrada de “CAMADA” foi corrigida antes do fechamento.

A verificação de áudio registrada é técnica: intensidade integrada e pico verdadeiro, com fade no início/fim. Não é uma avaliação subjetiva de mixagem ou prova de desempenho em todos os alto-falantes. A aprovação editorial final e a publicação no portfólio pertencem à revisão de integração. Não há métricas de vendas ou de alcance.

O ZIP público usa uma lista explícita de arquivos e exclui caminhos pessoais, logs internos e o erro de trava da tentativa do assistente local. `SHA256SUMS.txt` permite conferir seus componentes. Os recibos completos permanecem na pasta de trabalho, separados do pacote público.
