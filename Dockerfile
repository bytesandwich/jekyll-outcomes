FROM jekyll/jekyll:3
RUN apk --update add tree
RUN apk --update add python
COPY files /files
COPY jekyll-test.py /jekyll-test.py
RUN chmod -R 777 /files
RUN mkdir /jekyll
WORKDIR /jekyll
RUN chmod -R 777 .
CMD /jekyll-test.py
