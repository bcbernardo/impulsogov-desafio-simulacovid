# Desafio ImpulsoGov - SimulaCovid

*Este repositório contém a descrição e a implementação de análises em resposta
ao desafio de ciência de dados da ImpulsoGov disponível
[neste outro repositório][Desafio].*

A [Impulso] é uma organização da sociedade civil que tem como missão
potencializar governos para entregar melhores serviços públicos aos cidadãos
que mais precisam. Desde março de 2019, tem trabalhado com governos municipais
e estaduais e com outras organizações da sociedade civil para o combate à
emergência sanitária gerada pela COVID-19, por meio da disponibilização de
informação qualificada, dados, ferramentas e suporte especializado.

Saiba mais em: [Coronacidades.org]

[Coronacidades.org]: https://coronacidades.org/
[Desafio]: https://github.com/ImpulsoGov/techdados_desafio_datasience
[Impulso]: https://www.impulsogov.com.br

## Início rápido

Para executar a análise descrita nos passos seguintes em sua própria máquina,
você deve primeiro clonar este repositório para um diretório local:

```text
$ git clone https://github.com/bcbernardo/impulsogov-desafio-simulacovid
$ cd impulsogov-desafio-simulacovid
```

Os notebooks dependem de uma instalação local do gerenciador de pacotes
[`conda`][Conda], bem como do utilitário [`anaconda-project`][Anaconda Project].
Visite a [página de instalação][Miniconda] do Miniconda para obter uma
instalação minimalista do gerenciador de pacotes. Em seguida, instale o
`anaconda-project`:

```text
$ conda install anaconda-project
```

Uma vez que você tenha essas dependências instaladas e listadas entre os
diretórios com executáveis na sua máquina (`$PATH`), você pode rodar as
análises com um único comando a partir do diretório local onde instalou o
repositório:

```text
$ anaconda-project run
```

[Anaconda Project]: https://anaconda-project.readthedocs.io
[Conda]: https://docs.conda.io
[Miniconda]: https://docs.conda.io/en/latest/miniconda.html

## Estrutura do repositório

<!-- TODO -->

## O desafio

### Contexto

Como parte do processo de seleção da pessoa responsável pelo desenvolvimento de
análises e produtos digitais, a Impulso disponibilizou um desafio real,
relacionado à ferramenta "*SimulaCovid*".

Trata-se de um simulador de demanda hospitalar desenvolvido pela organização
para prever a quantidade adicional de leitos enfermaria e UTI necessários para
lidar com os efeitos da pandemia de SARS-CoV-2 nas unidades federativas
brasileiras.

Atualmente, a ferramenta utiliza um modelo SEIR (Suscetíveis,
Expostos, Infectados e Removidos) baseado em [Hill (2020)] para projetar o
número de casos necessitando de hospitalização e cuidados intensivos nos dias e
semanas seguintes. As entradas utilizadas nos modelos são provenientes de dados abertos, que são consolidados e distribuídos pela plataforma [FarolCovid].

[FarolCovid]: https://github.com/ImpulsoGov/farolcovid
[Hill (2020)]: https://github.com/alsnhll/SEIR_COVID19

### Limitações do modelo atual

<!-- TODO -->

### Hipóteses explicativas

<!-- TODO -->

### Implementação

<!-- TODO -->

### Discussão

<!-- TODO -->

## Referências

<!-- TODO -->

## Licença

Copyright 2020 Bernardo Chrispim Baron

O uso deste código fonte é regida por uma licença do tipo MIT, que pode ser
encontrada no arquivo [LICENSE](./LICENSE) ou em
<https://opensource.org/licenses/MIT>.
