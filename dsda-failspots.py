from omg import *
import sys
import os
import subprocess
from PIL import Image, ImageDraw, ImageFont
import math
from concurrent.futures import ThreadPoolExecutor, as_completed
import argparse
import colorsys

def drawmap(wad, name, width):
    xsize = width - 8

    try:
        edit = UMapEditor(wad.udmfmaps[name])
    except KeyError:
        edit = UMapEditor(wad.maps[name])

    xmin = ymin = float('inf')
    xmax = ymax = float('-inf')
    for v in edit.vertexes:
        xmin = min(xmin, v.x)
        xmax = max(xmax, v.x)
        ymin = min(ymin, -v.y)
        ymax = max(ymax, -v.y)

    scale = xsize / float(xmax - xmin)
    xmax = xmax * scale
    xmin = xmin * scale
    ymax = ymax * scale
    ymin = ymin * scale

    for v in edit.vertexes:
        v.x = v.x * scale
        v.y = -v.y * scale

    im = Image.new('RGBA', (int(xmax - xmin) + 8, int(ymax - ymin) + 8), (0,0,0,255))
    draw = ImageDraw.Draw(im)

    edit.linedefs.sort(key=lambda a: not a.twosided)

    for line in edit.linedefs:
        p1x = edit.vertexes[line.v1].x - xmin + 4
        p1y = edit.vertexes[line.v1].y - ymin + 4
        p2x = edit.vertexes[line.v2].x - xmin + 4
        p2y = edit.vertexes[line.v2].y - ymin + 4

        color = (200, 200, 200)
        if line.twosided:
            color = (120, 120, 120)
        if line.dontdraw:
          continue

        draw.line((p1x, p1y, p2x, p2y), fill=color)
        draw.line((p1x+1, p1y, p2x+1, p2y), fill=color)
        draw.line((p1x-1, p1y, p2x-1, p2y), fill=color)
        draw.line((p1x, p1y+1, p2x, p2y+1), fill=color)
        draw.line((p1x, p1y-1, p2x, p2y-1), fill=color)

    return im, xmax, xmin, ymax, ymin, xsize, scale

def draw_points(points, xmax, xmin, ymax, ymin, xsize, scale):
    overlay = Image.new('RGBA', (int(xmax - xmin) + 8, int(ymax - ymin) + 8), (0,0,0,0))
    draw = ImageDraw.Draw(overlay)

    if (args.heatmap == 0):
      for point in points:
        point[0] = point[0] * scale
        point[1] = -point[1] * scale
        point[0] = point[0] - xmin + 4
        point[1] = point[1] - ymin + 4

        draw.ellipse((point[0]-5, point[1]-5, point[0]+5, point[1]+5), fill=(250,0,0,160))
    else:
      grid = [[0 for _ in range(args.heatmap)] for _ in range(args.heatmap)]
      s = xsize / args.heatmap

      for point in points:
        point[0] = point[0] * scale
        point[1] = -point[1] * scale
        point[0] = point[0] - xmin + 4
        point[1] = point[1] - ymin + 4

        grid[int(point[1]*args.heatmap/xsize)][int(point[0]*args.heatmap/xsize)] += 1

      most_frequent = 0
      for y in range(len(grid)):
        for x in range(len(grid[0])):
          if grid[y][x] > most_frequent:
            most_frequent = grid[y][x]

      for y in range(len(grid)):
        for x in range(len(grid[0])):
          k = 1.2
          if grid[y][x] > 0:
            heat_value = (math.log(grid[y][x] + 1) / math.log(most_frequent + 1))**k
            hue = 0.6 * (1 - heat_value)
            r, g, b = colorsys.hsv_to_rgb(hue, 1, 1)
            draw.rectangle((x*s, y*s, (x+1)*s, (y+1)*s), fill=(int(r*255),int(g*255),int(b*255),200))

    if args.gif:
      font = ImageFont.truetype(os.path.join(pwd, "OpenSans.ttf"), int(xsize/25))
      text = str(image_index+1) + "/10"
      x, y = 10, 10

      bbox = draw.textbbox((x, y), text, font=font)
      text_width = bbox[2] - bbox[0]
      text_height = bbox[3] - bbox[1]

      draw.rectangle([x - 5, y - 5, x + text_width + 5, y + text_height + 50 ], fill="black")

      draw.text((x, y), text, fill="white", font=font)

    return overlay

