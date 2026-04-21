#!/bin/bash

usage() {
    echo "Usage: $0 --size <integer>"
    echo "Example: $0 --size 10"
    exit 1
}

round() {
    printf "%.0f" "$1"
}

get_ratio() {
    round $(echo "$1*$2" | bc)
}

while [[ $# -gt 0 ]]; do
    case $1 in
        --size)
            if [[ -n $2 ]] && [[ $2 =~ ^[0-9]+$ ]]; then
                size="$2"
                shift 2
            else
                echo "Error: --size requires a positive integer argument"
                usage
            fi
            ;;
        *)
            echo "Error: Unknown option $1"
            usage
            ;;
    esac
done

if [[ -z $size ]]; then
    echo "Error: --size argument is required"
    usage
fi

source cfg/dataset_params.sh

# Random per scene generation
export NUM_SCENES=$(get_ratio $size $RANDOM_RATIO)
export MUSHROOM_COUNT_MIN=1
export MUSHROOM_COUNT_MAX=100
export MUSHROOM_SIZE_MIN=0.2
export MUSHROOM_SIZE_MAX=1.6
blender --background --python main.py

# No mushrooms in every scene generation
export NUM_SCENES=$(get_ratio $size $NO_MUSHROOMS_RATIO)
export MUSHROOM_COUNT_MIN=0
export MUSHROOM_COUNT_MAX=0
export MUSHROOM_SIZE_MIN=0.2
export MUSHROOM_SIZE_MAX=1.6
blender --background --python main.py

# One mushroom per scene generation
export NUM_SCENES=$(get_ratio $size $ONE_MUSHROOM_RATIO)
export MUSHROOM_COUNT_MIN=1
export MUSHROOM_COUNT_MAX=1
export MUSHROOM_SIZE_MIN=0.2
export MUSHROOM_SIZE_MAX=1.6
blender --background --python main.py

# Maximum mushrooms per scene generation
export NUM_SCENES=$(get_ratio $size $MAX_MUSHROOMS_RATIO)
export MUSHROOM_COUNT_MIN=100
export MUSHROOM_COUNT_MAX=100
export MUSHROOM_SIZE_MIN=0.2
export MUSHROOM_SIZE_MAX=1.6
blender --background --python main.py

# Small mushrooms in every scene generation
export NUM_SCENES=$(get_ratio $size $SMALL_MUSHROOMS_RATIO)
export MUSHROOM_COUNT_MIN=30
export MUSHROOM_COUNT_MAX=100
export MUSHROOM_SIZE_MIN=0.2
export MUSHROOM_SIZE_MAX=0.8
blender --background --python main.py

# Huge mushrooms in every scene generation
export NUM_SCENES=$(get_ratio $size $HUGE_MUSHROOMS_RATIO)
export MUSHROOM_COUNT_MIN=30
export MUSHROOM_COUNT_MAX=100
export MUSHROOM_SIZE_MIN=0.8
export MUSHROOM_SIZE_MAX=1.6
blender --background --python main.py
