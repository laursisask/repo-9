FROM public.ecr.aws/docker/library/python:3.10-slim as compile-image

ARG M3_MODULAR_ADMIN_PATH=.

COPY $M3_MODULAR_ADMIN_PATH/requirements.txt /src/requirements.txt
RUN pip install --user -r /src/requirements.txt

COPY $M3_MODULAR_ADMIN_PATH/modular_api /src/modular_api
COPY $M3_MODULAR_ADMIN_PATH/modular_api_cli /src/modular_api_cli
COPY $M3_MODULAR_ADMIN_PATH/modular.py $M3_MODULAR_ADMIN_PATH/entrypoint.sh /src/

# RUN rm -rf $(find /root/.local/lib -name "*.dist-info") && rm -rf $(find /root/.local/lib/ -name "__pycache__")

FROM public.ecr.aws/docker/library/python:3.10-alpine AS build-image
#FROM public.ecr.aws/docker/library/python:3.10-slim AS build-image

ARG MODULES_PATH=./docker_modules/

COPY --from=compile-image /root/.local /root/.local
COPY --from=compile-image /src /src
COPY $MODULES_PATH /tmp/m3-modules

ENV PATH=/root/.local/bin:$PATH
WORKDIR /src

EXPOSE 8085
RUN chmod +x modular.py entrypoint.sh

RUN for pkg in $(ls -d /tmp/m3-modules/*/); do ./modular.py install --module_path $pkg; done; rm -rf /tmp/m3-modules
ENTRYPOINT ["./entrypoint.sh"]