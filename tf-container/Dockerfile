FROM debian:bookworm-slim

RUN apt-get update && apt-get install -y bmake make git gcc curl groff-base libtls-dev python3-dev libpcre3-dev libicu-dev pkg-config libncurses-dev

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


WORKDIR /usr/local/share/tf-lib

COPY entrypoint.sh /entrypoint.sh

ENTRYPOINT /entrypoint.sh