def process_demo(iwad, files, demo):
    points = []
    try:
      params = [os.path.join(pwd,"dsda-doom"), "-timedemo", demo, "-nodraw", "-nosound"]
      if iwad != "":
        params += ["-iwad", iwad]
      if files != []:
        params += ["-file", *files]

      output = subprocess.run(params, capture_output=True, text=True)

      for line in output.stdout.splitlines():
        if line.startswith("death_pos"):
          points.append([int(line.split()[1]), int(line.split()[2]), os.path.getmtime(demo)])
          break
    except Exception:
      pass

    return points

def get_death_spots(iwad, files, map):
    path = os.path.join(pwd, 'demos')
    demos = [os.path.join(path, d) for d in os.listdir(path) if os.path.isfile(os.path.join(path, d))]
    all_points = []

    with ThreadPoolExecutor(max_workers=16) as executor:
        future_to_demo = {executor.submit(process_demo, iwad, files, demo): demo for demo in demos}

        for i, future in enumerate(as_completed(future_to_demo), 1):
            future_points = future.result()
            all_points.extend(future_points)
            print("Processed " + str(i) + "/" + str(len(demos)) + " demos")

    return all_points


pwd = os.path.dirname(os.path.abspath(__file__))

parser = argparse.ArgumentParser(description="dsda-failspots")
parser.add_argument("-iwad", default="", help="IWAD to load")
parser.add_argument("-file", nargs="+", default=[], help="The first WAD passed needs to have the map lump")
parser.add_argument("-map", required=True, help="Map to get the failspots of (ex: E3M1, MAP12)")
parser.add_argument("-width", type=int, default=1920, help="Width of the resulting image (default: 1920)")
parser.add_argument("-heatmap", type=int, default=0, help="Turn on the heatmap and set the number of samples on each direction")
parser.add_argument("-gif", type=int, default=0, help="Outputs a gif of the progression of the demo attempts.\n1: Only show attempts on this interval.\n2: Accumulate attempts")

args = parser.parse_args()

wadpath = args.file[0] if args.file != [] else args.iwad
if wadpath == "":
  print("Need to suply some WAD with -iwad or -file")
  exit()

wad = WAD()
wad.from_file(wadpath)
wadname = os.path.splitext(os.path.basename(wadpath))[0]
map = (wad.maps.find(args.map) + wad.udmfmaps.find(args.map))[0]

points = get_death_spots(args.iwad, args.file, map)
sorted_points= sorted(points, key=lambda x: x[2])
interval = int(len(sorted_points)/10)

base, xmax, xmin, ymax, ymin, xsize, scale = drawmap(wad, map, args.width)

if args.gif:
  images = []
  image_index = 0
  while image_index < 10:
    overlay = draw_points(points[image_index*interval:(image_index+1)*interval],
                          xmax, xmin, ymax, ymin, xsize, scale)
    if image_index == 0 or args.gif == 1:
      images += [Image.alpha_composite(base, overlay)]
    else:
      images += [Image.alpha_composite(images[image_index-1], overlay)]
    image_index += 1


  images[0].save(
    os.path.join(pwd, "output", wadname + "_" + map + ("_heatmap.gif" if args.heatmap else ".gif")),
    save_all=True,
    append_images=images[1:],
    duration=1000,
    loop=0
  )
else:
  overlay = draw_points(points,xmax, xmin, ymax, ymin, xsize, scale)
  image = Image.alpha_composite(base, overlay)

  image.save(os.path.join(pwd, "output", wadname + "_" + map + ("_heatmap.png" if args.heatmap else ".png")))
