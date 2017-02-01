#!/bin/bash

while read file; do
	orig=$(echo "$file" | sed -re 's/\.rej$//')
	if [ -e "$orig" ]; then
		args+="$orig $file"$'\n'
	fi
done <<< "$(find ./ -name "*.rej")"

args+=$(git ls-files --unmerged | awk '{print $4}' | uniq)

args=$(echo "$args" | xargs)
if [ "$args" ]; then
	vi -p $args
fi
