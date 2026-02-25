# dsda-failspots

Python script that generates an image of a map with spots where demo attempts end at. Can also generate a custom sized heatmap.

## How to run
You need a custom build of dsda-doom that outputs the position where the demo attempts end.

1. Install the required libraries with `pip install -r requirements.txt`
2. Download https://github.com/Pedro-Beirao/dsda-doom/releases/tag/v0.29.3-failspots
3. Copy the dsda-doom binary and dsda-doom.wad to the same folder as dsda-failspots.py
4. Put the demos that you want to examine in the `/demos` folder

Please provide the full paths to the WAD files.

```bash
python3 dsda-failspots.py [-h] [-iwad IWAD] [-file FILE [FILE ...]] -map MAP [-width WIDTH] [-heatmap HEATMAP] [-gif GIF]

options:
  -h, --help            show this help message and exit
  -iwad IWAD            IWAD to load
  -file FILE [FILE ...]
                        The first WAD passed needs to have the map lump
  -map MAP              Map to get the failspots of (ex: E3M1, MAP12)
  -width WIDTH          Width of the resulting image (default: 1920)
  -heatmap HEATMAP      Turn on the heatmap and set the number of samples on each direction
  -gif GIF              Outputs a gif of the progression of the demo attempts. 1: Only show attempts on this interval. 2: Accumulate
                        attempts
```
