# Lift
Lift contains custom tools to analyze python code.

## Installation

1. `git clone https://github.com/JeffreyMFarley/lift.git`
1. `cd lift`
3. Maybe virtual environment?  There is only one dependency now...
1. `pip install configargparse`
1. Install GraphViz

## Running

1. Customize the `config.ini` to the paths that you want
1. Go to the directory above where you want to analyze the code
1. `python -m lift -c lift/config.ini`

## Make the graphs

1. `find lift/gv -name "*.gv" -exec dot -Tpng -O {} \;`
