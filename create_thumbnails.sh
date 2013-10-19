#!/bin/sh

for f in $(find img/samples)
do
	filename=${f##*/}
	if [[ $filename == *.jpg ]]; then
		convert -thumbnail 100 $f "img/resized_samples/$filename"
	fi
done
