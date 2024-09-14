docker run \
       --rm \
       --tty \
       --interactive \
       --mount type=bind,source="$(pwd)/logs",target=/logs \
       --mount type=bind,source="$(pwd)/worlds",target=/usr/local/share/tf-lib/worlds \
       --mount type=bind,source="$(pwd)/scripts",target=/usr/local/share/tf-lib/py \
       bcproxy-tf
