# docker-images

These docker images are used to build software for different target systems.

Originally used by `prebuildify-cross`, these images were modified by Contrast Security, Inc. so
they had fewer dependencies.

All images include Node.js LTS, Python 3.x, npm and a build toolchain suitable for
`node-gyp` and `prebuildify`.

# using the images

The primary changes are that the containers now require that the repo
be mapped to `/repo`, `entrypoint` is set to `sh`, and `cmd` is set to `scripts/build-generic.sh`
with an argument of the image name, e.g., `centos7`. You'll typically want to set the user when
you invoke the image; if you don't you'll have to make sure the file/directory permissions will
work.

From `centos7/Dockerfile`:
```
ENTRYPOINT ["sh"]
CMD ["scripts/build-generic.sh", "centos7"]
```

How to invoke the `centos7` image (to build from my local copy of `node-fn-inspect`):
```
# typical usage is to set the user to the user invoking the image so that the
# permissions are effectively inherited.

docker run -v /home/bruce/github/csi/fn-inspect:/repo -u $(id -u) ghcr.io/contrast-security-oss/centos7

# The docker image will invoke `/home/bruce/github/csi/fn-inspect/scripts/build-generic.sh`
# as a shell script with the argument `centos7` (the name of the image). The command that is
# executed is relative to `/repo`, so it will be:
#
# `sh scripts/build-generic.sh centos7`
```

A more minor change is to not create the `node` user in the `centos7` image. It's not
needed and had the potential to create permissions issues.

## build-generic.sh

The `build-generic.sh` script can be invoked from images that do not have `bash`, so your
script must be Posix-compliant in order to work with `ash`, `dash`, etc.

Of course, you can use `--entrypoint` or run a command other than `scripts/build-generic.sh`
if your use case calls for it.

## limitations

Only the images required by Contrast Security, Inc. are built and published at this time.
If you're using the images and need another target, let us know; we'll add it.

## releasing

Create a version tag of the form vX.Y.Z and push it to master.

## License

[GPL-3.0-only](LICENSE) © 2019 `prebuild` contributors. 2024 Contrast Security, Inc.
