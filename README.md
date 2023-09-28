# macOS power consumption

This collection of scripts helps measure and compare power consumption in macOS using *powermetrics*.

## How to use it?

## Goal

The scripts rely on the native *powermetrics* app. Each call of *powermetrics* returns a large txt file that will be placed into the folder *powermetric-logs*. After all the measure are completed, used the *powermetrics-parse.py* to parse them and produce the SVG files summarizing and comparing the measures.  
A *run.sh* bash script is provided to run *powermetrics* in sudo mode, along with a *launch-test.scpt* Applescript that will pilot the tested application.

## Configuration

*powermetrics* is heavily dependant to the System on Chip og your mac. Each one will return different results. In order to help the parser, a *config.json* file is provided where you can define the regexp used to find the relevant information corresponding to a "device" (a part of the SoC such as the GPU or a CPU cluster).

## Steps

1. Modify the *config.json* according to the output of *powermetrics* on your machine
2. Modify *run.sh* to provide the output location of the *powermetrics* logs
3. Modify *launch-test.scpt* to launch the app to be tested and pilot it
4. Run *run.sh*
5. Run *powermetrics-parse.py*