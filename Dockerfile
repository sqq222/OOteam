FROM ubuntu:14.04
RUN sudo apt-get update
RUN sudo apt-get install -y make build-essential libssl-dev zlib1g-dev libbz2-dev \
libreadline-dev libsqlite3-dev wget curl llvm libncurses5-dev libncursesw5-dev \
xz-utils tk-dev git curl
RUN curl -L https://raw.githubusercontent.com/pyenv/pyenv-installer/master/bin/pyenv-installer | bash

RUN echo 'export PYENV_ROOT="$HOME/.pyenv"' >> ~/.bashrc
RUN echo 'export PATH="$PYENV_ROOT/bin:$PATH"' >> ~/.bashrc
RUN echo 'eval "$(pyenv init -)"' >> ~/.bashrc
RUN exec $SHELL
RUN pyenv install 3.4.3
RUN pyenv global 3.4.3
RUN pyenv virtualenv shop
RUN pyenv activate shop
RUN mkdir /src;
WORKDIR /src
ADD /config/requirements.pip /config/
