# TODO

## [v1] To be done
- [ ] Add effects and glitches to images
- [ ] Setup camera (position, lens, distortion) as it will be in real life
- [ ] Use real texture for ground
- [ ] Add random objects in scenes
- [ ] Refactor all functions
- [ ] Create unique displacement texture for every mushroom
- [ ] Add waves of mushroom generation. First wave creates only the biggest mushrooms, second - medium, and third - only tiny mushrooms to fill up the space
- [ ] Test launching without DatasetRoot env var being set
- [ ] Add random saturation variety
- [ ] Add random color channels variety

## [v2] To be done
- [ ] Add more variety to mushroom angles
- [ ] Add pose estimation metadata: stem direction vector (SDV)
- [ ] Add pose estimation metadata: angle between SDV and X and Y axis on 2D plane
- [ ] Add pose estimation metadata: angle between SDV and Z axis (or ground)

## [Training] To be done
- [ ] Create an architecture of the module
- [ ] Find an optimal base model for pose estimation
- [ ] Generate dataset of 1000 samples with pose estimation data
- [ ] Modify dataset visualisation tool so it can display pose estimation (SDV, angles)
- [ ] Generate dataset of 10000 samples with pose estimation data

## [Research] To be done
- [ ] Create an architecture of the route planner

---

## Already done
- [x] Create material only once and use it for all objects (instead of creating material for every object)
- [x] Use real textures for mushrooms
- [x] Save centers and radiuses (all in [x,y]) of every mushroom in the scene
- [x] Detect collision with existing mushrooms when creating new one (and re-generate mushroom with different position and radius, or pass after certain amount of tries)
- [x] Convert Blender coordinates into YOLO coordinates (upper left 0,0 and other boundaries are 1)
<!-- - [x] Label different mushroom size groups (small, medium, large, etc) -->
- [x] Make mushrooms more as irl (size, proportions)
- [x] Rework creating mushroom - from now on it will also add information about size of mushroom into bboxes list
- [x] Add batches of scenes. Add unique generation_params for every batch of scenes
- [x] Add perspective compensation (multiply by function of distance from center of camera and of focal distance)
- [x] Clip mushrooms' coordinates if they are a little out of boundaries
- [x] Do not mark mushrooms with coordinates way out of boundaries
- [x] Randomize light direction
- [x] Add launch.sh file to automate dataset generation with fixed ratios of elements
- [x] Move batch_params.sh and dataset_params.sh to cfg/ directory

# Usage

## Generating in one line

If you want to generate using following rules, run:
```
./launch.sh --size 1000
```

It will create directory `mushroom_dataset` in your user's home directory. If you want to change this behaviour and other low-level parameters, go to `Changing parameters` section down below

## Dataset generation tips

For better dataset augmentation and diversion use these tips:
1. Create 50% of elements as random as possible
2. Create 5% with no mushrooms
3. Create 10% with only one mushroom of random sizes
4. Create 15% with as many mushrooms as possible
5. Create 10% with only small mushrooms
6. Create 10% with only huge mushrooms

You can always configure ratios in `dataset_params.sh`

## Changing batch parameters

If you want to change a default directory or run batch creation manually, follow these steps:

1. Set environment variable `DatasetRoot` where you want a dataset to be located in (will default to your user's home directory):
```
export DatasetRoot='$HOME'
```

2. Create `batch_params.sh` file holding all the variable parameters for a generator:
```
cp batch_params.sh.example batch_params.sh
```

2. Set environment variables for parameters of dataset generation (or you can skip it to use default values) in `batch_params.sh` file:
```
nano batch_params.sh
```

3. Run:
```
source batch_params.sh; blender --background --python main.py
```
