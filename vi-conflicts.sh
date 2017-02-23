#!/bin/bash

while read file; do
	orig=$(echo "$file" | sed -re 's/\.rej$//')
	if [ -e "$orig" ]; then
		args+="$orig $file"$'\n'
	fi
done <<< "$(find ./ -name "*.rej")"

unmerged=$(git ls-files --unmerged | awk '{print $4}' | uniq)
if [ "$unmerged" ]; then
	args+=$unmerged
fi

args=$(echo "$args" | xargs)
if [ "$args" ]; then
	if [ "$unmerged" ]; then
		vi -p $args '+/^[<=>]\{7}'
	else
		vi -p $args
	fi
fi
