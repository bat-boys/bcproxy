FROM debian:bookworm-slim

RUN apt-get update && apt-get install -y bmake make git gcc curl groff-base libtls-dev python3-dev libpcre3-dev libicu-dev pkg-config libncurses-dev tmux

# install bcproxy

RUN git clone https://github.com/bat-boys/bcproxy.git
WORKDIR /bcproxy

RUN git checkout origin/tf-container
RUN ./configure
RUN bmake obj
RUN bmake
RUN cp obj/bcproxy /usr/local/bin/

# install tf

WORKDIR /

RUN git clone https://github.com/bat-boys/tinyfugue.git
WORKDIR /tinyfugue

RUN ./configure --enable-python --disable-inet6 --disable-mailcheck --disable-ssl
RUN make
RUN make install

# unix socket location
RUN mkdir /run/bcproxy-tf

WORKDIR /usr/local/share/tf-lib

# overwrite dummy tf.py with a python 3 compatible version
COPY py/tf.py tf.py

# config location, will be mounted from host
RUN mkdir /usr/local/etc/confs

ENV TERM=screen-256color
ENV COLORTERM=truecolor

# -u is to force tmux to use utf-8 even if it doesn't believe it's supported
CMD tmux -u -2 new-session "tmux source-file /usr/local/etc/confs/tmux.conf"
