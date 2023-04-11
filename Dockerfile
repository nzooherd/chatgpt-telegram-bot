FROM python:3.10-slim

RUN useradd -m appuser
USER appuser
WORKDIR /home/appuser/

ENV PIPENV_PYPI_MIRROR=https://pypi.tuna.tsinghua.edu.cn/simple
ENV PATH="/home/appuser/.local/bin:$PATH"
RUN pip install --user poetry -i https://pypi.tuna.tsinghua.edu.cn/simple

WORKDIR /home/appuser/app
COPY . .
COPY .env .
RUN poetry install  --no-interaction --no-ansi --no-root
