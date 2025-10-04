# Contributing

Questions and suggestions are welcomed in the [Issues section](https://github.com/corbel-spatial/giso/issues). The information below will help you set up a 
development environment if you wish to submit pull requests.

## Development Environment Setup

First, install the [Pixi](https://pixi.sh/latest/installation/) package management tool. Then,

```shell
git clone https://github.com/corbel-spatial/giso.git
cd giso
pixi install -a
```

To test the CLI:

```shell
pixi shell -e dev
giso --help
```

To run the pytest suite:

```shell
pixi run test-py313
```

## IDE Support

Pixi has extenions that support various code editing applications. By default `pixi install` will install `pixi-pycharm` for [JetBrains PyCharm](https://pixi.sh/latest/integration/editor/jetbrains/), and you can set the project's Python interpreter to the `dev` environment.

Pixi also supports 
[VSCode](https://pixi.sh/latest/integration/editor/vscode/),
[Zed](https://pixi.sh/latest/integration/editor/zed/),
[RStudio](https://pixi.sh/latest/integration/editor/r_studio/), and
[JupyterLab](https://pixi.sh/latest/integration/editor/jupyterlab/).
