FROM schachr/raspbian-stretch
RUN apt-get update && apt-get install -yy python python-dev python-setuptools ca-certificates build-essential python-pil python-pip
ADD . /code
WORKDIR /code
RUN python setup.py install
RUN pip install -r requirements.txt
