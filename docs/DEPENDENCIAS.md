# Dependências

Os três conceitos usam HTML, CSS, JavaScript, imagens locais e fontes do sistema. Não dependem de CDN, API, banco ou formulário remoto. Não há instalação npm ou build.

O servidor opcional e o verificador usam Python 3.10+ e sua biblioteca padrão. Não precisam de ambiente virtual ou pacote pip. Também é possível abrir os HTML diretamente no navegador.

HTML-Validate, axe-core e Playwright/Edge foram usados na revisão local do autor. Não são dependências das páginas e não são distribuídos neste repositório. Seus resultados valem para o recorte verificado; não comprovam integração real ou acessibilidade completa.

O registro de autoria das imagens indica ComfyUI local, Z-Image Turbo e conversão para JPEG com FFmpeg. Esses programas e os pesos não são necessários para abrir as páginas e não são incluídos. A revisão/hash exata do checkpoint usado não consta no registro consultado.

## Exemplos executáveis

| Exemplo | Execução | Geração das provas |
|---|---|---|
| Alto Lume premium | HTML/CSS/JavaScript, imagens e fontes locais; servidor estático opcional | Empacotador em Python padrão; licenças das fontes no pacote |
| Automação CSV | Python 3.12+, biblioteca padrão | Relatório HTML local; capturas e MP4 já incluídos |
| Vídeo Chapa Quente | MP4 em navegador ou player compatível | Python, Pillow, NumPy, FFmpeg/ffprobe e fontes licenciadas; versões e comandos no README do pacote |

Os scripts não instalam dependências. O vídeo inclui fontes de edição e áudio original; os binários e arquivos de fontes do Windows não são distribuídos. A reprodução do vídeo foi conferida no ambiente Windows existente. Outro ambiente ou outra tipografia exige nova revisão do layout.

Cada exemplo declara suas próprias dependências, direitos e limites. A licença MIT do código não se estende a imagens ou fontes por suposição.
