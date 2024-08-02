FROM python:3.9-alpine

COPY . /exp_engine
WORKDIR /exp_engine
# apline can not build pandas by default
# https://copyprogramming.com/howto/install-pandas-in-a-dockerfile

# Install OpenJDK-11
# TODO switch to JDK8? (which is officially supported by Proactive)
RUN apk --no-cache add openjdk11 --repository=http://dl-cdn.alpinelinux.org/alpine/edge/community

RUN python3 -m pip install --upgrade pip setuptools wheel python-dotenv
RUN pip install --upgrade --pre proactive
RUN pip install -r requirements.txt

COPY . .

WORKDIR /exp_engine
ENV PORT 5556
EXPOSE 5556

ENTRYPOINT [ "python" ]
CMD [ "run.py" ]
