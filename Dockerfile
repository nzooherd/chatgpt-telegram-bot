FROM python:3.10-slim

RUN useradd -m appuser
USER appuser
WORKDIR /home/appuser/

ENV PIPENV_PYPI_MIRROR=https://pypi.tuna.tsinghua.edu.cn/simple
ENV PATH="/home/appuser/.local/bin:$PATH"
RUN pip install --user pipenv -i https://pypi.tuna.tsinghua.edu.cn/simple

WORKDIR /home/appuser/app
COPY . .
COPY .env .
RUN pipenv install --system --deploy  --ignore-pipfile

CMD ["python", "main.py"]