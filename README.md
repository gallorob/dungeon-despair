# Dungeon Despair
A PyGame reverse dungeon crawler.

## Installation
First create a Conda environment
```shell
conda create -n dungeon-despair python=3.10
```

Then activate the environment
```shell
conda activate dungeon-despair
```

## Running it

### Game with GUI
You can launch the game from the Python script:
```shell
python main_gui.py
```

Or you can compile the application into an executable file:
```shell
pyinstaller main_gui.spec
```

The executable will be placed in `./dist`.

### CLI Simulator
You can launch the simulator from the Python script:
```shell
python dd_cli.py run_simulation {SCENARIO_FINALENAME} {SIMULATION_TYPE} {SIMULATION_RUNS} {OUTPUT_FILENAME}
```

Or you can compile the application into an executable file:
```shell
pyinstaller dd_cli.spec
```

The executable will be placed in `./dist`.