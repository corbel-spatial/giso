# Contributing

Questions and suggestions are welcomed in the [Issues section](https://github.com/corbel-spatial/giso/issues). 
The information below will help you set up a development environment if you wish to submit pull requests.

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
pixi run test
```
